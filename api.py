from werkzeug.utils import secure_filename
import ged2sql
from gedcom import parser
import shutil
import sqlite3
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from config import get_cfg

api = FastAPI()
cfg = get_cfg()

# VARIABLES
UPLOAD_FOLDER = f"{cfg['user_data_dir']}/gedcom"

@api.get("/")
async def root():
    user_data_dir = cfg['user_data_dir']
    return {"message": "Hello World"}

# Take upload of gedcom file, process it, return 200 when complete.
# If the file is not provided, return 400.
# If there's another error, return 500 and provide the error.

@api.post("/upload/gedcom")
async def gedcom_upload(file: UploadFile = File(...)):
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