import sqlite3
from passlib.hash import argon2
from database import Database
from config import get_cfg
from datetime import datetime, timedelta, timezone
import secrets
import os

# Get config dictionary and set constants used in auth.
cfg = get_cfg()
SESSION_TTL = timedelta(hours=(float(cfg['session_ttl'])))
USER_DIR = str(cfg['user_data_dir'])

# Create User directory, connect to/create database, and create the Auth DB tables (if they don't exist).
os.makedirs(USER_DIR, exist_ok=True)
db = Database(f'{USER_DIR}/auth.db')
db.create_auth_db()
db.clear_sessions() # Clear open sessions when program restarts, logging out all users.

##### USER MANAGEMENT #####
# Take user details, hash the password, create a new user entry with details in DB.
# If there's any errors, respond with the error, else return true.
def create_user(username, email, password):
    pass_hash = argon2.hash(password)
    try:
        db.new_user(username, email, pass_hash)
    except sqlite3.IntegrityError:
        return 403
    except Exception as e:
        print(f'Unknown Error Occurred when creating user: {e}')
        return 500
    finally:
        return 200

# Take username and password, retrieve the hash from that username.
# Check password against hash, if it's valid respond with 200(ok), else return 401 (unauthorised)
def verify_user(username, password):
    pass_hash = db.verify_user(username)
    if pass_hash:
        if argon2.verify(password, pass_hash):
            return True
        else:
            return False
    else:
        return False

# Take session token, validate it (which returns the username if valid), and then call db.delete_user on that username.
# If the session is not valid, return None.
def delete_user(token):
    username = validate_session(token)
    if username is None:
        return None
    else:
        revoke_session(token)
        db.delete_user(username)
    return True

# Take a username and tree, get a user's list of trees from DB.
# If the provided tree is in that list, return True, else return False.
def check_tree_match(username, tree):
    trees = db.get_user_trees(username)
    if tree in trees:
        return True
    else:
        return False

##### SESSION MANAGEMENT #####
# Get the session for that token from DB, if it doesn't exist, return 401 (unauthorised).
# If it does exist, check the time is in the future (not expired).
# If it is expired, delete the session token, if it is valid, return 200 (ok)
def validate_session(token):
    row = db.get_session(token)
    if not row:
        return None
    token, username, expires_at = row
    if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
        revoke_session(token)
        return None
    return username

# Delete the session from that token
def revoke_session(token):
    db.delete_session(token)

# Take the username, generate a 32 byte token, take the current time,
# add the time from SESSION_TTL (config for session time, in hours),
# then create that session in the DB.
def create_session(username):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    db.save_session(username, token, expires_at)
    return token, expires_at