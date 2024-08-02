from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import random
import hashlib
import spacy
from textstat import flesch_kincaid_grade

# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

# Load the dataset
file_path = 'Logical q.xlsx'  # Update this path to your actual file path
df = pd.read_excel(file_path)  # Load Excel file

# Extract questions from the DataFrame
questions = df['Questions'].tolist()

# Store user sessions
user_sessions = {}

def hash_email(name, email):
    """Generate a hash based on the name and email to use for random seed."""
    combined = f"{name}_{email}".encode()
    return int(hashlib.md5(combined).hexdigest(), 16) % (10 ** 8)

def get_unique_question(name, email):
    """Generate a unique question for the student based on name and email."""
    seed = hash_email(name, email)
    random.seed(seed)
    question_index = random.randint(0, len(questions) - 1)
    return questions[question_index]

def start_session(name, email):
    """Start a new session for the user with a unique question."""
    student_id = f"{name}_{email}"
    unique_question = get_unique_question(name, email)
    user_sessions[student_id] = {"question": unique_question}
    return student_id

def get_current_question(student_id):
    """Retrieve the current question for the student."""
    if student_id not in user_sessions:
        raise ValueError(f"Session for student_id '{student_id}' not found.")
    session = user_sessions[student_id]
    question = session.get("question")
    return question

def evaluate_response(user_response):
    """Evaluate user response and provide feedback using NLP."""
    user_response = user_response.strip()

    if len(user_response) < 10:
        return "Your response is too short or not meaningful. Score: 0"

    doc = nlp(user_response)

    # Readability score
    readability_score = flesch_kincaid_grade(user_response)

    # Assess coherence and structure
    coherence_score = len(list(doc.sents))  # Simple count of sentences as a proxy for coherence

    # Basic scoring based on length, readability, and coherence
    if len(user_response.split()) < 20:
        score = 2
    elif readability_score > 12:
        score = max(0, 10 - (readability_score - 12))  # Penalize for high readability score
    elif coherence_score < 2:
        score = min(6, 2 + coherence_score * 2)  # Increase score for better coherence
    else:
        score = 8

    if len(user_response.split()) > 50:
        score = min(10, score + 1)  # Reward for longer, more detailed responses

    feedback = f"Your answer scored {score} out of 10.\n"
    if score == 0:
        feedback += "Response not meaningful or too short."
    elif score == 2:
        feedback += "Very poor response; lacks relevance and depth."
    elif score == 4:
        feedback += "Poor response; some relevance but lacks detail."
    elif score == 6:
        feedback += "Average response; moderately relevant and detailed."
    elif score == 8:
        feedback += "Good response; relevant and detailed."
    elif score == 10:
        feedback += "Excellent response; highly relevant and detailed."

    return feedback

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_session', methods=['POST'])
def start_session_route():
    name = request.form['name']
    email = request.form['email']
    student_id = start_session(name, email)
    return redirect(url_for('question', student_id=student_id))

@app.route('/question/<student_id>', methods=['GET', 'POST'])
def question(student_id):
    if request.method == 'POST':
        user_response = request.form['response']
        feedback = evaluate_response(user_response)
        return render_template('feedback.html', feedback=feedback)
    else:
        question = get_current_question(student_id)
        return render_template('question.html', question=question, student_id=student_id)

if __name__ == '__main__':
    app.run(debug=True)
