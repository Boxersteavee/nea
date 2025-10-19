from passlib.context import CryptContext
from database import Database
import os

db = Database('user_data/auth.db')
db.create_user_db()
plctx = CryptContext(schemes=["argon2"], deprecated="auto")

def create_user(username, email, password):
    salt = os.urandom(16)
    pass_hash = plctx.hash(password, salt=salt)
    db.new_user(username, email, pass_hash, salt)

def verify_user(username, password):
    pass_hash, salt = db.verify_user(username)
    if pass_hash and salt:
        given_pass = plctx.hash(password, salt=salt)
        if given_pass == pass_hash:
            print("Password Correct")
            # allow access
        else:
            print("Password Incorrect")
            # make them retry
    else:
        print("Username does not exist")
        # make them retry