import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from database.db import get_session
from database.models import Trade, Symbol, TimeSlot, Approach, EntryModel, Reflection, Settings

# ── DB helpers ───────────────────────────────────────────────
def load_symbols():
    db = get_session()
    rows = db.query(Symbol).order_by(Symbol.name).all()
    db.close()
    return [r.name for r in rows]

def load_time_slots():
    db = get_session()
    rows = db.query(TimeSlot).order_by(TimeSlot.id).all()
    db.close()
    return [r.name for r in rows]

def load_approaches():
    db = get_session()
    rows = db.query(Approach).order_by(Approach.name).all()
    db.close()
    return rows

def load_entry_models(approach_name):
    db = get_session()
    rows = db.query(EntryModel).filter(EntryModel.approach_name == approach_name).all()
    db.close()
    return rows

def load_trades():
    db = get_session()
    rows = db.query(Trade).order_by(Trade.date.desc()).all()
    db.close()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([{
        "id":          r.id,
        "date":        r.date,
        "symbol":      r.symbol,
        "time_slot":   r.time_slot,
        "approach":    r.approach,
        "entry_model": r.entry_model,
        "r_gain":      r.r_gain,
        "size":        r.size,
        "time_to_tp":  r.time_to_tp,
        "time_to_sl":  r.time_to_sl,
    } for r in rows])

def add_trade(date, symbol, time_slot, approach, entry_model, r_gain, size, time_to_tp, time_to_sl):
    db = get_session()
    trade = Trade(
        date=str(date), symbol=symbol, time_slot=time_slot,
        approach=approach, entry_model=entry_model, r_gain=r_gain,
        size=size, time_to_tp=time_to_tp, time_to_sl=time_to_sl
    )
    db.add(trade)
    db.commit()
    db.close()

def delete_trade(trade_id):
    db = get_session()
    db.query(Trade).filter(Trade.id == trade_id).delete()
    db.commit()
    db.close()

def load_reflection(week_start):
    db = get_session()
    row = db.query(Reflection).filter(Reflection.week_start == str(week_start)).first()
    db.close()
    return row.reflection if row else None

def save_reflection(week_start, reflection):
    db = get_session()
    row = db.query(Reflection).filter(Reflection.week_start == str(week_start)).first()
    if row:
        row.reflection = reflection
    else:
        db.add(Reflection(week_start=str(week_start), reflection=reflection))
    db.commit()
    db.close()

