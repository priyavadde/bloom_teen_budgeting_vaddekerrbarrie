import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "bloom.db"

CATEGORY_ICONS = {
    "eating_out": ("🍔", "pink"),
    "shopping": ("🛍️", "purple"),
    "transportation": ("⛽", "blue"),
    "college": ("🎓", "mint"),
    "income": ("💵", "mint"),
    "other": ("💳", "blue"),
}

CATEGORY_LABELS = {
    "eating_out": "Eating out",
    "shopping": "Shopping",
    "transportation": "Gas & transportation",
    "college": "College fund",
    "income": "Income",
    "other": "Other",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,           -- 'income' or 'expense'
            category TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            saved REAL NOT NULL DEFAULT 0,
            kind TEXT NOT NULL DEFAULT 'personal'   -- 'personal' or 'college'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,           -- 'user' or 'ai'
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed with starter data only if empty, so the app looks alive on first run
    count = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
    if count == 0:
        seed = [
            ("Domino's Pizza", -14.20, "expense", "eating_out"),
            ("Babysitting — Johnsons", 45.00, "income", "income"),
            ("Shell Gas Station", -18.75, "expense", "transportation"),
            ("Nike Store", -52.00, "expense", "shopping"),
        ]
        conn.executemany(
            "INSERT INTO transactions (name, amount, type, category) VALUES (?, ?, ?, ?)",
            seed,
        )

    count = conn.execute("SELECT COUNT(*) AS c FROM goals").fetchone()["c"]
    if count == 0:
        seed_goals = [
            ("Spring Break Trip", 500, 325, "personal"),
            ("First Car Fund", 3000, 900, "personal"),
            ("College App Fees", 250, 220, "college"),
        ]
        conn.executemany(
            "INSERT INTO goals (name, target, saved, kind) VALUES (?, ?, ?, ?)",
            seed_goals,
        )

    conn.commit()
    conn.close()


def guess_category(name: str) -> str:
    """Very simple keyword-based auto-categorizer. Swap for AI later if you want."""
    name_lower = name.lower()
    keywords = {
        "eating_out": ["pizza", "restaurant", "starbucks", "chipotle", "mcdonald",
                       "cafe", "coffee", "food", "dining", "doordash", "uber eats"],
        "transportation": ["gas", "shell", "chevron", "uber", "lyft", "bus", "train", "parking"],
        "shopping": ["nike", "amazon", "target", "mall", "store", "shein", "clothes", "shoes"],
        "college": ["tuition", "application fee", "college", "sat", "act", "fafsa"],
    }
    for category, words in keywords.items():
        if any(w in name_lower for w in words):
            return category
    return "other"
