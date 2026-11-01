"""
SQLite 本地题库持久化存储模块
"""
import hashlib
import sqlite3
import threading
from typing import Optional, Dict, Any
from config import DB_PATH, ENABLE_CACHE

_lock = threading.Lock()

class CacheStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        if ENABLE_CACHE:
            self._init_db()

    def _init_db(self):
        with _lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ocs_cache (
                        key TEXT PRIMARY KEY,
                        q_type TEXT,
                        title TEXT,
                        options TEXT,
                        answer TEXT,
                        reason TEXT,
                        model TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

    @staticmethod
    def _compute_key(q_type: str, title: str, options: str) -> str:
        raw = f"{str(q_type).strip().lower()}||{str(title).strip()}||{str(options).strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, q_type: str, title: str, options: str) -> Optional[Dict[str, Any]]:
        if not ENABLE_CACHE:
            return None
        key = self._compute_key(q_type, title, options)
        with _lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT answer, reason, model, created_at FROM ocs_cache WHERE key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
            except Exception:
                pass
        return None

    def set(self, q_type: str, title: str, options: str, answer: str, reason: str = "", model: str = ""):
        if not ENABLE_CACHE or not answer:
            return
        key = self._compute_key(q_type, title, options)
        with _lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ocs_cache (key, q_type, title, options, answer, reason, model)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (key, q_type, title, options, answer, reason, model))
                    conn.commit()
            except Exception:
                pass

    def count(self) -> int:
        if not ENABLE_CACHE:
            return 0
        with _lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM ocs_cache")
                    return cursor.fetchone()[0]
            except Exception:
                return 0

    def clear(self) -> int:
        """清空本地 SQLite 题库缓存记录并返回删除的数量"""
        with _lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM ocs_cache")
                    cnt = cursor.fetchone()[0]
                    cursor.execute("DELETE FROM ocs_cache")
                    conn.commit()
                    return cnt
            except Exception:
                return 0

cache = CacheStore()
