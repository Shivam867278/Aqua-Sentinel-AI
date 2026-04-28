from __future__ import annotations

import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from config import settings


DB_PATH = Path(settings.database_url.replace("sqlite:///", ""))


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> Optional[Dict[str, Any]]:
    return dict(row) if row else None


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def init_db() -> None:
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL,
                country TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'operator', 'citizen')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER NOT NULL,
                zone TEXT NOT NULL,
                flow_rate REAL NOT NULL,
                pressure REAL NOT NULL,
                demand REAL NOT NULL,
                turbidity REAL NOT NULL,
                energy REAL NOT NULL,
                loss REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER NOT NULL,
                severity TEXT NOT NULL,
                zone TEXT NOT NULL,
                event TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                prediction_type TEXT NOT NULL,
                input_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS control_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                strategy TEXT NOT NULL,
                zone TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                zone TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                response TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(city_id) REFERENCES cities(id)
            );

            CREATE TABLE IF NOT EXISTS system_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                zone TEXT NOT NULL,
                control_type TEXT NOT NULL,
                target_value REAL NOT NULL,
                unit TEXT NOT NULL,
                reason TEXT NOT NULL,
                safety_note TEXT NOT NULL,
                status TEXT NOT NULL,
                reviewer_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(city_id) REFERENCES cities(id),
                FOREIGN KEY(reviewer_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS household_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                connection_id TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS water_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                billing_month TEXT NOT NULL,
                consumption_kl REAL NOT NULL,
                amount_due REAL NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        seed_demo_data(db)


def seed_demo_data(db: sqlite3.Connection) -> None:
    city = db.execute("SELECT id FROM cities WHERE name = ?", ("Smart Water City",)).fetchone()
    if city is None:
        db.execute(
            "INSERT INTO cities (name, state, country, created_at) VALUES (?, ?, ?, ?)",
            ("Smart Water City", "Maharashtra", "India", utc_now()),
        )
    city_id = db.execute("SELECT id FROM cities WHERE name = ?", ("Smart Water City",)).fetchone()["id"]

    demo_users = [
        ("City Admin", "admin@aqua.local", "admin123", "admin"),
        ("Water Operator", "operator@aqua.local", "operator123", "operator"),
        ("Citizen User", "citizen@aqua.local", "citizen123", "citizen"),
    ]
    for full_name, email, password, role in demo_users:
        exists = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists is None:
            db.execute(
                """
                INSERT INTO users (city_id, full_name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (city_id, full_name, email, generate_password_hash(password), role, utc_now()),
            )

    users = db.execute("SELECT id, role FROM users").fetchall()
    for user in users:
        profile = db.execute("SELECT id FROM household_profiles WHERE user_id = ?", (user["id"],)).fetchone()
        if profile is None:
            db.execute(
                """
                INSERT INTO household_profiles (user_id, connection_id, address, meter_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    f"AQUA-{10000 + user['id']}",
                    f"Sector {user['id'] + 4}, Smart Water City",
                    f"FM-{22000 + user['id']}",
                    utc_now(),
                ),
            )
        bill = db.execute("SELECT id FROM water_bills WHERE user_id = ?", (user["id"],)).fetchone()
        if bill is None:
            db.execute(
                """
                INSERT INTO water_bills
                    (user_id, billing_month, consumption_kl, amount_due, due_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    "April 2026",
                    18.5 + user["id"],
                    420 + user["id"] * 38,
                    "2026-05-10",
                    "Unpaid" if user["role"] == "citizen" else "Paid",
                    utc_now(),
                ),
            )

    if db.execute("SELECT COUNT(*) AS count FROM alerts").fetchone()["count"] == 0:
        db.executemany(
            """
            INSERT INTO alerts (city_id, severity, zone, event, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (city_id, "High", "Industrial East", "Pressure deviation near bulk meter", "Investigating", utc_now()),
                (city_id, "Medium", "River Intake", "Turbidity increased above normal baseline", "Open", utc_now()),
                (city_id, "Low", "Residential West", "Demand spike resolved automatically", "Closed", utc_now()),
            ],
        )


def create_user(full_name: str, email: str, password: str, city_name: str, role: str = "citizen") -> Dict[str, Any]:
    with get_db() as db:
        city = db.execute("SELECT id FROM cities WHERE name = ?", (city_name,)).fetchone()
        if city is None:
            db.execute(
                "INSERT INTO cities (name, state, country, created_at) VALUES (?, ?, ?, ?)",
                (city_name, "Unknown", "India", utc_now()),
            )
            city = db.execute("SELECT id FROM cities WHERE name = ?", (city_name,)).fetchone()
        db.execute(
            """
            INSERT INTO users (city_id, full_name, email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (city["id"], full_name, email.lower(), generate_password_hash(password), role, utc_now()),
        )
        db.commit()
        return authenticate_user(email, password) or {}


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        row = db.execute(
            """
            SELECT users.*, cities.name AS city_name
            FROM users
            JOIN cities ON cities.id = users.city_id
            WHERE users.email = ? AND users.is_active = 1
            """,
            (email.lower(),),
        ).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            return None

        token = secrets.token_urlsafe(32)
        expires_at = (datetime.utcnow() + timedelta(hours=settings.auth_token_hours)).isoformat() + "Z"
        db.execute(
            "INSERT INTO auth_tokens (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (row["id"], token, expires_at, utc_now()),
        )
        user = user_public_dict(row)
        return {"token": token, "expires_at": expires_at, "user": user}


def user_public_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "city_id": row["city_id"],
        "city_name": row["city_name"],
        "full_name": row["full_name"],
        "email": row["email"],
        "role": row["role"],
    }


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        row = db.execute(
            """
            SELECT users.*, cities.name AS city_name, auth_tokens.expires_at
            FROM auth_tokens
            JOIN users ON users.id = auth_tokens.user_id
            JOIN cities ON cities.id = users.city_id
            WHERE auth_tokens.token = ? AND users.is_active = 1
            """,
            (token,),
        ).fetchone()
        if row is None:
            return None
        expires = datetime.fromisoformat(row["expires_at"].replace("Z", ""))
        if expires < datetime.utcnow():
            return None
        return user_public_dict(row)


def list_alerts(city_id: int) -> list[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT severity, zone, event, status, created_at AS time
            FROM alerts
            WHERE city_id = ?
            ORDER BY id DESC
            LIMIT 20
            """,
            (city_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def create_alert(
    city_id: int,
    severity: str,
    zone: str,
    event: str,
    status: str = "Open",
) -> Dict[str, Any]:
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO alerts (city_id, severity, zone, event, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (city_id, severity, zone, event, status, utc_now()),
        )
        alert_id = cursor.lastrowid
        row = db.execute(
            """
            SELECT id, severity, zone, event, status, created_at AS time
            FROM alerts
            WHERE id = ?
            """,
            (alert_id,),
        ).fetchone()
        return dict(row)


def save_prediction(user_id: int, city_id: int, prediction_type: str, input_json: str, result_json: str) -> None:
    with get_db() as db:
        db.execute(
            """
            INSERT INTO predictions (user_id, city_id, prediction_type, input_json, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, city_id, prediction_type, input_json, result_json, utc_now()),
        )


def save_control_action(user_id: int, city_id: int, strategy: str, zone: str, action: str) -> None:
    with get_db() as db:
        db.execute(
            """
            INSERT INTO control_actions (user_id, city_id, strategy, zone, action, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, city_id, strategy, zone, action, "Pending Approval", utc_now()),
        )


def list_saved_activity(city_id: int) -> Dict[str, Any]:
    with get_db() as db:
        predictions = db.execute(
            """
            SELECT prediction_type, result_json, created_at
            FROM predictions
            WHERE city_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (city_id,),
        ).fetchall()
        actions = db.execute(
            """
            SELECT strategy, zone, action, status, created_at
            FROM control_actions
            WHERE city_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (city_id,),
        ).fetchall()
        return {
            "predictions": [dict(row) for row in predictions],
            "control_actions": [dict(row) for row in actions],
        }


def create_complaint(
    user_id: int,
    city_id: int,
    category: str,
    zone: str,
    subject: str,
    description: str,
    priority: str,
) -> Dict[str, Any]:
    with get_db() as db:
        now = utc_now()
        cursor = db.execute(
            """
            INSERT INTO complaints
                (user_id, city_id, category, zone, subject, description, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, city_id, category, zone, subject, description, priority, "Open", now, now),
        )
        complaint_id = cursor.lastrowid
        row = db.execute(
            """
            SELECT complaints.*, users.full_name, users.email
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            WHERE complaints.id = ?
            """,
            (complaint_id,),
        ).fetchone()
        return dict(row)


def list_complaints(user: Dict[str, Any]) -> list[Dict[str, Any]]:
    with get_db() as db:
        if user["role"] in {"admin", "operator"}:
            rows = db.execute(
                """
                SELECT complaints.*, users.full_name, users.email
                FROM complaints
                JOIN users ON users.id = complaints.user_id
                WHERE complaints.city_id = ?
                ORDER BY complaints.id DESC
                LIMIT 100
                """,
                (user["city_id"],),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT complaints.*, users.full_name, users.email
                FROM complaints
                JOIN users ON users.id = complaints.user_id
                WHERE complaints.city_id = ? AND complaints.user_id = ?
                ORDER BY complaints.id DESC
                LIMIT 100
                """,
                (user["city_id"], user["id"]),
            ).fetchall()
        return [dict(row) for row in rows]


def update_complaint_status(
    complaint_id: int,
    city_id: int,
    status: str,
    response: str,
) -> Dict[str, Any] | None:
    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM complaints WHERE id = ? AND city_id = ?",
            (complaint_id, city_id),
        ).fetchone()
        if existing is None:
            return None
        db.execute(
            """
            UPDATE complaints
            SET status = ?, response = ?, updated_at = ?
            WHERE id = ? AND city_id = ?
            """,
            (status, response, utc_now(), complaint_id, city_id),
        )
        row = db.execute(
            """
            SELECT complaints.*, users.full_name, users.email
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            WHERE complaints.id = ?
            """,
            (complaint_id,),
        ).fetchone()
        return dict(row) if row else None


def create_rating(user_id: int, city_id: int, stars: int, comment: str) -> Dict[str, Any]:
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO ratings (user_id, city_id, stars, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, city_id, stars, comment, utc_now()),
        )
        rating_id = cursor.lastrowid
        row = db.execute(
            """
            SELECT ratings.*, users.full_name, users.email
            FROM ratings
            JOIN users ON users.id = ratings.user_id
            WHERE ratings.id = ?
            """,
            (rating_id,),
        ).fetchone()
        return dict(row)


def list_ratings(city_id: int) -> Dict[str, Any]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT ratings.*, users.full_name, users.email
            FROM ratings
            JOIN users ON users.id = ratings.user_id
            WHERE ratings.city_id = ?
            ORDER BY ratings.id DESC
            LIMIT 100
            """,
            (city_id,),
        ).fetchall()
        summary = db.execute(
            """
            SELECT COUNT(*) AS total, AVG(stars) AS average
            FROM ratings
            WHERE city_id = ?
            """,
            (city_id,),
        ).fetchone()
        return {
            "ratings": [dict(row) for row in rows],
            "summary": {
                "total": summary["total"] or 0,
                "average": round(summary["average"] or 0, 2),
            },
        }


def create_system_control(
    user_id: int,
    city_id: int,
    zone: str,
    control_type: str,
    target_value: float,
    unit: str,
    reason: str,
    safety_note: str,
) -> Dict[str, Any]:
    with get_db() as db:
        now = utc_now()
        cursor = db.execute(
            """
            INSERT INTO system_controls
                (user_id, city_id, zone, control_type, target_value, unit, reason, safety_note, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, city_id, zone, control_type, target_value, unit, reason, safety_note, "Pending Approval", now, now),
        )
        control_id = cursor.lastrowid
        row = db.execute(
            """
            SELECT system_controls.*, users.full_name, users.email
            FROM system_controls
            JOIN users ON users.id = system_controls.user_id
            WHERE system_controls.id = ?
            """,
            (control_id,),
        ).fetchone()
        return dict(row)


