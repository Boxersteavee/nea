from werkzeug.utils import secure_filename
import ged2sql
from gedcom import parser
import shutil
import sqlite3
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response
from config import get_cfg
import auth
from pydantic import EmailStr
import sql2json

api = FastAPI(root_path="/api")
cfg = get_cfg()

# VARIABLES
UPLOAD_FOLDER = f"{cfg['user_data_dir']}/gedcom"
@api.get("/")
async def root():
    return 'Hello World!'

# Take upload of gedcom file, process it, return 200 when complete.
# If the file is not provided, return 400.
# If there's another error, return 500 and provide the error.

##### GEDCOM MANAGEMENT #####
@api.post("/upload/gedcom")
async def gedcom_upload(file: UploadFile = File(...), token: str = Form(...)):
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid token in order to upload files")
    username = auth.validate_session(token)
    if username == 401:
        raise HTTPException(status_code=401, detail="You are not authorised to complete this request.")
    if not file.filename:
        raise HTTPException(status_code=400, detail="File required")
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in {".ged", ".gedcom"}:
        raise HTTPException(status_code=400, detail="Wrong filetype. Must be .ged/.gedcom file")

    #Save uploaded file to UPLOAD_FOLDER
    filename = secure_filename(file.filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(file_path, "wb") as savefile:
            shutil.copyfileobj(file.file, savefile)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error when saving file: {e}")

    try:
        ged2sql.run(file_path)
    except sqlite3.DatabaseError as e:
        message = f'Database file is corrupted. Please delete/move it and try again. {e}'
        print(f"SQL.DatabaseError: {e}")
        os.remove(UPLOAD_FOLDER + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    except (parser.GedcomFormatViolationError, AttributeError) as e:
        message = f'Gedcom Parse failed. Is this a valid Gedcom file? {e}'
        print(f"GedcomFormatViolationError: {e}")
        os.remove(UPLOAD_FOLDER + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    except UnicodeDecodeError as e:
        message = f'The file is not a readable format. Please re-generate the file or try a different file. {e}'
        print(f'UnicodeDecodeError: The file is not encoded in UTF-8 format: {e}')
        os.remove(UPLOAD_FOLDER + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    except Exception as e:
        message = f'An unexpected error occurred: {str(e)}'
        print(f"Unexpected Error: {e}")
        os.remove(UPLOAD_FOLDER + "/" + filename)
        raise HTTPException(status_code=500, detail=message)
    return {"status": "ok"}

##### USER MANAGEMENT #####
@api.post('/login/create')
async def create_user(username: str = Form(...), email: EmailStr = Form(...), password: str = Form(...)):
        result = auth.create_user(username, email, password)
        if result == 200:
            return {"status": f"User {username} created successfully"}
        elif result == 403:
            raise HTTPException(status_code=403, detail="Username already exists")
        else:
            raise HTTPException(status_code=500, detail="Error creating user")

@api.post('/login/verify')
async def verify_user(response: Response, username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="You must provide a username and password")
    result = auth.verify_user(username, password)
    if result == 401:
        raise HTTPException(status_code=403, detail= "Username or Password incorrect")
    token, expires_at = auth.create_session(username)

    response.set_cookie(
        key="token",
        value=token,
        expires=expires_at,
        httponly=True,
        samesite="lax",
    )

    return {"username": username}

@api.post('/login/delete')
async def delete_user(token: str = Form(...)):
    if not token:
        raise HTTPException(status_code=400, detail="You must provide a valid session token")
    result = auth.delete_user(token)
    if result == 401:
        raise HTTPException(status_code=401, detail="Invalid Session Token")
    auth.revoke_session(token)
    return {"status": "ok"}

@api.post('/login/logout')
async def delete_session(token: str = Form(...)):
    if not token:
        raise HTTPException(status_code=400, detail="You must provide a valid session token")
    auth.revoke_session(token)
    return {"status": "ok"}



##### TREE ROUTES #####
@api.get('/tree/test')
async def test_data():
    data = [
        {"id": 4, "Name": "Ben Harris", "gender": "male", "Birth Place": "Gateshead", "fid": 1, "mid": 2},
        {"id": 1, "Name": "David Harris", "gender": "male", "pids": [2]},
        {"id": 2, "Name": "Janice Harris", "gender": "female", "pids": [1]},
        {"id": 3, "Name": "Alice Harris", "gender": "female", "Birth Place": "Nijmegen", "Death Place": "", "fid": 1, "mid": 2},
    ]
    return data

@api.get('/tree')
async def get_tree(token: str, tree: str):
    if not token:
        raise HTTPException(status_code=400, detail="You must provide a valid session token")
    result = auth.validate_session(token)
    if result == 401:
        raise HTTPException(status_code=401, detail="You are not authorised to complete this request")
    try:
        output = sql2json.run(tree)
    except any as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    if output == 404:
        raise HTTPException(status_code=404, detail="Tree not found.")
    return output

@api.get('/config/ttl')
async def get_ttl():
    return {'ttl': cfg['session_ttl']}