import os
import secrets
import sqlite3
import time
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'ham_bot.db')


def _get_conn() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                platform TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT DEFAULT '',
                full_name TEXT DEFAULT '',
                sub_token TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                invited_by TEXT DEFAULT '',
                created_at INTEGER NOT NULL,
                PRIMARY KEY (platform, user_id)
            );

            CREATE TABLE IF NOT EXISTS invites (
                code TEXT PRIMARY KEY,
                created_by TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                used_by TEXT DEFAULT NULL,
                used_at INTEGER DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS allowed_groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT DEFAULT '',
                added_by INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS seen_strangers (
                platform TEXT NOT NULL,
                user_id TEXT NOT NULL,
                first_seen_at INTEGER NOT NULL,
                PRIMARY KEY (platform, user_id)
            );

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        conn.commit()


def set_meta(key: str, value: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


def get_meta(key: str) -> Optional[str]:
    with _get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row['value'] if row else None


def is_valid_personal_token(token: str) -> bool:
    if not token:
        return False
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE sub_token = ? AND is_active = 1",
            (token,),
        ).fetchone()
        return row is not None


def get_or_create_tg_user(
    user_id: int,
    username: str = '',
    full_name: str = '',
    invited_by: str = '',
) -> str:
    uid = str(user_id)
    now = int(time.time())
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT sub_token, is_active FROM users WHERE platform = 'tg' AND user_id = ?",
            (uid,),
        ).fetchone()
        if row:
            if row['is_active'] != 1:
                conn.execute(
                    "UPDATE users SET is_active = 1, username = ?, full_name = ? "
                    "WHERE platform = 'tg' AND user_id = ?",
                    (username, full_name, uid),
                )
                conn.commit()
            else:
                conn.execute(
                    "UPDATE users SET username = ?, full_name = ? "
                    "WHERE platform = 'tg' AND user_id = ?",
                    (username, full_name, uid),
                )
                conn.commit()
            return row['sub_token']

        sub_token = secrets.token_urlsafe(18)
        conn.execute(
            "INSERT INTO users (platform, user_id, username, full_name, sub_token, is_active, invited_by, created_at) "
            "VALUES ('tg', ?, ?, ?, ?, 1, ?, ?)",
            (uid, username, full_name, sub_token, invited_by, now),
        )
        conn.commit()
        return sub_token


def is_tg_user_allowed(user_id: int) -> bool:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE platform = 'tg' AND user_id = ? AND is_active = 1",
            (str(user_id),),
        ).fetchone()
        return row is not None


def create_invite(created_by: str, ttl_hours: int = 24) -> str:
    code = secrets.token_urlsafe(12)
    expires_at = int(time.time()) + ttl_hours * 3600
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO invites (code, created_by, expires_at) VALUES (?, ?, ?)",
            (code, created_by, expires_at),
        )
        conn.commit()
    return code


def redeem_invite(
    code: str,
    user_id: int,
    username: str = '',
    full_name: str = '',
) -> Optional[str]:
    now = int(time.time())
    uid = str(user_id)
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT code, created_by, expires_at, used_by FROM invites WHERE code = ?",
            (code,),
        ).fetchone()
        if not row:
            return None
        if row['used_by'] is not None or row['expires_at'] < now:
            return None

        cur = conn.execute(
            "UPDATE invites SET used_by = ?, used_at = ? WHERE code = ? AND used_by IS NULL",
            (uid, now, code),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return None

        existing = conn.execute(
            "SELECT sub_token FROM users WHERE platform = 'tg' AND user_id = ?",
            (uid,),
        ).fetchone()
        if existing:
            sub_token = existing['sub_token']
            conn.execute(
                "UPDATE users SET is_active = 1, username = ?, full_name = ?, invited_by = ? "
                "WHERE platform = 'tg' AND user_id = ?",
                (username, full_name, row['created_by'], uid),
            )
        else:
            sub_token = secrets.token_urlsafe(18)
            conn.execute(
                "INSERT INTO users (platform, user_id, username, full_name, sub_token, is_active, invited_by, created_at) "
                "VALUES ('tg', ?, ?, ?, ?, 1, ?, ?)",
                (uid, username, full_name, sub_token, row['created_by'], now),
            )
        conn.commit()
        return sub_token


def revoke_tg_user(user_id: int) -> bool:
    with _get_conn() as conn:
        cur = conn.execute(
            "UPDATE users SET is_active = 0 WHERE platform = 'tg' AND user_id = ?",
            (str(user_id),),
        )
        conn.commit()
        return cur.rowcount > 0


def list_tg_users() -> List[Dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, username, full_name, is_active, invited_by, created_at "
            "FROM users WHERE platform = 'tg' ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def mark_stranger_if_new(platform: str, user_id: str) -> bool:
    now = int(time.time())
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO seen_strangers (platform, user_id, first_seen_at) VALUES (?, ?, ?)",
            (platform, str(user_id), now),
        )
        conn.commit()
        return cur.rowcount == 1


def set_group_allowed(chat_id: int, title: str, added_by: int, active: bool = True) -> None:
    now = int(time.time())
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO allowed_groups (chat_id, title, added_by, is_active, created_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title, is_active = excluded.is_active",
            (chat_id, title, added_by, 1 if active else 0, now),
        )
        conn.commit()


def is_group_allowed(chat_id: int) -> bool:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM allowed_groups WHERE chat_id = ? AND is_active = 1",
            (chat_id,),
        ).fetchone()
        return row is not None
