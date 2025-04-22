from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import os
import time

app = Flask(__name__)

# MongoDB setup with retry logic
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
db = client["gamified_lab"]
collection = db["students"]

# Sample student data
students = [
    {"name": "Alice", "stars": 0, "completed": 0, "badge": 0},
    {"name": "Bob", "stars": 0, "completed": 0, "badge": 0},
    {"name": "Charlie", "stars": 0, "completed": 0, "badge": 0}
]

# Insert data into the collection
try:
    collection.insert_many(students)
    print("Sample student data inserted successfully")
except Exception as e:
    print(f"Error inserting sample data: {e}")

# Add this after the `students` collection setup

# Sample web development questions
questions = [
    {"level": 1, "question": "What does HTML stand for?", "answer": "HyperText Markup Language"},
    {"level": 2, "question": "What is the purpose of the `<head>` tag in HTML?", "answer": "To contain metadata about the document"},
    {"level": 3, "question": "What CSS property is used to change the text color?", "answer": "color"},
    {"level": 4, "question": "What does the HTTP status code 404 mean?", "answer": "Not Found"},
    {"level": 5, "question": "What is the difference between `id` and `class` in HTML?", "answer": "id is unique, class can be reused"}
]

# Insert questions into the collection
questions_collection = db["questions"]
questions_collection.insert_many(questions)

print("Database populated with web development questions.")

current_student = None

@app.route('/', methods=['GET', 'POST'])
def login():
    global current_student
    if request.method == 'POST':
        name = request.form['name'].strip()
        student = collection.find_one({"name": name})
        if student:
            current_student = student
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Student not found.")
    return render_template('login.html', error=None)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', student=current_student)

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    global current_student
    if not current_student:
        return redirect(url_for('login'))

    # Get the current question based on the student's progress
    level = current_student["stars"] + 1
    question = db["questions"].find_one({"level": level})

    if not question:
        # If no question exists for the current level, redirect to the dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        answer = request.form['answer'].strip()
        if answer.lower() == question["answer"].lower():
            # Correct answer, redirect to complete the questionnaire
            return redirect(url_for('complete_questionnaire'))
        else:
            # Incorrect answer, show the error message
            return render_template('questionnaire.html', question=question, error="Incorrect answer. Try again.")

    # Render the questionnaire template with the current question
    return render_template('questionnaire.html', question=question, error=None)

@app.route('/complete')
def complete_questionnaire():
    global current_student
    if current_student["stars"] < 5:
        current_student["stars"] += 1
        current_student["completed"] += 1
        if current_student["stars"] == 5:
            current_student["badge"] = "Web Rookie ⭐"

        # Update the document in MongoDB
        collection.update_one(
            {"name": current_student["name"]},
            {"$set": {
                "stars": current_student["stars"],
                "completed": current_student["completed"],
                "badge": current_student["badge"]
            }}
        )
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=True)
