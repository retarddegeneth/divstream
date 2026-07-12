#!/usr/bin/env python3
import sqlite3, os, json, math
from datetime import datetime
from flask import Flask, g, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = "div-router-leaderboard"
DB_PATH = os.path.join(app.root_path, "div.db")

# Robinhood Chain settings
CHAIN_ID = 4663
NETWORK_NAME = "robinhood_chain"

TOKEN_MAP = {
    "AAPL": "0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9",
    "AMD": "0x86923f96303D656E4aa86D9d42D1e57ad2023fdC",
    "AMZN": "0x12f190a9F9d7D37a250758b26824B97CE941bF54",
    "BABA": "0xad25Ac6C84D497db898fa1E8387bf6Af3532a1c4",
    "BE": "0x822CC93fFD030293E9842c30BBD678F530701867",
    "COIN": "0x6330D8C3178a418788dF01a47479c0ce7CCF450b",
    "CRCL": "0xdF0992E440dD0be65BD8439b609d6D4366bf1CB5",
    "CRWV": "0x5f10A1C971B69e47e059e1dC91901B59b3fB49C3",
    "GOOGL": "0x2e0847E8910a9732eB3fb1bb4b70a580ADAD4FE3",
    "INTC": "0xc72b96e0E48ecd4DC75E1e45396e26300BC39681",
    "META": "0xc0D6457C16Cc70d6790Dd43521C899C87ce02f35",
    "MSFT": "0xe93237C50D904957Cf27E7B1133b510C669c2e74",
    "MU": "0xfF080c8ce2E5feadaCa0Da81314Ae59D232d4afD",
    "NVDA": "0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC",
    "ORCL": "0xb0992820E760d836549ba69BC7598b4af75dEE03",
    "PLTR": "0x894E1EC2D74FFE5AEF8Dc8A9e84686acCB964F2A",
    "SNDK": "0xB90A19fF0Af67f7779afF50A882A9CfF42446400",
    "SPCX": "0x4a0E65A3EcceC6dBe60AE065F2e7bb85Fae35eEa",
    "TSLA": "0x322F0929c4625eD5bAd873c95208D54E1c003b2d",
    "USAR": "0xd917B029C761D264c6A312BBbcDA868658eF86a6",
    "QQQ": "0xD5f3879160bc7c32ebb4dC785F8a4F505888de6",
}

DIVIDEND_MAP = {
    "AAPL": {"annual_per_share": 0.96, "frequency": "quarterly"},
    "KO": {"annual_per_share": 1.84, "frequency": "quarterly"},
    "PEP": {"annual_per_share": 2.38, "frequency": "quarterly"},
    "NVDA": {"annual_per_share": 0.04, "frequency": "quarterly"},
    "MSFT": {"annual_per_share": 3.00, "frequency": "quarterly"},
}

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS vaults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            token_address TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'cash',
            shares REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS dividend_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            ex_date DATE,
            pay_date DATE,
            amount_per_share REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            tx_hash TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_id INTEGER NOT NULL REFERENCES vaults(id),
            event_id INTEGER NOT NULL REFERENCES dividend_events(id),
            amount_usd REAL NOT NULL,
            mode TEXT NOT NULL,
            tx_hash TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()

@app.before_request
def before():
    init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()
    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        token_address = request.form.get("token_address", "").strip()
        mode = request.form.get("mode", "cash").strip().lower()
        shares_raw = request.form.get("shares", "0").strip()
        try:
            shares = float(shares_raw)
        except ValueError:
            shares = 0
        if not symbol or not token_address or shares <= 0:
            return jsonify({"ok": False, "error": "symbol, token_address, and shares > 0 required"}), 400
        db.execute(
            "INSERT INTO vaults (symbol, token_address, mode, shares) VALUES (?, ?, ?, ?)",
            (symbol, token_address, mode, shares),
        )
        db.commit()
        return jsonify({"ok": True})

    vaults = db.execute("SELECT * FROM vaults ORDER BY created_at DESC").fetchall()
    events = db.execute("SELECT * FROM dividend_events ORDER BY ex_date DESC LIMIT 50").fetchall()
    payouts = db.execute("SELECT p.*, v.symbol FROM payouts p JOIN vaults v ON v.id=p.vault_id ORDER BY created_at DESC LIMIT 50").fetchall()
    return render_template("index.html", vaults=vaults, events=events, payouts=payouts, chain_id=CHAIN_ID, network=NETWORK_NAME, token_map=TOKEN_MAP)

@app.route("/events", methods=["POST"])
def add_event():
    db = get_db()
    data = request.get_json(force=True) or {}
    symbol = data.get("symbol", "").strip().upper()
    ex_date = data.get("ex_date", "").strip()
    pay_date = data.get("pay_date", "").strip()
    amount = data.get("amount_per_share")
    if not symbol or not ex_date or not pay_date or amount is None:
        return jsonify({"ok": False, "error": "missing fields"}), 400
    db.execute(
        "INSERT INTO dividend_events (symbol, ex_date, pay_date, amount_per_share) VALUES (?, ?, ?, ?)",
        (symbol, ex_date, pay_date, float(amount)),
    )
    db.commit()
    return jsonify({"ok": True})

@app.route("/payouts", methods=["POST"])
def payout():
    db = get_db()
    data = request.get_json(force=True) or {}
    vault_id = data.get("vault_id")
    event_id = data.get("event_id")
    amount = data.get("amount_usd")
    mode = data.get("mode", "cash")
    tx_hash = data.get("tx_hash", "").strip()
    if not vault_id or not event_id or amount is None:
        return jsonify({"ok": False, "error": "missing fields"}), 400
    db.execute(
        "INSERT INTO payouts (vault_id, event_id, amount_usd, mode, tx_hash) VALUES (?, ?, ?, ?, ?)",
        (int(vault_id), int(event_id), float(amount), mode, tx_hash),
    )
    db.execute("UPDATE dividend_events SET status='paid' WHERE id=?", (int(event_id),))
    db.commit()
    return jsonify({"ok": True})

@app.route("/vaults")
def vaults_api():
    db = get_db()
    rows = db.execute("SELECT * FROM vaults ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/events")
def events_api():
    db = get_db()
    rows = db.execute("SELECT * FROM dividend_events ORDER BY ex_date DESC LIMIT 100").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/payouts")
def payouts_api():
    db = get_db()
    rows = db.execute("SELECT p.*, v.symbol FROM payouts p JOIN vaults v ON v.id=p.vault_id ORDER BY created_at DESC LIMIT 100").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/tokens")
def tokens_api():
    out = []
    for sym, addr in TOKEN_MAP.items():
        out.append({"symbol": sym, "address": addr})
    return jsonify(out)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
