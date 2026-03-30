import os
import time
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from flask import Flask, render_template, request, flash, redirect, url_for, session, Response, stream_with_context
from werkzeug.utils import secure_filename

# Local imports
from core.parser import parse_resume
from core.matcher import calculate_match_score
from core.keywords import ROLE_KEYWORDS

def process_resume_worker(args):
    file_path, filename, keywords = args
    resume_text = parse_resume(file_path)
    score, matched, experience = calculate_match_score(resume_text, keywords)
    if score > 0:
        return {
            'filename': filename,
            'score': score,
            'matched': matched,
            'total_keywords': len(keywords),
            'experience': experience
        }
    return None

app = Flask(__name__)
app.secret_key = 'super_secret_ai_resume_key'

# Configuration for resume uploads (if directly uploading, though plan requested scanning a folder)
# We will support both: reading from a specified local directory path, and direct uploads.
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def standardize_filename(filename):
    """
    Standardizes a filename to Title Case with underscores.
    Example: 'john_doe-resume.pdf' -> 'John_Doe_Resume.pdf'
    """
    if '.' not in filename:
        return filename
    
    parts = filename.rsplit('.', 1)
    name = parts[0]
    ext = parts[1].lower()
    
    # Replace common separators with space
    name = name.replace('_', ' ').replace('-', ' ')
    # Switch to Title Case
    name = ' '.join(word.capitalize() for word in name.split())
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    return f"{name}.{ext}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        role = request.form.get('role')
        
        if action == 'scan_folder':
            filter_type = request.form.get('filter_type', 'role')
            role = request.form.get('role')
            
            if filter_type == 'role':
                if not role or role not in ROLE_KEYWORDS:
                    flash("Please select a valid target role.", "error")
                    return redirect(url_for('index'))
            else:
                custom_skills = request.form.get('custom_skills', '')
                if not custom_skills.strip():
                    flash("Please enter at least one custom skill.", "error")
                    return redirect(url_for('index'))
            
            # Save parameters in session
            session['filter_type'] = filter_type
            session['role'] = role
            session['custom_skills'] = request.form.get('custom_skills', '')
            session['start_time'] = time.time()
            return redirect(url_for('results'))
            
        elif action == 'upload':
            files = request.files.getlist('resumes')
            folder_files = request.files.getlist('folder_resumes')
            
            # Combine both lists together natively
            all_files = files + folder_files
            
            # Check if any legitimate file structure was uploaded
            valid_files = [f for f in all_files if f and allowed_file(f.filename)]
            
            if not valid_files:
                flash("No valid files or folder selected.", "error")
                return redirect(url_for('index'))
                
            uploaded_count = 0
            for file in valid_files:
                base_name = file.filename.replace('\\', '/').split('/')[-1]
                standardized_name = standardize_filename(base_name)
                filename = secure_filename(standardized_name)
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_count += 1
            
            flash(f"Successfully uploaded {uploaded_count} file(s) locally. Head over to the Scan tab to evaluate them.", "success")
            return redirect(url_for('index'))

    # GET request
    roles = list(ROLE_KEYWORDS.keys())
    return render_template('index.html', roles=roles)

@app.route('/results')
def results():
    filter_type = session.get('filter_type', 'role')
    role_display = session.get('role') if filter_type == 'role' else "Custom Skillset"
    return render_template('results.html', role=role_display)

@app.route('/stream_results')
def stream_results():
    filter_type = session.get('filter_type', 'role')
    if filter_type == 'role':
        role = session.get('role')
        if not role or role not in ROLE_KEYWORDS:
            return Response("data: DONE\n\n", mimetype='text/event-stream')
        keywords = ROLE_KEYWORDS[role]
    else:
        custom_skills = session.get('custom_skills', '')
        keywords = [k.strip() for k in custom_skills.split(',') if k.strip()]

    folder_path = app.config['UPLOAD_FOLDER']
    if not os.path.isdir(folder_path) or not os.listdir(folder_path):
        return Response("data: DONE\n\n", mimetype='text/event-stream')

    valid_files = [f for f in os.listdir(folder_path) if allowed_file(f)]
    if not valid_files:
        return Response("data: DONE\n\n", mimetype='text/event-stream')

    args_list = [(os.path.join(folder_path, filename), filename, keywords) for filename in valid_files]
    
    start_time = session.get('start_time', time.time())

    def generate():
        executor = ProcessPoolExecutor(max_workers=os.cpu_count() or 4)
        futures = [executor.submit(process_resume_worker, arg) for arg in args_list]
        try:
            for future in as_completed(futures):
                res = future.result()
                if res:
                    yield f"data: {json.dumps(res)}\n\n"
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        time_taken = round(time.time() - start_time, 2)
        yield f"data: DONE|{time_taken}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
