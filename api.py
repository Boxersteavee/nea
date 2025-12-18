from werkzeug.utils import secure_filename
import ged2sql
from gedcom import parser
import shutil
import sqlite3
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from config import get_cfg
import auth
from pydantic import EmailStr

api = FastAPI()
cfg = get_cfg()

# VARIABLES
UPLOAD_FOLDER = f"{cfg['user_data_dir']}/gedcom"

@api.get("/")
async def root():
    user_data_dir = cfg['user_data_dir']
    return 'Hello World! Visit /docs to see documentation on available requests.'

# Take upload of gedcom file, process it, return 200 when complete.
# If the file is not provided, return 400.
# If there's another error, return 500 and provide the error.

##### GEDCOM MANAGEMENT #####
@api.post("/upload/gedcom")
async def gedcom_upload(file: UploadFile = File(...), token: str = Form(...)):
    if not token:
        raise HTTPException(status_code=401, detail="You must provide a valid token in order to upload files")
    username = auth.validate_session(token)
    if username == None:
        raise HTTPException(status_code=403, detail="You are not authorised to complete this request.")
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
async def verify_user(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="You must provide a username and password")
    result = auth.verify_user(username, password)
    if result == 401:
        raise HTTPException(status_code=403, detail= "Username or Password incorrect")
    token, expires_at = auth.create_session(username)
    return {"token": token, "expires": expires_at}

@api.post('/login/delete')
async def delete_user(token: str = Form(...)):
    if not token:
        raise HTTPException(status_code=400, detail="You must provide a valid session token")
    result = auth.delete_user(token)
    if result == 401:
        raise HTTPException(status_code=401, detail="Invalid Session Token")
    return {"status": "ok"}

@api.get('/tree/test')
async def test_data():
    data = [
        {"id": 1, "name": "Ben", "gender": "male", "fid": 2, "mid": 3, "img": ""},
        {"id": 2, "name": "David", "gender": "male", "pids": [3], "img": ""},
        {"id": 3, "name": "Janice", "gender": "female", "pids": [2], "img": ""},
        {"id": 4, "name": "Alice", "gender": "female", "fid": 2, "mid": 3, "img": ""},
    ]
    return data