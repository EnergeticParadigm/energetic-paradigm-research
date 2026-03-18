
import os
import sqlite3
import threading
import time


class NonceStore:
    def __init__(self, db_path: str, ttl_seconds: int) -> None:
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=30, isolation_level=None)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nonces (
                    nonce TEXT PRIMARY KEY,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nonces_created_at ON nonces(created_at)")

    def cleanup(self) -> None:
        cutoff = int(time.time()) - self.ttl_seconds
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM nonces WHERE created_at < ?", (cutoff,))

    def consume(self, nonce: str) -> bool:
        self.cleanup()
        now = int(time.time())
        with self._lock:
            try:
                with self._connect() as conn:
                    conn.execute("INSERT INTO nonces (nonce, created_at) VALUES (?, ?)", (nonce, now))
                return True
            except sqlite3.IntegrityError:
                return False