def list_system_controls(city_id: int) -> list[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT system_controls.*, users.full_name, users.email
            FROM system_controls
            JOIN users ON users.id = system_controls.user_id
            WHERE system_controls.city_id = ?
            ORDER BY system_controls.id DESC
            LIMIT 100
            """,
            (city_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def update_system_control_status(
    control_id: int,
    city_id: int,
    reviewer_id: int,
    status: str,
) -> Dict[str, Any] | None:
    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM system_controls WHERE id = ? AND city_id = ?",
            (control_id, city_id),
        ).fetchone()
        if existing is None:
            return None
        db.execute(
            """
            UPDATE system_controls
            SET status = ?, reviewer_id = ?, updated_at = ?
            WHERE id = ? AND city_id = ?
            """,
            (status, reviewer_id, utc_now(), control_id, city_id),
        )
        row = db.execute(
            """
            SELECT system_controls.*, users.full_name, users.email
            FROM system_controls
            JOIN users ON users.id = system_controls.user_id
            WHERE system_controls.id = ?
            """,
            (control_id,),
        ).fetchone()
        return dict(row) if row else None


def get_citizen_water_account(user: Dict[str, Any]) -> Dict[str, Any]:
    with get_db() as db:
        profile = db.execute(
            "SELECT connection_id, address, meter_id FROM household_profiles WHERE user_id = ?",
            (user["id"],),
        ).fetchone()
        if profile is None:
            db.execute(
                """
                INSERT INTO household_profiles (user_id, connection_id, address, meter_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    f"AQUA-{10000 + user['id']}",
                    f"Sector {user['id'] + 4}, {user['city_name']}",
                    f"FM-{22000 + user['id']}",
                    utc_now(),
                ),
            )
            profile = db.execute(
                "SELECT connection_id, address, meter_id FROM household_profiles WHERE user_id = ?",
                (user["id"],),
            ).fetchone()

        bill = db.execute(
            """
            SELECT billing_month, consumption_kl, amount_due, due_date, status
            FROM water_bills
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"],),
        ).fetchone()

        seed = user["id"] * 13
        tank_level = 52 + (seed % 43)
        flow_rate = round(8.5 + (seed % 9) * 0.7, 2)
        pressure = round(2.8 + (seed % 5) * 0.35, 2)
        turbidity = round(1.2 + (seed % 4) * 0.45, 2)
        ph = round(7.0 + ((seed % 5) - 2) * 0.12, 2)
        chlorine = round(0.45 + (seed % 4) * 0.08, 2)
        motor_status = "Running" if tank_level < 72 else "Standby"

        return {
            "profile": dict(profile),
            "bill": dict(bill) if bill else {
                "billing_month": "Current Month",
                "consumption_kl": 0,
                "amount_due": 0,
                "due_date": "N/A",
                "status": "No bill generated",
            },
            "tank": {
                "level_percent": tank_level,
                "capacity_liters": 1000,
                "estimated_available_liters": round(tank_level * 10, 1),
            },
            "motor": {
                "status": motor_status,
                "mode": "Automatic",
                "last_run": "Today 06:40",
                "health": "Good",
            },
            "quality": {
                "status": "Safe" if 6.5 <= ph <= 8.5 and turbidity < 5 else "Review Required",
                "ph": ph,
                "turbidity_ntu": turbidity,
                "chlorine_mg_l": chlorine,
                "tds_ppm": 310 + seed,
                "last_tested": "Today",
            },
            "flow_meter": {
                "meter_id": profile["meter_id"],
                "current_flow_l_min": flow_rate,
                "pressure_bar": pressure,
                "today_usage_liters": 420 + seed * 4,
                "month_usage_kl": round((bill["consumption_kl"] if bill else 18.5), 2),
            },
        }
