# Imports
from werkzeug.utils import secure_filename
import ged2sql
from gedcom import parser
import shutil
import sqlite3
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response, Request
from config import get_cfg
import auth
from pydantic import EmailStr
import sql2json
# When making changes to the auth_db directly,
# use the same instance of the DB class,
# this way there's only one open connection.
from auth import db as auth_db

# Set the config for FastAPI, and read the config file into cfg dictionary
api = FastAPI(root_path="/api")
cfg = get_cfg()

# Config-set variables
GEDCOM_DIR = f"{cfg['gedcom_dir']}"
SESSION_TTL = cfg['session_ttl']
TREE_NAME = cfg['tree_name']
DB_DIR = cfg['db_dir']


# Hello world test on root API (check it works)
@api.get("/")
async def root():
    return 'Hello World!'

##### GEDCOM MANAGEMENT #####
# Take upload of gedcom file, process it, return 200 when complete.
# If the file is not provided, return 400.
# If there's another error, return 500 and provide the error.
@api.post("/upload/gedcom")
async def gedcom_upload(request: Request, file: UploadFile = File(...)): # Get request data, including token cookie. Require file with request.
    token = request.cookies.get("token")
    # Check if cookie exists, if it doesn't respond with 401 (unauthorised) to say so.
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid token in order to upload files")
    # Check if session is valid, which returns a username if true, or None if not
    username = auth.validate_session(token)
    # If validate_session returns None, then the token is either expired or invalid, so the user is not authorised.
    if username is None:
        raise HTTPException(status_code=401, detail="You are not authorised to complete this request.")
    # If a file is not provided, exit and say so.
    if not file.filename:
        raise HTTPException(status_code=400, detail="File required")
    # Extract the file extension from the file, check if it is .ged or .gedcom (supported named for GEDCOM),
    # if it isn't, exit and say so.
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in {".ged", ".gedcom"}:
        raise HTTPException(status_code=400, detail="Wrong filetype. Must be .ged/.gedcom file")

    # Set the filename to remove invalid characters/spaces.
    # Create the UPLOAD_FOLDER if it doesn't exist
    filename = secure_filename(file.filename)
    os.makedirs(GEDCOM_DIR, exist_ok=True)
    file_path = os.path.join(GEDCOM_DIR, filename)
    # Save the uploaded file to file_path (UPLOAD_FOLDER joined with filename), report error if an error occurs.
    try:
        with open(file_path, "wb") as savefile:
            shutil.copyfileobj(file.file, savefile)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f'Error when saving file: {e}')
        raise HTTPException(status_code=500, detail=f"Error when saving file: {e}")

    # Attempt to parse gedcom file using ged2sql
    # Extract the tree name from the file path (filename without extension), then add this to the user's trees.
    try:
        ged2sql.run(file_path)
        tree_name = os.path.splitext(filename)[0]
        auth_db.add_tree_to_user(username, tree_name)
    # Some known errors are handled and different responses are sent.
    # If the error is unknown, the entire error message is output and the process stops.
    except sqlite3.DatabaseError as e:
        message = f'Database file is corrupted. Please delete/move it and try again. {e}'
        print(f"SQL.DatabaseError: {e}")
        os.remove(GEDCOM_DIR + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    except (parser.GedcomFormatViolationError, AttributeError) as e:
        message = f'Gedcom Parse failed. Is this a valid Gedcom file? {e}'
        print(f"GedcomFormatViolationError: {e}")
        os.remove(GEDCOM_DIR + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    except UnicodeDecodeError as e:
        message = f'The file is not a readable format. Please re-generate the file or try a different file. {e}'
        print(f'UnicodeDecodeError: {e}')
        os.remove(GEDCOM_DIR + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        message = f'An unexpected error occurred: {str(e)}'
        print(f"Unexpected Error: {e}")
        os.remove(GEDCOM_DIR + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    # If no errors are reported, return 200 ok.
    return {"status": "ok"}

##### USER MANAGEMENT #####

# Take user information and create a user, then create a session token to log them in.
@api.post('/login/create')
async def create_user(response: Response, username: str = Form(...), email: EmailStr = Form(...), password: str = Form(...)):
        # Send to auth to create the user, if the result is 200, then it was successful
        result = auth.create_user(username, email, password)
        if result == 200:
            # If result was successful, call to create a session with that username,
            # then set a cookie with the details of the token
            token, expires_at = auth.create_session(username)

            response.set_cookie(
                key="token",
                value=token,
                expires=expires_at,
                httponly=True,
                samesite="lax",
            )

            return {"username": username}
        elif result == 403:
            # If auth.create_user responds with 403, the user already exists. Respond with 403 saying so.
            raise HTTPException(status_code=403, detail="Username already exists")
        elif result == 400:
            raise HTTPException(status_code=400, detail="Password is not strong enough")
        else:
            # If auth.create_user responds with 500, some other error occured. This will be printed to the console,
            # and then an error is sent in the response (which is displayed on login page)
            raise HTTPException(status_code=500, detail="Error creating user")

# Verify user details and create session token to log them in.
@api.post('/login/verify')
async def verify_user(response: Response, username: str = Form(...), password: str = Form(...)):
    # Check if username or password are not in the response, if so then respond with 401 saying no username or password.
    if not username or not password:
        raise HTTPException(status_code=401, detail="You must provide a username and password")
    # Send username and password to auth.verify_user to check, result is either 200 or 401... Why haven't I done a boolean for these???
    result = auth.verify_user(username, password)
    # If result is 401, details are wrong, so say username or password incorrect.
    if not result:
        raise HTTPException(status_code=403, detail= "Username or Password incorrect")
    # Create session then set cookie.
    token, expires_at = auth.create_session(username)

    response.set_cookie(
        key="token",
        value=token,
        expires=expires_at,
        httponly=True,
        samesite="lax",
    )

    return {"username": username}

# Check the validity of the session, used on root page to decide whether to send user to /home
@api.get('/checksession')
async def check_session(request: Request):
    # Get session token from cookie of request
    token = request.cookies.get("token")
    # If there is no value to token, the user doesn't have a session cookie active, so they do not have a valid session token.
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid session token")
    # Check session token validity, if it's invalid, None is returned so raise 401 error.
    result = auth.validate_session(token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid Session Token")
    # If token is valid, return 200 OK.
    return {"status": "ok"}

# Delete a user from database.
@api.post('/login/delete')
async def delete_user(request: Request):
    # Get token, if doesn't exist, state one must be provided.
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid session token")
    # Try to delete the user, which checks session. If session is not valid, return 401 and state Invalid Session Token
    result = auth.delete_user(token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid Session Token")
    # If token is valid, revoke the session token after user is deleted, and return 200 OK.
    auth.revoke_session(token)
    return {"status": "ok"}

# Removes session token to logout a user.
@api.post('/login/logout')
async def delete_session(request: Request):
    # Get session token, if it's not provided, state one must be provided.
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid session token")
    # Revoke the session token (invalidate it), then return 200 OK.
    auth.revoke_session(token)
    return {"status": "ok"}

##### TREE ROUTES #####

# Gets the json for the given tree from SQL, if an error is encountered, return it.
@api.get('/tree')
async def get_tree(request: Request, tree: str):
    # Get session token from cookie, if it does not exist then state there must be a valid session token.
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid session token")
    # Check the token is valid, store in username variable. If validate_session returns None, it is invalid, so return 401 Unauthorised.
    username = auth.validate_session(token)
    if username is None:
        raise HTTPException(status_code=401, detail="You are not authorised to complete this request")

    # Check the user has access to the tree they ask for.
    if auth.check_tree_match(username, tree):
        # Try to convert the data from SQL to JSON, if there's an error return 500 with the error.
        try:
            output = sql2json.run(tree)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
        # If output does not find the file, return 404 Not Found
        if output == None:
            raise HTTPException(status_code=404, detail="Tree not found.")
        # Return the output from sql2json (JSON data)
        return output
    # If auth.check_tree_match does not return True, state Tree not found.
    else:
        raise HTTPException(status_code=404, detail="Tree not found.")

# Deletes the SQL and Gedcom file for the given tree, and removes it from the auth DB.
@api.post('/tree/delete')
async def delete_tree(request: Request, tree: str):
    # Get session token from cookie, check it exists. If it doesn't state 401 Unauthorised, must provide token.
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid session token")
    # Check token is valid, if auth.validate_session returns None, it is not, so return 401 Unauthorised.
    username = auth.validate_session(token)
    if username is None:
        raise HTTPException(status_code=401, detail="You not authorised to complete this request")
    # If the token is valid, call auth_db.delete_user_tree for the username and tree then delete the DB and gedcom file.
    try:
        auth_db.delete_user_tree(username, tree)
        tree_path = f"{DB_DIR}/{tree}.db"
        ged_path = f"{GEDCOM_DIR}/{tree}.ged"
        os.remove(tree_path)
        os.remove(ged_path)
    # If there's an error with deleting, return 500 and state the error.
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    # If everything works fine, return 200 OK.
    return {"status": "ok"}

# Get the user's list of trees and return it as a JSON object list.
@api.get('/trees')
async def get_trees(request: Request):
    # Get the session token from cookies, if it does not exist, return 401 and state it must be provided.
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid session token")
    # Check session is valid, if it is then the username is returned.
    username = auth.validate_session(token)
    # None is returned by auth.validate_session if the session is not valid, so return 401 Unauthorised.
    if username is None:
        raise HTTPException(status_code=401, detail="You are not authorised to complete this request")
    # Once the user is authorised, get get their trees from auth_db using the username from validate_session, returns a list.
    trees = auth_db.get_user_trees(username)
    # Return this list into a JSON object.
    return {"trees": trees}

# Retrieve session_ttl, used when figuring out session expiry
@api.get('/config/ttl')
async def get_ttl():
    return {'ttl': SESSION_TTL}

# Retrieve tree_name, used for the home page to display the tree name.
@api.get('/config/name')
async def get_name():
    return {'name': TREE_NAME}