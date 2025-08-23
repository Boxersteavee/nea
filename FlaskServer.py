import os
from flask import Flask, flash, request
from werkzeug.utils import secure_filename
import ged2sql
from gedcom import parser
import time
import sqlite3

UPLOAD_FOLDER = 'gedcom'
ALLOWED_EXTENSIONS = {'ged', 'gedcom'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def main_page():
    message = ''
    if request.method == 'POST':
        if 'file' not in request.files:
            message = 'Please select a file.'
        else:
            file = request.files['file']
            if file.filename == '':
                message = 'Please select a file.'
            elif file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                time.sleep(0.5)
                try:
                    ged2sql.run(file_path)
                except sqlite3.DatabaseError:
                    message = 'Database file is corrupted. Please delete/move it and try again.'
                    os.remove(UPLOAD_FOLDER + "/" + filename)
                except (parser.GedcomFormatViolationError, AttributeError):
                    message = 'Gedcom Parse failed. Is this a valid Gedcom file?'
                    os.remove(UPLOAD_FOLDER + "/" + filename)
                else:
                    message = 'File uploaded successfully and Parsed.'
            else:
                message = 'Disallowed file type. Please upload a .ged or .gedcom file.'
    return f'''
    <!doctype html>
    <title>Upload and Parse File</title>
    <form method=post enctype=multipart/form-data>
        <input type=file name=file>
        <p>Select a .ged or .gedcom file</p>
        <input type=submit value="Upload and Parse">
    </form>
    <p>{message}</p>
    '''

if __name__ == "__main__":
    app.run(debug=True)