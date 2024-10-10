from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)

# SQLite database setup
DATABASE = 'resumes.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            file_data BLOB
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Handle file uploads
        files = request.files.getlist('files')  # Get multiple files from the form
        if len(files) > 10:
            return 'You can only upload up to 10 files', 400

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_data = file.read()

                # Insert the file into the SQLite database
                c.execute('INSERT INTO resumes (filename, file_data) VALUES (?, ?)', (filename, file_data))

        conn.commit()
        conn.close()

        return redirect(url_for('upload_file'))

    # Retrieve resumes from the database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, filename FROM resumes')
    resumes = [{'id': row[0], 'filename': row[1]} for row in c.fetchall()]
    conn.close()

    return render_template('index.html', resumes=resumes)

@app.route('/resume/<int:id>')
def get_resume(id):
    # Retrieve the file by its ID from the database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT filename, file_data FROM resumes WHERE id = ?', (id,))
    resume = c.fetchone()
    conn.close()

    if resume:
        filename, file_data = resume
        return send_from_directory(directory='.', filename=filename, as_attachment=True)

    return 'Resume not found', 404

if __name__ == '__main__':
    app.run(debug=True)
