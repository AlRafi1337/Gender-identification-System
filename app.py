import os
from flask import Flask, render_template, redirect, url_for, request, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production security

# Directory configurations
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Load YOLO model
model = YOLO("models/best.pt")  

# Mock user data
users = {}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('selection'))  # Redirect to new selection page

        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if username in users:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        users[username] = {
            'email': email,
            'password': generate_password_hash(password)
        }
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/menu')
def menu():
    if 'username' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))
    return render_template('menu.html')

@app.route('/upload_data', methods=['GET', 'POST'])
def upload_data():
    if 'username' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    results = []
    summary = {
        "total_images": 0,
        "male_count": 0,  # Ensure lowercase keys
        "female_count": 0,
        "low_confidence": 0
    }
    visualizations = []

    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No file part detected.', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('No files selected. Please choose images.', 'danger')
            return redirect(request.url)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Perform YOLO inference
                detection_results = model(filepath)
                output_img_path = os.path.join(app.config['RESULT_FOLDER'], f"output_{filename}")

                for result in detection_results:
                    image = result.plot()
                    cv2.imwrite(output_img_path, image)
                    visualizations.append(f"results/output_{filename}")

                for result in detection_results:
                    for box in result.boxes:
                        cls = result.names[int(box.cls[0])]
                        conf = float(box.conf[0])

                        # Adjust label for low confidence
                        flagged = False
                        if conf < 0.5:
                            summary["low_confidence"] += 1
                            flagged = True
                            if cls.lower() == "female":  # Make sure comparison is case-insensitive
                                cls = "male"

                        key = f"{cls.lower()}_count"  # Convert class to lowercase and match dictionary key
                        if key in summary:
                            summary[key] += 1  # ✅ Fixes KeyError

                        results.append({
                            "filename": filename,
                            "label": cls,
                            "confidence": round(conf * 100, 2),
                            "flagged": flagged
                        })

                summary["total_images"] += 1

    session['summary'] = summary
    session['results'] = results
    session['visualizations'] = visualizations

    return render_template('upload_data.html', results=results, summary=summary, visualizations=visualizations)



@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if 'username' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))

    username = session.get('username', 'Unknown User')  # Get logged-in username
    results = session.get('results', [])
    summary = session.get('summary', {})
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Gender Detection Report", ln=True, align='C')
        pdf.ln(10)

        pdf.cell(200, 10, txt=f"Generated By: {username}", ln=True)
        pdf.cell(200, 10, txt=f"Date: {current_date}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt=f"Total Images: {summary.get('total_images', 0)}", ln=True)
        pdf.cell(200, 10, txt=f"Male: {summary.get('male_count', 0)}", ln=True)
        pdf.cell(200, 10, txt=f"Female: {summary.get('female_count', 0)}", ln=True)
        pdf.cell(200, 10, txt=f"Low Confidence: {summary.get('low_confidence', 0)}", ln=True)
        pdf.ln(10)

        pdf.cell(200, 10, txt="Detection Results:", ln=True)
        for result in results:
            status = "LOW CONFIDENCE" if result['flagged'] else "OK"
            pdf.cell(200, 10, txt=f"{result['filename']}: {result['label']} ({result['confidence']}%) - {status}", ln=True)

        report_path = os.path.join(app.config['RESULT_FOLDER'], 'report.pdf')
        pdf.output(report_path)
        flash('Report generated successfully!', 'success')
        return send_from_directory(app.config['RESULT_FOLDER'], 'report.pdf', as_attachment=True)

    return render_template('reports.html', results=results, summary=summary, date=current_date, username=username)


@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if 'username' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))

    reminders_list = session.get('reminders', [])
    if request.method == 'POST':
        title = request.form.get('title')
        date_time = request.form.get('date_time')
        reminders_list.append({'title': title, 'date_time': date_time})
        session['reminders'] = reminders_list
        flash('Reminder added!', 'success')

    return render_template('reminders.html', reminders=reminders_list)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))
    return render_template('settings.html')
@app.route('/selection')
def selection():
    if 'username' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    return render_template('selection.html')
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
