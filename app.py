import json, os
from flask import Flask, render_template, request, redirect, url_for
from db import get_db, init_db, guess_category, CATEGORY_ICONS, CATEGORY_LABELS
from ai import ask_gemini

app = Flask(__name__)
init_db()
def init_aid_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            goal_id INTEGER,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_aid_table()
def load_colleges():
    with open(os.path.join(app.root_path, "data", "colleges.json")) as f:
        return json.load(f)

# ---------------------------------------------------------------- helpers --
def load_details():
    with open(os.path.join(app.root_path, "data", "college_details.json")) as f:
        return json.load(f)

def college_summary(conn):
    goals = conn.execute(
        "SELECT * FROM goals WHERE kind = 'college' ORDER BY id DESC"
    ).fetchall()
    aid_rows = conn.execute("SELECT * FROM scholarships WHERE active = 1").fetchall()
    out = []
    for g in goals:
        aid = sum(a["amount"] for a in aid_rows
                  if a["goal_id"] is None or a["goal_id"] == g["id"])
        net = max(g["target"] - aid, 0)
        pct = round(min(g["saved"] / net, 1) * 100) if net > 0 else 100
        out.append({
            "id": g["id"], "name": g["name"], "target": g["target"],
            "aid": round(aid, 2), "net": round(net, 2), "saved": g["saved"],
            "remaining": round(max(net - g["saved"], 0), 2), "pct": pct,
        })
    return out
def compute_dashboard_data():
    conn = get_db()

    txs = conn.execute(
        "SELECT * FROM transactions ORDER BY id DESC"
    ).fetchall()

    balance = sum(t["amount"] for t in txs)
    spent_this_month = sum(-t["amount"] for t in txs if t["type"] == "expense")

    # spending grouped by category (expenses only)
    totals = {}
    for t in txs:
        if t["type"] == "expense":
            totals[t["category"]] = totals.get(t["category"], 0) + (-t["amount"])
    max_total = max(totals.values()) if totals else 1
    categories = []
    for cat, amt in sorted(totals.items(), key=lambda x: -x[1]):
        icon, color = CATEGORY_ICONS.get(cat, ("💳", "blue"))
        categories.append({
            "name": CATEGORY_LABELS.get(cat, cat.title()),
            "icon": icon,
            "color": color,
            "amount": round(amt, 2),
            "pct": round(min(amt / max_total, 1) * 100),
        })

    goals = conn.execute("SELECT * FROM goals ORDER BY id DESC LIMIT 3").fetchall()
    recent = txs[:5]

    conn.close()
    return {
        "balance": round(balance, 2),
        "spent": round(spent_this_month, 2),
        "categories": categories,
        "goals": goals,
        "recent": recent,
    }


# ------------------------------------------------------------------ pages --
@app.route("/")
def dashboard():
    data = compute_dashboard_data()
    return render_template("dashboard.html", active="dashboard", data=data)


@app.route("/transactions", methods=["GET", "POST"])
def transactions():
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        amount = request.form.get("amount", "").strip()
        tx_type = request.form.get("type", "expense")
        category = request.form.get("category") or guess_category(name)

        if name and amount:
            amount_val = abs(float(amount))
            if tx_type == "expense":
                amount_val = -amount_val
            conn.execute(
                "INSERT INTO transactions (name, amount, type, category) VALUES (?, ?, ?, ?)",
                (name, amount_val, tx_type, category),
            )
            conn.commit()
        conn.close()
        return redirect(url_for("transactions"))

    txs = conn.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
    conn.close()

    rows = []
    for t in txs:
        icon, color = CATEGORY_ICONS.get(t["category"], ("💳", "blue"))
        rows.append({
            "name": t["name"],
            "amount": t["amount"],
            "type": t["type"],
            "category_label": CATEGORY_LABELS.get(t["category"], t["category"].title()),
            "icon": icon,
            "color": color,
        })

    return render_template(
        "transactions.html", active="transactions", rows=rows,
        categories=CATEGORY_LABELS,
    )


