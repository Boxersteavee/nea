import sqlite3

from passlib.hash import argon2
from database import Database
from config import get_cfg
from datetime import datetime, timedelta
import secrets

cfg = get_cfg()

db = Database(f'{cfg['user_data_dir']}/auth.db')
session_ttl = timedelta(hours=(float(cfg['session_ttl'])))
db.create_user_db()
db.create_sessions_table()

##### USER MANAGEMENT #####
def create_user(username, email, password):
    pass_hash = argon2.hash(password)
    try:
        db.new_user(username, email, pass_hash)
    except sqlite3.IntegrityError:
        return 403
    else:
        return 200

def verify_user(username, password):
    pass_hash = db.verify_user(username)
    if pass_hash:
        if argon2.verify(password, pass_hash):
            return 200
        else:
            return 401
    else:
        return 401

def delete_user(token):
    username = validate_session(token)
    if not username:
        return 401
    db.delete_user(username)
    return 200

##### SESSION MANAGEMENT #####
def validate_session(token):
    row = db.get_session(token)
    if not row:
        return None
    token, username, expires_at = row
    if datetime.fromisoformat(expires_at) < datetime.utcnow():
        db.delete_session(token)
        return None
    return username

def revoke_session(token):
    db.delete_session(token)

def create_session(username):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + session_ttl
    db.save_session(username, token, expires_at)
    return token, expires_at