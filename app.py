from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os
import sqlite3
from werkzeug.utils import secure_filename
import PyPDF2
import docx

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}

# Initialize database
def init_db():
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, filename TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Upload file and store in the database
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text and store in the database
            file_content = extract_text(filepath, filename)
            save_to_db(filename, file_content)
            
            return redirect(url_for('search'))
    return render_template('upload.html')

def extract_text(filepath, filename):
    # Extract text from PDF
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    # Extract text from DOCX
    elif filename.endswith('.docx'):
        return extract_text_from_docx(filepath)

def extract_text_from_pdf(filepath):
    text = ''
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

# Save the resume content in the database
def save_to_db(filename, content):
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute("INSERT INTO resumes (filename, content) VALUES (?, ?)", (filename, content))
    conn.commit()
    conn.close()

# Search for resumes matching a description
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['description']
        matched_resumes = search_resumes(search_query)
        return render_template('results.html', resumes=matched_resumes)
    return render_template('search.html')

def search_resumes(description):
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute("SELECT filename FROM resumes WHERE content LIKE ?", ('%' + description + '%',))
    results = c.fetchall()
    conn.close()
    return results

# Download matched resume
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