# ── Week helpers ─────────────────────────────────────────────
def get_week_bounds(d=None):
    d = d or date.today()
    monday = d - timedelta(days=d.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday

def get_week_days(monday):
    return [monday + timedelta(days=i) for i in range(5)]

# ── Volatility score ─────────────────────────────────────────
def calc_volatility(week_df, base_size):
    if week_df.empty:
        return 0, 0
    score = 0
    for day, day_df in week_df.groupby("date"):
        trade_count     = len(day_df)
        approaches_used = day_df["approach"].nunique()
        slots_used      = day_df["time_slot"].nunique()
        oversized       = (day_df["size"] > base_size).sum()
        score += max(0, trade_count - 1) * 3
        score += max(0, approaches_used - 1) * 3
        score += max(0, slots_used - 1) * 2
        score += oversized * 1
    max_possible = 5 * (3 + 3 + 2 + 1)
    return score, max_possible

def load_setting(key, default=None):
    db = get_session()
    row = db.query(Settings).filter(Settings.key == key).first()
    db.close()
    return float(row.value) if row else default


# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Trading Journal", layout="wide")
st.title("📈 Trading Journal")

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Log a Trade")
    trade_date = st.date_input("Date", value=date.today())
    symbol     = st.selectbox("Symbol", load_symbols())
    time_slot  = st.selectbox("Time Slot", load_time_slots())
    approaches = load_approaches()
    approach   = st.selectbox("Approach", [a.name for a in approaches])
    entry_models = load_entry_models(approach)
    entry_model  = st.selectbox("Entry Model", [e.name for e in entry_models]) if entry_models else None
    r_gain     = st.number_input("R Gain", format="%.2f")

    if r_gain > 0:
        time_to_tp = st.number_input("Time to TP (mins)", min_value=0, step=1)
        time_to_sl = None
    elif r_gain < 0:
        time_to_sl = st.number_input("Time to SL (mins)", min_value=0, step=1)
        time_to_tp = None
    else:
        time_to_tp = None
        time_to_sl = None

    base_size = load_setting("base_size", default=0.01)
    size = st.number_input("Size", min_value=base_size, format="%.2f")

    if st.button("Add Trade", use_container_width=True):
        add_trade(trade_date, symbol, time_slot, approach, entry_model, r_gain, size, time_to_tp, time_to_sl)
        st.success("Trade logged!")
        st.rerun()

# ── Load data ────────────────────────────────────────────────
df = load_trades()
monday, friday = get_week_bounds()
week_days = get_week_days(monday)
week_df   = df[(df["date"] >= str(monday)) & (df["date"] <= str(friday))] if not df.empty else pd.DataFrame()

# ── Principle Dashboard ──────────────────────────────────────
st.subheader("Reduce Volatility · End in Blue")
left, right = st.columns(2)

with left:
    st.markdown("**Volatility Score**")
    base_size = load_setting("base_size", default=0.01)
    score, max_possible = calc_volatility(week_df, base_size)
    ratio     = score / max_possible if max_possible > 0 else 0
    threshold = 0.4
    bar_color  = "#22c55e" if ratio <= threshold else "#ef4444"
    fill_width = min(int(ratio * 100), 100) if ratio > 0 else 0

    st.markdown(f"""
        <div style="background:#1f2937;border-radius:8px;height:28px;width:100%;overflow:hidden;margin-bottom:6px;">
            <div style="background:{bar_color};width:{fill_width}%;height:100%;border-radius:8px;"></div>
        </div>
        <div style="color:#aaa;font-size:13px;">Score: {score} / {max_possible} &nbsp;|&nbsp; Week of {monday.strftime('%b %d')}</div>
    """, unsafe_allow_html=True)

    last_monday = monday - timedelta(weeks=1)
    existing_reflection = load_reflection(last_monday)
    if date.today().weekday() == 0 and not existing_reflection:
        st.markdown("---")
        st.markdown("**Before the week resets — reflect on last week:**")
        reflection_text = st.text_area("What's your volatility assessment for this week?", key="reflection_input")
        if st.button("Submit & Reset", use_container_width=True):
            if reflection_text.strip():
                save_reflection(last_monday, reflection_text)
                st.success("Reflection saved.")
                st.rerun()
            else:
                st.error("Please write your assessment before resetting.")

with right:
    st.markdown("**End in Blue**")
    day_pnl = {}
    if not df.empty:
        for d in week_days:
            day_trades = df[df["date"] == str(d)]
            if not day_trades.empty:
                day_pnl[d] = day_trades["r_gain"].sum()

    blocks_html = "<div style='display:flex;gap:8px;margin-top:8px;'>"
    for d in week_days:
        label = d.strftime("%a")
        if d not in day_pnl:
            color, txt_col = "#374151", "#6b7280"
        elif day_pnl[d] > 0:
            color, txt_col = "#1d4ed8", "#ffffff"
        else:
            color, txt_col = "#dc2626", "#ffffff"
        r_text = f"{day_pnl[d]:+.2f}R" if d in day_pnl else ""
        blocks_html += f"""
            <div style="background:{color};border-radius:8px;width:72px;height:72px;
                display:flex;flex-direction:column;align-items:center;justify-content:center;
                font-size:13px;font-weight:600;color:{txt_col};">
                <div>{label}</div>
                <div style="font-size:11px;margin-top:4px;">{r_text}</div>
            </div>"""
    blocks_html += "</div>"
    st.components.v1.html(blocks_html, height=100)

st.divider()

# ── Stats filters ────────────────────────────────────────────
if df.empty:
    st.info("No trades yet. Log your first trade in the sidebar.")
    st.stop()

st.subheader("Stats")
f1, f2, f3 = st.columns(3)
with f1:
    filter_approach = st.selectbox("Approach", ["All"] + [a.name for a in load_approaches()])
with f2:
    filter_slot = st.selectbox("Time Slot", ["All"] + load_time_slots())
with f3:
    filter_em_options = ["All"]
    if filter_approach != "All":
        filter_em_options += [e.name for e in load_entry_models(filter_approach)]
    filter_em = st.selectbox("Entry Model", filter_em_options)

stats_df = df.copy()
if filter_approach != "All":
    stats_df = stats_df[stats_df["approach"] == filter_approach]
if filter_slot != "All":
    stats_df = stats_df[stats_df["time_slot"] == filter_slot]
if filter_em != "All":
    stats_df = stats_df[stats_df["entry_model"] == filter_em]

if stats_df.empty:
    st.info("No trades match the selected filters.")
else:
    total_r    = stats_df["r_gain"].sum()
    win_rate   = (stats_df["r_gain"] > 0).mean() * 100
    avg_win    = stats_df[stats_df["r_gain"] > 0]["r_gain"].mean() if (stats_df["r_gain"] > 0).any() else 0
    avg_loss   = stats_df[stats_df["r_gain"] < 0]["r_gain"].mean() if (stats_df["r_gain"] < 0).any() else 0
    loss_rate  = 1 - (win_rate / 100)
    expectancy = (win_rate / 100 * avg_win) + (loss_rate * avg_loss)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total R",    f"{total_r:,.2f}R")
    c2.metric("Win Rate",   f"{win_rate:.1f}%")
    c3.metric("Avg Win",    f"{avg_win:.2f}R")
    c4.metric("Avg Loss",   f"{avg_loss:.2f}R")
    c5.metric("Expectancy", f"{expectancy:.2f}R")

st.divider()

# ── R Curve ──────────────────────────────────────────────────
st.subheader("R Curve")
df_sorted = df.sort_values("date")
df_sorted["cumulative_r"] = df_sorted["r_gain"].cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_sorted["date"], y=df_sorted["cumulative_r"],
    mode="lines+markers", fill="tozeroy",
    line=dict(color="#00c896", width=2),
    fillcolor="rgba(0,200,150,0.1)"
))
fig.update_layout(
    xaxis_title="Date", yaxis_title="Cumulative R",
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    height=300, margin=dict(l=0, r=0, t=10, b=0)
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── TP/SL Cluster ────────────────────────────────────────────
st.subheader("Time to TP / SL Cluster")
wins   = stats_df[stats_df["r_gain"] > 0].dropna(subset=["time_to_tp"])
losses = stats_df[stats_df["r_gain"] < 0].dropna(subset=["time_to_sl"])

if wins.empty and losses.empty:
    st.info("No TP/SL time data yet.")
else:
    fig2 = go.Figure()
    if not wins.empty:
        fig2.add_trace(go.Scatter(
            x=wins["time_to_tp"], y=wins["r_gain"],
            mode="markers", name="Wins",
            marker=dict(color="#1d4ed8", size=10, opacity=0.8)
        ))
    if not losses.empty:
        fig2.add_trace(go.Scatter(
            x=losses["time_to_sl"], y=losses["r_gain"],
            mode="markers", name="Losses",
            marker=dict(color="#dc2626", size=10, opacity=0.8)
        ))
    fig2.update_layout(
        xaxis_title="Minutes to TP / SL", yaxis_title="R Gain",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Trade Log ────────────────────────────────────────────────
st.subheader("Trade Log")
col1, col2 = st.columns([2, 1])
with col1:
    symbol_filter = st.selectbox("Filter by Symbol", ["All"] + load_symbols())
with col2:
    slot_filter = st.selectbox("Filter by Time Slot", ["All"] + load_time_slots())

filtered = df.copy()
if symbol_filter != "All":
    filtered = filtered[filtered["symbol"] == symbol_filter]
if slot_filter != "All":
    filtered = filtered[filtered["time_slot"] == slot_filter]

for _, row in filtered.iterrows():
    icon = "🔵" if row["r_gain"] >= 0 else "🔴"
    with st.expander(f"{icon} {row['date']} — {row['symbol']} | {row['time_slot']} | R Gain: {row['r_gain']:+.2f}R"):
        st.write(f"**Approach:** {row['approach']}")
        st.write(f"**Entry Model:** {row['entry_model'] or '—'}")
        st.write(f"**Size:** {row['size']}")
        st.write(f"**Time Slot:** {row['time_slot']}")
        st.write(f"**R Gain:** {row['r_gain']:+.2f}R")
        if pd.notna(row["time_to_tp"]) and row["time_to_tp"] > 0:
            st.write(f"**Time to TP:** {int(row['time_to_tp'])} mins")
        if pd.notna(row["time_to_sl"]) and row["time_to_sl"] > 0:
            st.write(f"**Time to SL:** {int(row['time_to_sl'])} mins")
        if st.button("Delete", key=f"del_{row['id']}"):
            delete_trade(row["id"])
            st.rerun()

#test