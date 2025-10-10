import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import ged2sql
from gedcom import parser
import time
import sqlite3

UPLOAD_FOLDER = 'user_data/gedcom'
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
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                time.sleep(0.5)
                try:
                    ged2sql.run(file_path)
                except sqlite3.DatabaseError as e:
                    message = f'Database file is corrupted. Please delete/move it and try again. {e}'
                    print(f"SQL.DatabaseError: {e}")
                    os.remove(UPLOAD_FOLDER + "/" + filename)
                except (parser.GedcomFormatViolationError, AttributeError) as e:
                    message = 'Gedcom Parse failed. Is this a valid Gedcom file?'
                    print(f"GedcomFormatViolationError: {e}")
                    os.remove(UPLOAD_FOLDER + "/" + filename)
                except UnicodeDecodeError as e:
                    message = 'The file is not a readable format. Please re-generate the file or try a different file.'
                    print(f'UnicodeDecodeError: The file is not encoded in UTF-8 format: {e}')
                    os.remove(UPLOAD_FOLDER + "/" + filename)
                except Exception as e:
                    message = f'An unexpected error occurred: {str(e)}'
                    print(f"Unexpected Error: {e}")
                    os.remove(UPLOAD_FOLDER + "/" + filename)
                else:
                    message = 'File uploaded successfully and Parsed.'
            else:
                message = 'Disallowed file type. Please upload a .ged or .gedcom file.'
    return render_template('index.html', message=message)

if __name__ == "__main__":
    app.run(debug=True)