import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from PIL.ExifTags import TAGS
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'civicconnect-ghaziabad-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///civicconnect.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# ============== DATABASE MODELS ==============
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    issues = db.relationship('Issue', backref='reporter', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # pothole, garbage, water, electricity, etc.
    locality_id = db.Column(db.Integer, nullable=False)
    locality_name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, assigned, resolved
    severity = db.Column(db.Integer, default=3)  # 1-5 scale
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='issue', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============== HELPER FUNCTIONS ==============
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_gps_from_image(filepath):
    """Extract GPS coordinates from EXIF data"""
    try:
        image = Image.open(filepath)
        exifdata = image.getexif()
        
        gps_ifd = {}
        for tag_id, tag_name in TAGS.items():
            if tag_name == "GPSInfo":
                if tag_id in exifdata:
                    gps_ifd = exifdata.get_ifd(tag_id)
                    break
        
        if gps_ifd:
            gps_latitude = gps_ifd.get(2)  # North
            gps_longitude = gps_ifd.get(4)  # East
            
            if gps_latitude and gps_longitude:
                lat = float(gps_latitude[0][0]) / float(gps_latitude[0][1])
                lng = float(gps_longitude[0][0]) / float(gps_longitude[0][1])
                return lat, lng
    except Exception as e:
        print(f"GPS extraction error: {e}")
    
    return None, None

def detect_locality(lat, lng):
    """Auto-detect locality based on GPS coordinates"""
    with open('localities.json', 'r') as f:
        localities = json.load(f)['localities']
    
    min_distance = float('inf')
    closest_locality = None
    
    for loc in localities:
        # Simple distance calculation
        distance = math.sqrt((loc['lat'] - lat)**2 + (loc['lng'] - lng)**2)
        if distance < min_distance:
            min_distance = distance
            closest_locality = loc
    
    if min_distance < 0.05:  # Within ~5km
        return closest_locality
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ============== ROUTES ==============
@app.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            return render_template('register.html', error='All fields required'), 400
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match'), 400
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists'), 400
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already exists'), 400
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid credentials'), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - view and report issues"""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    query = Issue.query
    
    if category_filter:
        query = query.filter_by(category=category_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    issues = query.order_by(Issue.created_at.desc()).paginate(page=page, per_page=10)
    
    with open('localities.json', 'r') as f:
        localities = json.load(f)['localities']
    
    user = User.query.get(session['user_id'])
    
    return render_template('dashboard.html', 
                          issues=issues, 
                          localities=localities,
                          user=user)

@app.route('/report-issue', methods=['GET', 'POST'])
@login_required
def report_issue():
    """Report a new civic issue"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        severity = request.form.get('severity', 3, type=int)
        locality_id = request.form.get('locality_id', type=int)
        
        with open('localities.json', 'r') as f:
            localities = {loc['id']: loc for loc in json.load(f)['localities']}
        
        locality = localities.get(locality_id)
        
        photo_url = None
        latitude, longitude = None, None
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = f"{session['user_id']}_{datetime.now().timestamp()}.jpg"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo_url = f"/static/uploads/{filename}"
                
                # Extract GPS and auto-detect locality
                lat, lng = extract_gps_from_image(filepath)
                if lat and lng:
                    latitude, longitude = lat, lng
                    detected_locality = detect_locality(lat, lng)
                    if detected_locality:
                        locality = detected_locality
                        locality_id = detected_locality['id']
        
        issue = Issue(
            title=title,
            description=description,
            category=category,
            locality_id=locality_id,
            locality_name=locality['name'] if locality else 'Unknown',
            latitude=latitude,
            longitude=longitude,
            photo_url=photo_url,
            severity=severity,
            reporter_id=session['user_id']
        )
        
        db.session.add(issue)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    
    with open('localities.json', 'r') as f:
        localities = json.load(f)['localities']
    
    return render_template('report_issue.html', localities=localities)

@app.route('/issue/<int:issue_id>')
def view_issue(issue_id):
    """View issue details"""
    issue = Issue.query.get_or_404(issue_id)
    reporter = User.query.get(issue.reporter_id)
    comments = Comment.query.filter_by(issue_id=issue_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('issue_detail.html', issue=issue, reporter=reporter, comments=comments)

@app.route('/api/issue/<int:issue_id>/comment', methods=['POST'])
@login_required
def add_comment(issue_id):
    """Add a comment to an issue"""
    issue = Issue.query.get_or_404(issue_id)
    text = request.form.get('comment_text', '').strip()
    
    if not text:
        return redirect(url_for('view_issue', issue_id=issue_id))
    
    comment = Comment(
        text=text,
        author_id=session['user_id'],
        issue_id=issue_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return redirect(url_for('view_issue', issue_id=issue_id))

@app.route('/hall-of-shame')
def hall_of_shame():
    """Hall of Shame - Worst RWA rankings"""
    with open('localities.json', 'r') as f:
        localities_data = json.load(f)['localities']
    
    # Calculate statistics per locality
    locality_stats = {}
    for loc in localities_data:
        issues = Issue.query.filter_by(locality_id=loc['id']).all()
        unresolved = [i for i in issues if i.status != 'resolved']
        avg_severity = sum(i.severity for i in issues) / len(issues) if issues else 0
        
        locality_stats[loc['id']] = {
            'name': loc['name'],
            'rwa_name': loc['rwa_name'],
            'rwa_contact': loc['rwa_contact'],
            'rwa_email': loc['rwa_email'],
            'total_issues': len(issues),
            'unresolved_issues': len(unresolved),
            'avg_severity': round(avg_severity, 1),
            'severity_score': loc['severity_score']
        }
    
    # Sort by most problematic
    ranked = sorted(
        locality_stats.values(),
        key=lambda x: (x['unresolved_issues'], x['avg_severity']),
        reverse=True
    )
    
    return render_template('hall_of_shame.html', rankings=ranked)

@app.route('/admin')
@admin_required
def admin():
    """Admin panel"""
    total_issues = Issue.query.count()
    total_users = User.query.count()
    pending_issues = Issue.query.filter_by(status='pending').count()
    resolved_issues = Issue.query.filter_by(status='resolved').count()
    
    # Filtering for admin table
    status_filter = request.args.get('status', '')
    query = Issue.query
    if status_filter == 'pending':
        query = query.filter(Issue.status != 'pending')  # Hide unresolved
    elif status_filter == 'assigned':
        query = query.filter(Issue.status != 'assigned')  # Hide in process
    elif status_filter == 'resolved':
        query = query.filter(Issue.status != 'resolved')  # Hide resolved

    filtered_issues = query.order_by(Issue.created_at.desc()).all()
    
    return render_template('admin.html',
                          total_issues=total_issues,
                          total_users=total_users,
                          pending_issues=pending_issues,
                          resolved_issues=resolved_issues,
                          issues=filtered_issues,
                          status_filter=status_filter)

@app.route('/api/issue/<int:issue_id>/upvote', methods=['POST'])
@login_required
def upvote_issue(issue_id):
    """Upvote an issue"""
    issue = Issue.query.get_or_404(issue_id)
    issue.upvotes += 1
    db.session.commit()
    return jsonify({'upvotes': issue.upvotes})

@app.route('/api/issue/<int:issue_id>/status', methods=['POST'])
@admin_required
def update_issue_status(issue_id):
    """Update issue status (admin only)"""
    issue = Issue.query.get_or_404(issue_id)
    new_status = request.json.get('status')
    
    if new_status in ['pending', 'assigned', 'resolved']:
        issue.status = new_status
        db.session.commit()
        return jsonify({'status': issue.status})
    
    return jsonify({'error': 'Invalid status'}), 400

# ============== ERROR HANDLERS ==============
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

# ============== INITIALIZATION ==============
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@civicconnect.in',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
