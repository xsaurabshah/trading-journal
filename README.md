# Trading Journal

A local trading journal and analytics dashboard built with Streamlit, SQLAlchemy, and SQLite.

## Setup

1. Create and activate virtual environment
```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    source venv/bin/activate  # Mac/Linux
```
2. Install dependencies
```bash
    pip install -r requirements.txt
```
3. Run migrations
```bash
    alembic upgrade head
```
4. Launch
```bash
    streamlit run app.py
```

## Features
- Trade logging with approach and entry model tracking
- Volatility score — tracks behavioral consistency week over week
- End in Blue — weekly day grid tracking positive R days
- Stats filtered by approach, time slot, and entry model
- Session log with pre-session gameplan, check-in, and post-session review
- Setup page for managing symbols, time slots, approaches, and entry models