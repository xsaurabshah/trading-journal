import streamlit as st
from database.db import get_session
from database.models import Symbol, TimeSlot, Approach, EntryModel, Settings

# ── Helpers ──────────────────────────────────────────────────

def load_setting(key, default=None):
    db = get_session()
    row = db.query(Settings).filter(Settings.key == key).first()
    db.close()
    return float(row.value) if row else default

def save_setting(key, value):
    db = get_session()
    row = db.query(Settings).filter(Settings.key == key).first()
    if row:
        row.value = str(value)
    else:
        db.add(Settings(key=key, value=str(value)))
    db.commit()
    db.close()

def load_symbols():
    db = get_session()
    rows = db.query(Symbol).order_by(Symbol.name).all()
    db.close()
    return rows

def load_time_slots():
    db = get_session()
    rows = db.query(TimeSlot).order_by(TimeSlot.id).all()
    db.close()
    return rows

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

def add_symbol(name):
    db = get_session()
    try:
        db.add(Symbol(name=name.upper().strip()))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_symbol(name):
    db = get_session()
    db.query(Symbol).filter(Symbol.name == name).delete()
    db.commit()
    db.close()

def add_time_slot(name):
    db = get_session()
    try:
        db.add(TimeSlot(name=name.strip()))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_time_slot(name):
    db = get_session()
    db.query(TimeSlot).filter(TimeSlot.name == name).delete()
    db.commit()
    db.close()

def add_approach(name, description):
    db = get_session()
    try:
        db.add(Approach(name=name.strip(), description=description.strip()))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_approach(name):
    db = get_session()
    db.query(Approach).filter(Approach.name == name).delete()
    db.commit()
    db.close()

def add_entry_model(approach_name, name, description):
    db = get_session()
    try:
        db.add(EntryModel(approach_name=approach_name, name=name.strip(), description=description.strip()))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_entry_model(entry_model_id):
    db = get_session()
    db.query(EntryModel).filter(EntryModel.id == entry_model_id).delete()
    db.commit()
    db.close()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Setup", layout="wide")
st.title("⚙️ Setup")

st.subheader("Risk Settings")
current_base_size = load_setting("base_size", default=0.01)
new_base_size = st.number_input("Base Size", value=current_base_size, min_value=0.01, format="%.2f", step=0.01)
if st.button("Save Base Size"):
    save_setting("base_size", new_base_size)
    st.success(f"Base size updated to {new_base_size}")

st.divider()

# ── Symbols ──────────────────────────────────────────────────
st.subheader("Symbols")
for s in load_symbols():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.text(s.name)
    with col2:
        if st.button("Remove", key=f"del_sym_{s.name}"):
            st.session_state[f"confirm_sym_{s.name}"] = True
        if st.session_state.get(f"confirm_sym_{s.name}"):
            st.warning(f"Remove **{s.name}**?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes", key=f"yes_sym_{s.name}"):
                    delete_symbol(s.name)
                    st.session_state.pop(f"confirm_sym_{s.name}")
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_sym_{s.name}"):
                    st.session_state.pop(f"confirm_sym_{s.name}")
                    st.rerun()

with st.form("add_symbol_form", clear_on_submit=True):
    new_symbol = st.text_input("Add Symbol", placeholder="e.g. EURUSD")
    if st.form_submit_button("Add"):
        if new_symbol.strip():
            if add_symbol(new_symbol):
                st.success(f"{new_symbol.upper()} added.")
                st.rerun()
            else:
                st.error("Symbol already exists.")

st.divider()

# ── Time Slots ───────────────────────────────────────────────
st.subheader("Time Slots")
for t in load_time_slots():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.text(t.name)
    with col2:
        if st.button("Remove", key=f"del_slot_{t.name}"):
            st.session_state[f"confirm_slot_{t.name}"] = True
        if st.session_state.get(f"confirm_slot_{t.name}"):
            st.warning(f"Remove **{t.name}**?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes", key=f"yes_slot_{t.name}"):
                    delete_time_slot(t.name)
                    st.session_state.pop(f"confirm_slot_{t.name}")
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_slot_{t.name}"):
                    st.session_state.pop(f"confirm_slot_{t.name}")
                    st.rerun()

with st.form("add_slot_form", clear_on_submit=True):
    new_slot = st.text_input("Add Time Slot", placeholder="e.g. 12PM-3PM ET")
    if st.form_submit_button("Add"):
        if new_slot.strip():
            if add_time_slot(new_slot):
                st.success(f"{new_slot} added.")
                st.rerun()
            else:
                st.error("Time slot already exists.")

st.divider()

# ── Approaches + Entry Models ────────────────────────────────
st.subheader("Approaches")
for a in load_approaches():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{a.name}**")
        if a.description:
            st.caption(a.description)
    with col2:
        if st.button("Remove", key=f"del_app_{a.name}"):
            st.session_state[f"confirm_app_{a.name}"] = True
        if st.session_state.get(f"confirm_app_{a.name}"):
            st.warning(f"Remove **{a.name}**?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes", key=f"yes_app_{a.name}"):
                    delete_approach(a.name)
                    st.session_state.pop(f"confirm_app_{a.name}")
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_app_{a.name}"):
                    st.session_state.pop(f"confirm_app_{a.name}")
                    st.rerun()

    # Entry models under each approach
    st.markdown(f"*Entry Models for {a.name}:*")
    entry_models = load_entry_models(a.name)
    if not entry_models:
        st.caption("No entry models yet.")
    for em in entry_models:
        ec1, ec2 = st.columns([4, 1])
        with ec1:
            st.text(em.name)
            if em.description:
                st.caption(em.description)
        with ec2:
            if st.button("Remove", key=f"del_em_{em.id}"):
                st.session_state[f"confirm_em_{em.id}"] = True
            if st.session_state.get(f"confirm_em_{em.id}"):
                st.warning(f"Remove **{em.name}**?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes", key=f"yes_em_{em.id}"):
                        delete_entry_model(em.id)
                        st.session_state.pop(f"confirm_em_{em.id}")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel_em_{em.id}"):
                        st.session_state.pop(f"confirm_em_{em.id}")
                        st.rerun()

    with st.form(f"add_em_form_{a.name}", clear_on_submit=True):
        em_name = st.text_input("Entry Model Name", placeholder="e.g. Break and Retest", key=f"em_name_{a.name}")
        em_desc = st.text_area("Description", placeholder="Describe this entry model...", key=f"em_desc_{a.name}")
        if st.form_submit_button("Add Entry Model"):
            if em_name.strip():
                if add_entry_model(a.name, em_name, em_desc):
                    st.success(f"{em_name} added.")
                    st.rerun()
                else:
                    st.error("Entry model already exists.")

    st.divider()

with st.form("add_approach_form", clear_on_submit=True):
    new_name = st.text_input("Approach Name", placeholder="e.g. OIAL")
    new_desc = st.text_area("Description", placeholder="Describe this approach...")
    if st.form_submit_button("Add Approach"):
        if new_name.strip():
            if add_approach(new_name, new_desc):
                st.success(f"{new_name} added.")
                st.rerun()
            else:
                st.error("Approach already exists.")