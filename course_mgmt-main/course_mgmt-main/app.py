from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import gridfs
from datetime import datetime
from bson import ObjectId
import os
import time

app = Flask(__name__)

# Connect to MongoDB with retry logic
def connect_to_mongodb():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://mongodb:27017/')
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            client.admin.command('ping')
            print(f"Successfully connected to MongoDB at {mongodb_uri}")
            return client
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to MongoDB.")
                raise

# Initialize MongoDB connection
client = connect_to_mongodb()
db = client["filedb"]
fs = gridfs.GridFS(db)

# Role selection page
@app.route('/')
def role_selection():
    return render_template('role_selection.html')

# Teacher page (upload form)
@app.route('/teacher')
def teacher():
    return render_template('upload.html')

# Student dashboard
@app.route('/student')
def student():
    # Fetch courses based on student_status
    available_courses = list(fs.find({"metadata.student_status": "available"}))
    started_courses = list(fs.find({"metadata.student_status": "started"}))
    completed_courses = list(fs.find({"metadata.student_status": "completed"}))
    return render_template('student_dashboard.html', 
                           available_courses=available_courses,
                           started_courses=started_courses, 
                           completed_courses=completed_courses)

# Handle course uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    title = request.form['title']
    description = request.form['description']
    resource_type = request.form['resource_type']
    course = request.form['course']
    access_level = request.form['access_level']
    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    # Store the file with student_status as "available"
    fs.put(file, filename=file.filename, metadata={
        "title": title,
        "description": description,
        "resource_type": resource_type,
        "course": course,
        "access_level": access_level,
        "uploadDate": datetime.utcnow(),
        "student_status": "available"
    })
    return redirect('/teacher')

# Start a course
@app.route('/start_course/<file_id>', methods=['POST'])
def start_course(file_id):
    file = fs.find_one({"_id": ObjectId(file_id)})
    if file and file.metadata.get("student_status") == "available":
        try:
            file_content = file.read()
            fs.delete(ObjectId(file_id))
            fs.put(file_content, filename=file.filename, metadata={
                **file.metadata,
                "student_status": "started",
                "startDate": datetime.utcnow()
            })
        except Exception as e:
            print(f"Error starting course: {e}")
            return "An error occurred while starting the course.", 500
    return redirect('/student')

# Complete a course
@app.route('/complete_course/<file_id>', methods=['POST'])
def complete_course(file_id):
    file = fs.find_one({"_id": ObjectId(file_id)})
    if file and file.metadata.get("student_status") == "started":
        try:
            file_content = file.read()
            fs.delete(ObjectId(file_id))
            fs.put(file_content, filename=file.filename, metadata={
                **file.metadata,
                "student_status": "completed",
                "completionDate": datetime.utcnow()
            })
        except Exception as e:
            print(f"Error completing course: {e}")
            return "An error occurred while completing the course.", 500
    return redirect('/student')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)