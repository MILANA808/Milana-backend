from __future__ import annotations

import hashlib

import app.db_sqlite as db


def test_new_password_hash_uses_pbkdf2_and_authenticates(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "users.sqlite3"))
    db.init_db()
    user = db.register_user("aksi-user", "correct horse battery")
    assert user["username"] == "aksi-user"
    with db.connect() as conn:
        row = conn.execute("SELECT password_hash, salt FROM users WHERE username=?", ("aksi-user",)).fetchone()
    assert row["password_hash"].startswith("pbkdf2_sha256$310000$")
    assert db.login_user("aksi-user", "correct horse battery")["id"] == user["id"]
    try:
        db.login_user("aksi-user", "wrong password")
    except ValueError as exc:
        assert str(exc) == "invalid credentials"
    else:
        raise AssertionError("wrong password was accepted")


def test_legacy_sha256_hash_is_upgraded_after_successful_login(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "legacy.sqlite3"))
    db.init_db()
    user = db.register_user("legacy-user", "old password")
    legacy_salt = "a1b2c3d4e5f60708"
    legacy_hash = hashlib.sha256(f"old password|{legacy_salt}|{db.SEED}".encode()).hexdigest()
    with db.connect() as conn:
        conn.execute("UPDATE users SET salt=?, password_hash=? WHERE id=?", (legacy_salt, legacy_hash, user["id"]))
    assert db.login_user("legacy-user", "old password")["id"] == user["id"]
    with db.connect() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
    assert row["password_hash"].startswith("pbkdf2_sha256$310000$")
