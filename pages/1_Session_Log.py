from datetime import date
import streamlit as st
from database.db import get_session
from database.models import SessionLog, TimeSlot

def load_time_slots():
    db = get_session()
    rows = db.query(TimeSlot).order_by(TimeSlot.id).all()
    db.close()
    return [r.name for r in rows]

def load_session(date, time_slot):
    db = get_session()
    row = db.query(SessionLog).filter(
        SessionLog.date == str(date),
        SessionLog.time_slot == time_slot
    ).first()
    db.close()
    return (row.pregame or "", row.checkin or "", row.post_review or "") if row else ("", "", "")

def save_session(date, time_slot, pregame, checkin, post_review):
    db = get_session()
    row = db.query(SessionLog).filter(
        SessionLog.date == str(date),
        SessionLog.time_slot == time_slot
    ).first()
    if row:
        row.pregame     = pregame
        row.checkin     = checkin
        row.post_review = post_review
    else:
        db.add(SessionLog(
            date=str(date), time_slot=time_slot,
            pregame=pregame, checkin=checkin, post_review=post_review
        ))
    db.commit()
    db.close()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Session Log", layout="wide")
st.title("📝 Session Log")

# ── Session selector ─────────────────────────────────────────
col1, col2 = st.columns([1, 1])
with col1:
    session_date = st.date_input("Date", value=date.today())
with col2:
    time_slot = st.selectbox("Time Slot", load_time_slots())

# ── Load existing session ────────────────────────────────────
pregame, checkin, post_review = load_session(session_date, time_slot)

st.divider()

# ── Text fields ──────────────────────────────────────────────
pregame_input  = st.text_area("📋 Pre-Session Gameplan",  value=pregame,      height=180, placeholder="What's your plan for this session?")
checkin_input  = st.text_area("🔄 Session Check-in",      value=checkin,      height=180, placeholder="How is the session going? Any adjustments?")
review_input   = st.text_area("📊 Post-Session Review",   value=post_review,  height=180, placeholder="How did the session go? What did you learn?")

if st.button("Save Session Log", use_container_width=True):
    save_session(session_date, time_slot, pregame_input, checkin_input, review_input)
    st.success(f"Session log saved for {session_date} — {time_slot}")