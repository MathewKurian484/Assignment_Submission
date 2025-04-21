from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['assignment_app']
submissions = db['submissions']
users = db['users']

# Ensure teacher and student accounts exist
if not users.find_one({"username": "teacher"}):
    users.insert_one({"username": "teacher", "password": "pass123", "role": "teacher"})

if not users.find_one({"username": "student1"}):
    users.insert_one({"username": "student1", "password": "abc123", "role": "student"})

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users.find_one({"username": request.form['username'], "password": request.form['password']})
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')


@app.route('/student_dashboard')
def student_dashboard():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    # Fetch only assignments with type 'assignment' (singular)
    assignments = db.submissions.find({"type": "assignment"})
    return render_template('student_dashboard.html', assignments=assignments)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['role'] == 'teacher':
        all_submissions = submissions.find()
        uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
        return render_template('dashboard.html', submissions=all_submissions, files=uploaded_files)
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    assignment_id = request.args.get('assignment_id')  # Get the assignment ID from the query string
    assignment = None

    if assignment_id:
        from bson.objectid import ObjectId
        assignment = submissions.find_one({"_id": ObjectId(assignment_id)})

    if request.method == 'POST':
        pdf = request.files['pdf']
        if pdf.filename.endswith('.pdf'):
            filename = secure_filename(pdf.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf.save(path)

            submissions.insert_one({
                'student': session['username'],
                'filename': filename,
                'assignment_id': assignment_id,
                'grade': None
            })
        return redirect(url_for('student_dashboard'))

    return render_template('upload.html', assignment=assignment)

@app.route('/grade/<submission_id>', methods=['GET', 'POST'])
def grade(submission_id):
    from bson.objectid import ObjectId

    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    sub = submissions.find_one({'_id': ObjectId(submission_id)})

    if request.method == 'POST':
        grade = request.form['grade']
        submissions.update_one({'_id': ObjectId(submission_id)}, {'$set': {'grade': grade}})
        return redirect(url_for('dashboard'))

    return render_template('grade.html', sub=sub)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)