@app.route("/goals", methods=["GET", "POST"])
def goals():
    conn = get_db()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            name = request.form.get("name", "").strip()
            target = request.form.get("target", "").strip()
            if name and target:
                conn.execute(
                    "INSERT INTO goals (name, target, saved, kind) VALUES (?, ?, 0, 'personal')",
                    (name, float(target)),
                )
                conn.commit()
        elif action == "add_money":
            goal_id = request.form.get("goal_id")
            amount = request.form.get("amount", "0").strip()
            if goal_id and amount:
                conn.execute(
                    "UPDATE goals SET saved = saved + ? WHERE id = ?",
                    (float(amount), goal_id),
                )
                conn.commit()
        conn.close()
        return redirect(url_for("goals"))

    all_goals = conn.execute(
        "SELECT * FROM goals WHERE kind = 'personal' ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("goals.html", active="goals", goals=all_goals)

@app.route("/college", methods=["GET", "POST"])
def college():
    conn = get_db()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            name = request.form.get("name", "").strip()
            target = request.form.get("target", "").strip()
            if name and target:
                conn.execute(
                    "INSERT INTO goals (name, target, saved, kind) VALUES (?, ?, 0, 'college')",
                    (name, float(target)),
                )
                conn.commit()
        elif action == "add_money":
            goal_id = request.form.get("goal_id")
            amount = request.form.get("amount", "0").strip()
            if goal_id and amount:
                conn.execute(
                    "UPDATE goals SET saved = saved + ? WHERE id = ?",
                    (float(amount), goal_id),
                )
                conn.commit()
        elif action == "add_school":
            school = next(
                (c for c in load_colleges() if c["id"] == request.form.get("school_id")),
                None,
            )
            if school:
                out_of_state = request.form.get("residency") == "out"
                yearly = school["coa_out"] if (out_of_state and "coa_out" in school) else school["coa"]
                label = f"{school['name']} · 4 years"
                if "coa_out" in school:
                    label += " (out-of-state)" if out_of_state else " (in-state)"
                exists = conn.execute(
                    "SELECT 1 FROM goals WHERE kind = 'college' AND name = ?", (label,)
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO goals (name, target, saved, kind) VALUES (?, ?, 0, 'college')",
                        (label, yearly * 4),
                    )
                    conn.commit()
        elif action == "delete":
            goal_id = request.form.get("goal_id")
            if goal_id:
                conn.execute("DELETE FROM scholarships WHERE goal_id = ?", (goal_id,))
                conn.execute("DELETE FROM goals WHERE id = ? AND kind = 'college'", (goal_id,))
                conn.commit()
        conn.close()
        return redirect(url_for("college"))

    summary = college_summary(conn)
    conn.close()

    tracked = [g["name"] for g in summary]
    schools = [
        {**c, "added": any(n.startswith(c["name"]) for n in tracked)}
        for c in load_colleges()
    ]

    return render_template(
        "college.html", active="college", goals=summary, colleges=schools
    )
@app.route("/scholarships", methods=["GET", "POST"])
def scholarships():
    conn = get_db()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            name = request.form.get("name", "").strip()
            amount = request.form.get("amount", "").strip()
            goal_id = request.form.get("goal_id") or None
            if name and amount:
                conn.execute(
                    "INSERT INTO scholarships (name, amount, goal_id, active) VALUES (?, ?, ?, 1)",
                    (name, abs(float(amount)), goal_id),
                )
        elif action == "toggle":
            conn.execute(
                "UPDATE scholarships SET active = 1 - active WHERE id = ?",
                (request.form.get("sid"),),
            )
        elif action == "delete":
            conn.execute("DELETE FROM scholarships WHERE id = ?", (request.form.get("sid"),))
        conn.commit()
        conn.close()
        return redirect(url_for("scholarships"))

    rows = conn.execute(
        "SELECT s.*, g.name AS school FROM scholarships s "
        "LEFT JOIN goals g ON g.id = s.goal_id ORDER BY s.id DESC"
    ).fetchall()
    schools = conn.execute(
        "SELECT id, name FROM goals WHERE kind = 'college' ORDER BY id DESC"
    ).fetchall()
    conn.close()

    total_active = sum(r["amount"] for r in rows if r["active"])
    return render_template(
        "scholarships.html", active="scholarships",
        rows=rows, schools=schools, total_active=total_active,
    )
@app.route("/chat", methods=["GET", "POST"])
def chat():
    conn = get_db()

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            conn.execute(
                "INSERT INTO chat_messages (role, content) VALUES ('user', ?)",
                (message,),
            )
            data = compute_dashboard_data()
            context = (
                f"Their current balance is ${data['balance']}. "
                f"They've spent ${data['spent']} this month."
            )
            colleges = college_summary(conn)
            if colleges:
                parts = [
                    f"{c['name']}: saved ${c['saved']:.2f} of ${c['net']:.2f} needed "
                    f"after ${c['aid']:.2f} in aid (${c['remaining']:.2f} left)"
                    for c in colleges
                ]
                context += " College savings goals: " + "; ".join(parts) + "."
            reply = ask_gemini(message, context)
            conn.execute(
                "INSERT INTO chat_messages (role, content) VALUES ('ai', ?)",
                (reply,),
            )
            conn.commit()
        conn.close()
        return redirect(url_for("chat"))

    history = conn.execute(
        "SELECT * FROM chat_messages ORDER BY id ASC"
    ).fetchall()
    conn.close()

    return render_template("chat.html", active="chat", history=history)

@app.route("/explore")
def explore():
    details = load_details()
    schools = [{**c, "has_details": c["id"] in details} for c in load_colleges()]
    return render_template("explore.html", active="explore", schools=schools)


@app.route("/explore/<school_id>")
def explore_detail(school_id):
    d = load_details().get(school_id)
    school = next((c for c in load_colleges() if c["id"] == school_id), None)
    if not d or not school:
        return redirect(url_for("explore"))
    return render_template("college_detail.html", active="explore", school=school, d=d)

if __name__ == "__main__":
    app.run(debug=True)
