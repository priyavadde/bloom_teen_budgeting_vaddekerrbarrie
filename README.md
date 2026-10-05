# Bloom — Teen Budgeting App

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a free Gemini API key from https://aistudio.google.com/app/apikey

3. Set it as an environment variable before running the app:

   **Mac/Linux (terminal):**
   ```
   export GEMINI_API_KEY="your-key-here"
   ```

   **Windows (PowerShell):**
   ```
   $env:GEMINI_API_KEY="your-key-here"
   ```

   **Or in PyCharm:** Run → Edit Configurations → find your app.py config →
   Environment variables → add `GEMINI_API_KEY=your-key-here`

   Without this key, the "Ask Bloom AI" chat will still work but will show
   a friendly message instead of a real answer.

4. Run the app:
   ```
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.

## What's real right now

- Transactions: add real income/expenses, auto-categorized by keyword, stored in SQLite (bloom.db)
- Goals: create goals, add money toward them, progress rings update live
- College costs: same as goals, filtered separately
- Dashboard: pulls real totals from your data
- Ask Bloom AI: sends your question + your budget context to Gemini and shows the real answer

## What's still a placeholder

- Bank connection / investment tracking (needs Plaid — a future step)
- Location-based cost of living estimates for college
- Notifications (currently just a static example)

## Files

- `app.py` — routes and logic
- `db.py` — database setup and helpers
- `ai.py` — Gemini integration
- `templates/` — HTML pages
- `static/css/style.css` — all styling (colors are CSS variables at the top — easy to tweak)
