# pyre-ignore-all-errors
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, datetime, random, re
from urllib.parse import quote_plus, urlparse, parse_qs
import urllib.request
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_
from dotenv import load_dotenv
from google import genai
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-edulearn-secret')
# Initialize Gemini Client
try:
    gemini_client = genai.Client()
except Exception as e:
    print(f"Failed to initialize Gemini Client: {e}")
    gemini_client = None
# Use SQLite file under instance/ to align with Flask conventions
db_path = os.path.join(app.instance_path, 'edulearn_full.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------------- MODELS ----------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, instructor, pending_instructor, admin
    department = db.Column(db.String(100))
    verification_doc_url = db.Column(db.String(255))
    rejection_reason = db.Column(db.Text)
    xp = db.Column(db.Integer, default=0)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    badges = db.relationship('UserBadge', backref='user', lazy=True)

    def check_password(self, pw): return check_password_hash(self.password_hash, pw)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), default='fa-medal') # fontawesome icon class
    xp_bonus = db.Column(db.Integer, default=0)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    short_desc = db.Column(db.String(300), nullable=False)
    long_desc = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(db.String(200), default='https://images.unsplash.com/photo-1513258496099-48168024aec0?q=80&w=1200&auto=format&fit=crop')
    instructor = db.Column(db.String(100), default='EduLearn Team')
    lessons = db.relationship('Lesson', backref='course', cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='course', cascade="all, delete-orphan")
    discussions = db.relationship('Discussion', backref='course', cascade="all, delete-orphan")

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(250))
    position = db.Column(db.Integer, default=0)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    questions = db.relationship('Question', backref='quiz', cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct = db.Column(db.String(1), nullable=False)  # A/B/C/D

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)  # lessons completed
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='uix_favorite_user_course'),
    )

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    percent_off = db.Column(db.Integer, default=0)  # 0-100
    amount_off_cents = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer)
    uses = db.Column(db.Integer, default=0)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    timestamp_seconds = db.Column(db.Integer, default=0)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
class RefresherSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    videos = db.Column(db.Text) # JSON serialized list of video links
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.date.today, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Late

# Global config helper (simulated)
def get_attendance_threshold():
    return 75  # Default threshold 75%


@login_manager.user_loader
def load_user(uid): return db.session.get(User, int(uid))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def instructor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Instructor access required', 'danger')
            return redirect(url_for('login'))
        if current_user.role == 'pending_instructor':
            flash('Your instructor account is pending verification.', 'warning')
            return redirect(url_for('instructor_onboarding'))
        if current_user.role not in ['instructor','admin']:
            flash('Instructor access required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# -------- Helpers (no schema changes) --------
def price_for_course_cents(cid: int) -> int:
    """Simple tiered pricing based on course id. Returns price in cents."""
    tiers = [4900, 5900, 7900]
    return tiers[cid % len(tiers)]

def luhn_valid(number: str) -> bool:
    """Validate PAN using the Luhn algorithm."""
    digits = [int(ch) for ch in number if ch.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d = d * 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def compute_discount(price_cents: int, code: str):
    """Return (discount_cents, final_cents, coupon_obj_or_None) for a given price and coupon code."""
    if not code:
        return 0, price_cents, None
    cp = Coupon.query.filter(func.upper(Coupon.code) == code.upper(), Coupon.active == True).first()
    if not cp:
        return 0, price_cents, None
    now = datetime.datetime.utcnow()
    if cp.expires_at and cp.expires_at < now:
        return 0, price_cents, None
    if cp.max_uses and cp.uses >= cp.max_uses:
        return 0, price_cents, None
    discount = 0
    if cp.percent_off:
        discount += (price_cents * int(cp.percent_off)) // 100
    if cp.amount_off_cents:
        discount += int(cp.amount_off_cents)
    discount = max(0, min(discount, price_cents))
    final_cents = price_cents - discount
    return discount, final_cents, cp

def normalize_to_embed(url: str | None) -> str | None:
    if not url:
        return None
    u = url.strip()
    # already embed or playlist
    if '/embed/' in u or '/embed?' in u:
        return u
    try:
        parsed = urlparse(u)
    except Exception:
        return u
    host = (parsed.netloc or '').lower()
    path = parsed.path or ''
    qs = parse_qs(parsed.query or '')
    # youtu.be short link
    if 'youtu.be' in host and path:
        vid = path.strip('/').split('/')[0]
        if vid:
            return f'https://www.youtube.com/embed/{vid}'
    # watch URL
    if 'youtube.com' in host and 'watch' in path:
        vid = qs.get('v', [None])[0]
        if vid:
            return f'https://www.youtube.com/embed/{vid}'
    # shorts URL
    if 'youtube.com' in host and '/shorts/' in path:
        parts = path.split('/shorts/')
        if len(parts) > 1 and parts[1]:
            vid = parts[1].split('/')[0]
            return f'https://www.youtube.com/embed/{vid}'
    return u

def award_xp(user_id, amount):
    """Safely award XP to a user."""
    u = db.session.get(User, user_id)
    if u:
        u.xp = (u.xp or 0) + amount
        db.session.commit()
        # logic to check for badges could go here
        return True
    return False

def check_and_award_badge(user_id, badge_name):
    """Award a badge if not already owned."""
    u = db.session.get(User, user_id)
    b = Badge.query.filter_by(name=badge_name).first()
    if u and b:
        if not UserBadge.query.filter_by(user_id=user_id, badge_id=b.id).first():
            db.session.add(UserBadge(user_id=user_id, badge_id=b.id))
            if b.xp_bonus:
                u.xp = (u.xp or 0) + b.xp_bonus
            db.session.commit()
            flash(f'🏆 Badge Unlocked: {b.name}!', 'success')

def generate_refresher(course_id, wrong_topics):
    if not gemini_client:
        return "AI suggestions are currently unavailable.", "[]"
    
    course = db.session.get(Course, course_id)
    c_title = course.title if course else "the course"
    prompt = f"The student failed a quiz in the course '{c_title}'. They struggled with the following questions/topics:\n{wrong_topics}\nProvide a brief, encouraging refresher summary (2-3 paragraphs max) explaining these concepts simply. Do not use Markdown formatting in the text, except for bolding key terms. Also suggest 1 or 2 specific concepts they should search for on YouTube."
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text, "[]"
    except Exception as e:
        import traceback
        with open('debug_gemini.txt', 'w') as f:
            f.write(traceback.format_exc())
        print(f"Gemini error generating refresher: {e}")
        return "We couldn't generate a personalized refresher at this time. Please review the previous lessons.", "[]"


# ---------------------- THEME MANAGEMENT ----------------------
THEME_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'theme_config.json')

def get_current_theme():
    try:
        if os.path.exists(THEME_CONFIG_FILE):
            with open(THEME_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('active_theme', 'ocean')
    except Exception as e:
        print(f"Error reading theme: {e}")
    return 'ocean'

def set_current_theme(theme_name):
    try:
        with open(THEME_CONFIG_FILE, 'w') as f:
            json.dump({'active_theme': theme_name}, f)
        return True
    except Exception as e:
        print(f"Error saving theme: {e}")
        return False

@app.context_processor
def inject_theme():
    return dict(active_color_theme=get_current_theme())


# ---------------------- ROUTES ----------------------
@app.route('/')
def index():
    courses = Course.query.order_by(Course.id.desc()).all()
    course_prices = {c.id: f"{price_for_course_cents(c.id)/100:.2f}" for c in courses}
    # avg ratings map
    avg_rows = db.session.query(Review.course_id, func.avg(Review.rating), func.count(Review.id)).group_by(Review.course_id).all()
    avg_ratings = {cid: {'avg': float(avg or 0), 'count': int(cnt)} for cid, avg, cnt in avg_rows}
    # enrollment counts per course for trending and instructor aggregates
    enroll_rows = db.session.query(Enrollment.course_id, func.count(Enrollment.id)).group_by(Enrollment.course_id).all()
    enroll_counts = {cid: int(cnt) for cid, cnt in enroll_rows}
    # Trending: top 6 by enrollments, fallback to recent
    sorted_ids = [cid for cid, _ in sorted(enroll_counts.items(), key=lambda x: x[1], reverse=True)]
    top_ids = sorted_ids[:6]
    trending_courses = []
    if top_ids:
        map_tc = {c.id: c for c in Course.query.filter(Course.id.in_(top_ids)).all()}
        trending_courses = [map_tc[i] for i in top_ids if i in map_tc]
    if len(trending_courses) < 6:
        needed = 6 - len(trending_courses)
        fill = Course.query.filter(~Course.id.in_([c.id for c in trending_courses])).order_by(Course.id.desc()).limit(needed).all()
        trending_courses += fill
    # New & noteworthy
    new_courses = Course.query.order_by(Course.id.desc()).limit(6).all()
    # Continue learning for logged-in users (last 3 enrollments)
    continue_learning = []
    if current_user.is_authenticated:
        recents = Enrollment.query.filter_by(student_id=current_user.id).order_by(Enrollment.created_at.desc()).limit(3).all()
        for e in recents:
            course = db.session.get(Course, e.course_id)
            if not course:
                continue
            total = len(course.lessons) or 1
            pct = int((e.progress/total)*100) if total else 0
            continue_learning.append({'course': course, 'pct': pct})
    # Featured instructors (by total enrollments across their courses)
    instr_counts = {}
    for c in courses:
        instr_counts[c.instructor] = instr_counts.get(c.instructor, 0) + int(enroll_counts.get(c.id, 0))
    top_instructors = sorted(instr_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    featured_instructors = []
    for name, cnt in top_instructors:
        sample = next((c for c in courses if c.instructor == name), None)
        featured_instructors.append({'name': name, 'enrolls': int(cnt), 'sample': sample})
    # Sitewide ratings and featured testimonials
    site_avg_row = db.session.query(func.avg(Review.rating), func.count(Review.id)).first()
    site_avg_rating = float(site_avg_row[0] or 0)
    site_review_count = int(site_avg_row[1] or 0)
    home_featured_reviews = []
    for r in Review.query.order_by(Review.rating.desc(), Review.created_at.desc()).limit(3).all():
        u = db.session.get(User, r.user_id)
        home_featured_reviews.append({'rating': int(r.rating), 'comment': r.comment or '', 'user': (u.name if u else 'Learner')})
    # Popular queries (static suggestions)
    popular_queries = ['Python', 'JavaScript', 'Data Science', 'Machine Learning', 'Design', 'DevOps']
    # Active promo coupon (nearest expiry)
    promo_coupon = Coupon.query.filter(Coupon.active == True).order_by(Coupon.expires_at.asc().nulls_last()).first()
    fav_ids = set()
    if current_user.is_authenticated:
        fav_ids = {f.course_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}
    return render_template(
        'index.html',
        courses=courses,
        trending_courses=trending_courses,
        new_courses=new_courses,
        continue_learning=continue_learning,
        featured_instructors=featured_instructors,
        site_avg_rating=site_avg_rating,
        site_review_count=site_review_count,
        home_featured_reviews=home_featured_reviews,
        promo_coupon=promo_coupon,
        popular_queries=popular_queries,
        course_prices=course_prices,
        avg_ratings=avg_ratings,
        fav_ids=fav_ids
    )

@app.route('/admin/theme', methods=['GET', 'POST'])
@admin_required
def admin_theme():
    themes = [
        {'id': 'ocean', 'name': 'Ocean Blue', 'colors': ['#0f172a', '#3b82f6']},
        {'id': 'emerald', 'name': 'Emerald Green', 'colors': ['#022c22', '#10b981']},
        {'id': 'crimson', 'name': 'Crimson Red', 'colors': ['#1a0505', '#f43f5e']},
        {'id': 'sunset', 'name': 'Sunset Orange', 'colors': ['#2a1200', '#f97316']}
    ]
    if request.method == 'POST':
        selected = request.form.get('theme')
        if selected in [t['id'] for t in themes]:
            set_current_theme(selected)
            flash('Site theme updated successfully!', 'success')
            return redirect(url_for('admin_theme'))
        else:
            flash('Invalid theme selected.', 'danger')
            
    current = get_current_theme()
    return render_template('admin_theme.html', themes=themes, current_theme=current)

@app.route('/about')
def about():
    team = [
        {'name': 'Aryan Sanjay Kalmegh', 'shine': True},
        {'name': 'Rahul Kumar Tiwari', 'shine': True},
        {'name': 'Sumit S Khandare', 'shine': True},
        {'name': 'Vansh Asati', 'shine': False},
        {'name': 'Shivam Deshmukh', 'shine': False},
        {'name': 'Snehal Mohod', 'shine': False},
    ]
    return render_template('about.html', team=team)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']; email = request.form['email']; pw = request.form['password']
        role = request.form.get('role', 'student')
        # harden: only allow student or instructor during self-registration
        if role not in ['student','instructor']:
            role = 'student'
            
        if role == 'instructor':
            if email.lower().endswith('.edu') or email.lower().endswith('.ac.in'):
                role = 'instructor'
            else:
                role = 'pending_instructor'

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger'); return redirect(url_for('register'))
        u = User(name=name, email=email, password_hash=generate_password_hash(pw), role=role)
        db.session.add(u); db.session.commit()
        if role == 'pending_instructor':
            flash('Registration successful. Your instructor account is pending verification.', 'info')
        else:
            flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']; pw = request.form['password']
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(pw):
            login_user(u); flash('Welcome back!', 'success'); return redirect(url_for('admin_users') if u.role == 'admin' else url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user(); flash('Logged out.', 'info'); return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    enrolls = Enrollment.query.filter_by(student_id=current_user.id).all()
    # derive progress percentage from lessons completed vs total lessons
    data = []
    for e in enrolls:
        course = db.session.get(Course, e.course_id)
        total = len(course.lessons) or 1
        pct = int((e.progress/total)*100) if total else 0
        data.append((course, pct))
    return render_template('dashboard.html', enrolls=data)

@app.route('/course/<int:cid>')
def course_detail(cid):
    c = db.get_or_404(Course, cid)
    enrolled = False
    if current_user.is_authenticated:
        enrolled = Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first() is not None
    lessons = Lesson.query.filter_by(course_id=c.id).order_by(Lesson.position.asc()).all()
    quizzes = Quiz.query.filter_by(course_id=c.id).all()
    posts = Discussion.query.filter_by(course_id=c.id).order_by(Discussion.created_at.desc()).all()
    # reviews
    reviews = Review.query.filter_by(course_id=c.id).order_by(Review.created_at.desc()).all()
    avg_row = db.session.query(func.avg(Review.rating), func.count(Review.id)).filter(Review.course_id==c.id).first()
    avg_rating = float(avg_row[0] or 0)
    review_count = int(avg_row[1] or 0)
    # rating breakdown and featured reviews
    breakdown_rows = db.session.query(Review.rating, func.count(Review.id)).filter(Review.course_id==c.id).group_by(Review.rating).all()
    rating_breakdown = {i: 0 for i in [1,2,3,4,5]}
    for r_val, cnt in breakdown_rows:
        try:
            rating_breakdown[int(r_val)] = int(cnt)
        except Exception:
            pass
    featured_reviews = Review.query.filter_by(course_id=c.id).order_by(Review.rating.desc(), Review.created_at.desc()).limit(3).all()
    user_fav = False
    if current_user.is_authenticated:
        user_fav = Favorite.query.filter_by(user_id=current_user.id, course_id=c.id).first() is not None
    # track progress position for checkmarks in curriculum
    progress_pos = 0
    if current_user.is_authenticated:
        e_obj = Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first()
        if e_obj:
            try:
                progress_pos = int(e_obj.progress or 0)
            except Exception:
                progress_pos = 0
    # enrollment count for social proof
    enroll_count = Enrollment.query.filter_by(course_id=c.id).count()
    # preview video from the first lesson that has a video_url
    preview_url = None
    for l in lessons:
        if l.video_url:
            preview_url = l.video_url
            break
    # related courses (prefer same instructor, fallback to recent others)
    related_courses = Course.query.filter(Course.instructor == c.instructor, Course.id != c.id).order_by(Course.id.desc()).limit(6).all()
    if len(related_courses) < 6:
        more = Course.query.filter(Course.id != c.id, Course.instructor != c.instructor).order_by(Course.id.desc()).limit(6 - len(related_courses)).all()
        related_courses += more
    price_cents = price_for_course_cents(c.id)
    price_str = f"{price_cents/100:.2f}"
    related_prices = {rc.id: f"{price_for_course_cents(rc.id)/100:.2f}" for rc in related_courses}
    canonical_url = url_for('course_detail', cid=c.id, _external=True)
    return render_template('course_detail.html', course=c, lessons=lessons, quizzes=quizzes, enrolled=enrolled, posts=posts, reviews=reviews, avg_rating=avg_rating, review_count=review_count, rating_breakdown=rating_breakdown, featured_reviews=featured_reviews, user_fav=user_fav, price_cents=price_cents, price_str=price_str, enroll_count=enroll_count, preview_url=preview_url, related_courses=related_courses, related_prices=related_prices, progress_pos=progress_pos, canonical_url=canonical_url)

@app.route('/enroll/<int:cid>', methods=['POST'])
@login_required
def enroll(cid):
    if price_for_course_cents(cid) > 0 and current_user.role != 'admin':
        flash('Direct enrollment is disabled for paid courses. Please check out.', 'danger')
        return redirect(url_for('checkout', cid=cid))
    if Enrollment.query.filter_by(student_id=current_user.id, course_id=cid).first():
        flash('Already enrolled.', 'info'); return redirect(url_for('course_detail', cid=cid))
    db.session.add(Enrollment(student_id=current_user.id, course_id=cid)); db.session.commit()
    flash('Enrollment successful!', 'success'); return redirect(url_for('course_detail', cid=cid))

@app.route('/lesson/<int:lid>')
@login_required
def lesson_view(lid):
    l = db.get_or_404(Lesson, lid); c = db.session.get(Course, l.course_id)
    lessons = Lesson.query.filter_by(course_id=c.id).order_by(Lesson.position.asc()).all()
    # update progress
    e = Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first()
    if e:
        # Gamification: First time reaching this position?
        if l.position > e.progress:
            award_xp(current_user.id, 10) # +10 XP per new lesson
            check_and_award_badge(current_user.id, 'First Step')

        e.progress = max(e.progress, l.position); db.session.commit()
        
        # Check for Course Completion
        total_lessons = len(lessons)
        if e.progress >= total_lessons:
             check_and_award_badge(current_user.id, 'Dedicated Learner')

    # Night Owl Check (between 12AM and 4AM)
    hour = datetime.datetime.utcnow().hour
    if 0 <= hour < 4:
        check_and_award_badge(current_user.id, 'Night Owl')

    # Fetch user notes for this lesson
    my_notes = Note.query.filter_by(user_id=current_user.id, lesson_id=l.id).order_by(Note.timestamp_seconds.asc()).all()
    
    return render_template('lesson.html', lesson=l, course=c, lessons=lessons, notes=my_notes)

@app.route('/api/note/save', methods=['POST'])
@login_required
def save_note():
    data = request.get_json()
    lid = data.get('lesson_id')
    ts = int(data.get('timestamp', 0))
    text = data.get('text', '').strip()
    if not text or not lid:
        return {'status': 'error', 'msg': 'Missing data'}, 400
    
    # Optional: verify enrollment
    n = Note(user_id=current_user.id, lesson_id=lid, timestamp_seconds=ts, text=text)
    db.session.add(n)
    db.session.commit()
    return {'status': 'ok', 'id': n.id, 'short_ts': str(datetime.timedelta(seconds=ts))}

@app.route('/api/note/delete/<int:nid>', methods=['POST'])
@login_required
def delete_note(nid):
    n = db.session.get(Note, nid)
    if not n or n.user_id != current_user.id:
        return {'status': 'error', 'msg': 'Denied'}, 403
    db.session.delete(n)
    db.session.commit()
    return {'status': 'ok'}

@app.route('/lesson/<int:lid>/mock-test')
@login_required
def mock_test(lid):
    lesson = db.get_or_404(Lesson, lid)
    course = db.session.get(Course, lesson.course_id)
    
    # check enrollment
    if not Enrollment.query.filter_by(student_id=current_user.id, course_id=course.id).first() and current_user.role != 'admin':
        flash("You must be enrolled to take mock tests.", "danger")
        return redirect(url_for('course_detail', cid=course.id))

    if not gemini_client:
        flash("AI Mock Test generation is currently unavailable.", "danger")
        return redirect(url_for('lesson_view', lid=lid))
        
    prompt = f"Generate exactly 3 multiple choice questions based on the following lesson text to test the student's understanding. Format the strictly as a JSON array where each element has: 'text' (the question string), 'option_a', 'option_b', 'option_c', 'option_d', and 'correct' (the correct letter A, B, C, or D).\n\nLESSON TEXT:\n{lesson.content}"
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # safely extract JSON from response
        raw_text = response.text
        start_idx = raw_text.find('[')
        end_idx = raw_text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            json_str = raw_text[start_idx:end_idx+1]
            questions = json.loads(json_str)
        else:
            raise ValueError("No JSON array returned by AI")
            
        return render_template('mock_test.html', lesson=lesson, course=course, questions=questions)
    except Exception as e:
        print(f"Gemini error generating mock test: {e}")
        flash("We couldn't generate a mock test right now. Please try again later.", "warning")
        return redirect(url_for('lesson_view', lid=lid))

@app.route('/api/flashcards/<int:cid>')
@login_required
def get_flashcards(cid):
    if not Enrollment.query.filter_by(student_id=current_user.id, course_id=cid).first() and current_user.role != 'admin':
        return {'status': 'error', 'msg': 'Not enrolled'}, 403
    # Auto-generate flashcards from quiz questions
    # In a real app, these might be manually created or AI-generated
    # Here we map Quiz Questions -> Flashcards (Front: Question Text, Back: Correct Option Text)
    c = db.get_or_404(Course, cid)
    cards = []
    quizzes = Quiz.query.filter_by(course_id=cid).all()
    for q in quizzes:
        for ques in q.questions:
            # simple logic: Front = Question, Back = Correct Answer Text
            correct_text = "Unknown"
            if ques.correct == 'A': correct_text = ques.option_a
            elif ques.correct == 'B': correct_text = ques.option_b
            elif ques.correct == 'C': correct_text = ques.option_c
            elif ques.correct == 'D': correct_text = ques.option_d
            
            cards.append({
                'id': ques.id,
                'front': ques.text,
                'back': correct_text,
                'lesson': q.title
            })
    return {'course': c.title, 'cards': cards}


@app.route('/quiz/<int:qid>')
@login_required
def quiz_view(qid):
    q = db.get_or_404(Quiz, qid)
    return render_template('quiz.html', quiz=q)

@app.route('/quiz/<int:qid>/submit', methods=['POST'])
@login_required
def quiz_submit(qid):
    q = db.get_or_404(Quiz, qid)
    score = 0; total = len(q.questions)
    wrong_q_texts = []
    
    for ques in q.questions:
        ans = request.form.get(f'question_{ques.id}', '')
        if ans == ques.correct: 
            score += 1
        else:
            wrong_q_texts.append(ques.text)
            
    passed = score >= (total / 2) if total > 0 else True
    
    attempt = QuizAttempt(user_id=current_user.id, quiz_id=qid, score=score, total=total, passed=passed)
    db.session.add(attempt)
    db.session.commit()
    
    # Gamification
    if score == total and total > 0:
        award_xp(current_user.id, 100) # +100 XP for perfect score
        check_and_award_badge(current_user.id, 'Quiz Master')
        flash(f'Perfect Score! You earned 100 XP.', 'success')
    elif passed:
        award_xp(current_user.id, 20) # +20 XP for passing
        flash(f'You passed! Scored {score}/{total}', 'success')
    else:
        # Generate Refresher
        refresher_text, dummy_videos = generate_refresher(q.course_id, " | ".join(wrong_q_texts))
        sugg = RefresherSuggestion(attempt_id=attempt.id, content=refresher_text, videos=dummy_videos)
        db.session.add(sugg)
        db.session.commit()
        flash(f'You scored {score}/{total}. Don\'t worry, we\'ve created a personalized refresher for you!', 'warning')
        return redirect(url_for('refresher_view', rid=sugg.id))
    
    return redirect(url_for('course_detail', cid=q.course_id))

@app.route('/refresher/<int:rid>')
@login_required
def refresher_view(rid):
    sugg = db.get_or_404(RefresherSuggestion, rid)
    attempt = db.session.get(QuizAttempt, sugg.attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)
    quiz = db.session.get(Quiz, attempt.quiz_id)
    course = db.session.get(Course, quiz.course_id)
    
    # Retry generation if it failed previously (e.g. stale API key in auto-reload)
    if "We couldn't generate a personalized refresher" in sugg.content:
        # Re-determine wrong questions
        wrong_q_texts = []
        for ques in quiz.questions:
            ans = request.form.get(f'question_{ques.id}', '') # this form data is lost, actually we can't accurately know what was wrong! 
            # Oh wait, we didn't save the exact wrong answers in the DB except in the original submit.
            # Let's just pass all questions as a generic refresher to fix this view state
            wrong_q_texts.append(ques.text)
        
        new_text, _ = generate_refresher(course.id, " | ".join(wrong_q_texts))
        if "We couldn't generate" not in new_text:
            sugg.content = new_text
            db.session.commit()
            
    return render_template('refresher.html', suggestion=sugg, attempt=attempt, quiz=quiz, course=course)

@app.route('/checkout/<int:cid>', methods=['GET','POST'])
@login_required
def checkout(cid):
    """Demo checkout that looks real and enrolls the user upon successful payment validation (Luhn)."""
    c = db.get_or_404(Course, cid)
    price_cents = price_for_course_cents(c.id)
    code = (request.args.get('code','') or '').strip()
    discount_cents, final_cents, cp = compute_discount(price_cents, code)
    price_str = f"{price_cents/100:.2f}"
    final_str = f"{final_cents/100:.2f}"
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        number = (request.form.get('number','') or '').replace(' ', '')
        exp = request.form.get('exp','').strip()
        cvv = (request.form.get('cvv','') or '').strip()
        coupon_in = (request.form.get('coupon','') or '').strip()
        d_cents, f_cents, used_cp = compute_discount(price_cents, coupon_in)
        if coupon_in and not used_cp:
            flash('Invalid or expired coupon.', 'danger')
        if not name or not number or not exp or not cvv or not luhn_valid(number) or len(cvv) < 3:
            flash('Payment failed: invalid card details. Try test card 4242 4242 4242 4242.', 'danger')
            return redirect(url_for('checkout', cid=cid))
        # Enroll user if not already
        if not Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first():
            db.session.add(Enrollment(student_id=current_user.id, course_id=c.id))
            db.session.commit()
        if used_cp:
            used_cp.uses = (used_cp.uses or 0) + 1
            db.session.commit()
        flash('Payment successful. You are enrolled!', 'success')
        return redirect(url_for('course_detail', cid=c.id))
    return render_template('checkout.html', course=c, price_cents=price_cents, price_str=price_str, discount_cents=discount_cents, final_cents=final_cents, final_str=final_str, coupon_code=code)

@app.route('/course/<int:cid>/discuss', methods=['POST'])
@login_required
def discuss(cid):
    txt = request.form.get('content', '').strip()
    if txt:
        db.session.add(Discussion(course_id=cid, author=current_user.name, content=txt)); db.session.commit()
        flash('Posted!', 'success')
    return redirect(url_for('course_detail', cid=cid))

# ---------------------- SEARCH & FAVORITES ----------------------
@app.route('/search')
def search():
    q = (request.args.get('q','') or '').strip()
    if not q:
        return redirect(url_for('index'))
    like = f"%{q}%"
    courses = Course.query.filter(
        or_(Course.title.ilike(like), Course.short_desc.ilike(like), Course.long_desc.ilike(like))
    ).order_by(Course.id.desc()).all()
    course_prices = {c.id: f"{price_for_course_cents(c.id)/100:.2f}" for c in courses}
    avg_rows = db.session.query(Review.course_id, func.avg(Review.rating), func.count(Review.id)).group_by(Review.course_id).all()
    avg_ratings = {cid: {'avg': float(avg or 0), 'count': int(cnt)} for cid, avg, cnt in avg_rows}
    fav_ids = set()
    if current_user.is_authenticated:
        fav_ids = {f.course_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}
    return render_template('search.html', q=q, courses=courses, course_prices=course_prices, avg_ratings=avg_ratings, fav_ids=fav_ids)

@app.route('/favorite/<int:cid>/toggle', methods=['POST'])
@login_required
def favorite_toggle(cid):
    c = db.get_or_404(Course, cid)
    f = Favorite.query.filter_by(user_id=current_user.id, course_id=c.id).first()
    if f:
        db.session.delete(f)
        flash('Removed from wishlist.', 'info')
    else:
        db.session.add(Favorite(user_id=current_user.id, course_id=c.id))
        flash('Added to wishlist.', 'success')
    db.session.commit()
    return redirect(request.referrer or url_for('course_detail', cid=cid))

@app.route('/wishlist')
@login_required
def wishlist():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    ids = [f.course_id for f in favs]
    courses = Course.query.filter(Course.id.in_(ids)).all() if ids else []
    course_prices = {c.id: f"{price_for_course_cents(c.id)/100:.2f}" for c in courses}
    return render_template('wishlist.html', courses=courses, course_prices=course_prices, fav_ids=set(ids))

@app.route('/leaderboard')
def leaderboard():
    # Top 20 users by XP
    users = User.query.filter(User.role=='student').order_by(User.xp.desc()).limit(20).all()
    return render_template('leaderboard.html', users=users)

# ---------------------- REVIEWS ----------------------
@app.route('/course/<int:cid>/review', methods=['POST'])
@login_required
def add_review(cid):
    c = db.get_or_404(Course, cid)
    # require enrollment to review
    if not Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first():
        flash('Enroll in the course to leave a review.', 'danger')
        return redirect(url_for('course_detail', cid=cid))
    rating = int(request.form.get('rating','0') or 0)
    comment = (request.form.get('comment','') or '').strip()
    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5.', 'danger')
        return redirect(url_for('course_detail', cid=cid))
    existing = Review.query.filter_by(course_id=c.id, user_id=current_user.id).first()
    if existing:
        existing.rating = rating
        existing.comment = comment
    else:
        db.session.add(Review(course_id=c.id, user_id=current_user.id, rating=rating, comment=comment))
    db.session.commit()
    flash('Thanks for your review!', 'success')
    return redirect(url_for('course_detail', cid=cid))

# ---------------------- CART ----------------------
def _get_cart():
    return set(session.get('cart', []))

def _save_cart(s):
    session['cart'] = list(s)

@app.route('/cart')
@login_required
def cart_view():
    ids = list(_get_cart())
    courses = Course.query.filter(Course.id.in_(ids)).all() if ids else []
    prices = {c.id: price_for_course_cents(c.id) for c in courses}
    total_cents = sum(prices.values())
    code = (request.args.get('code','') or '').strip()
    discount_cents, final_cents, cp = compute_discount(total_cents, code)
    return render_template('cart.html', courses=courses, prices=prices, total_cents=total_cents, discount_cents=discount_cents, final_cents=final_cents, coupon_code=code)

@app.route('/cart/add/<int:cid>', methods=['POST'])
@login_required
def cart_add(cid):
    db.get_or_404(Course, cid)
    s = _get_cart(); s.add(cid); _save_cart(s)
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart/remove/<int:cid>', methods=['POST'])
@login_required
def cart_remove(cid):
    s = _get_cart(); s.discard(cid); _save_cart(s)
    flash('Removed from cart.', 'info')
    return redirect(request.referrer or url_for('cart_view'))

@app.route('/cart/checkout', methods=['POST'])
@login_required
def cart_checkout():
    ids = list(_get_cart())
    if not ids:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('cart_view'))
    name = request.form.get('name','').strip()
    number = (request.form.get('number','') or '').replace(' ', '')
    exp = request.form.get('exp','').strip()
    cvv = (request.form.get('cvv','') or '').strip()
    coupon_in = (request.form.get('coupon','') or '').strip()
    courses = Course.query.filter(Course.id.in_(ids)).all()
    total_cents = sum(price_for_course_cents(c.id) for c in courses)
    d_cents, f_cents, used_cp = compute_discount(total_cents, coupon_in)
    if coupon_in and not used_cp:
        flash('Invalid or expired coupon.', 'danger')
        return redirect(url_for('cart_view'))
    if not name or not number or not exp or not cvv or not luhn_valid(number) or len(cvv) < 3:
        flash('Payment failed: invalid card details.', 'danger')
        return redirect(url_for('cart_view'))
    # enroll into all
    for c in courses:
        if not Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first():
            db.session.add(Enrollment(student_id=current_user.id, course_id=c.id))
    db.session.commit()
    if used_cp:
        used_cp.uses = (used_cp.uses or 0) + 1
        db.session.commit()
    _save_cart(set())
    flash('Payment successful. You are enrolled in your courses!', 'success')
    return redirect(url_for('dashboard'))

# ---------------------- CERTIFICATE ----------------------
@app.route('/certificate/<int:cid>')
@login_required
def certificate(cid):
    c = db.get_or_404(Course, cid)
    e = Enrollment.query.filter_by(student_id=current_user.id, course_id=c.id).first()
    if not e:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('course_detail', cid=cid))
    total = len(Lesson.query.filter_by(course_id=c.id).all()) or 1
    pct = int((e.progress/total)*100)
    if pct < 100:
        flash('Complete the course to unlock the certificate.', 'danger')
        return redirect(url_for('course_detail', cid=cid))
    cert_id = f"CERT-{cid}-{current_user.id}-{datetime.datetime.utcnow().strftime('%Y%m%d')}"
    return render_template('certificate.html', course=c, cert_id=cert_id, student=current_user, date=datetime.datetime.utcnow())

# ---------------------- INSTRUCTOR ANALYTICS ----------------------
@app.route('/instructor/onboarding', methods=['GET', 'POST'])
@login_required
def instructor_onboarding():
    if current_user.role != 'pending_instructor':
        flash('You do not need to onboard as an instructor.', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        department = request.form.get('department', '').strip()
        doc_file = request.files.get('document_file')
        
        if not department or not doc_file or not doc_file.filename:
            flash('Please provide both department and a verification document.', 'danger')
            return redirect(url_for('instructor_onboarding'))
            
        if not allowed_file(doc_file.filename):
            flash('Invalid file type.', 'danger')
            return redirect(url_for('instructor_onboarding'))
            
        filename = secure_filename(doc_file.filename)
        # Ensure unique filename
        filename = f"user_{current_user.id}_{int(datetime.datetime.utcnow().timestamp())}_{filename}"
        doc_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        current_user.department = department
        current_user.verification_doc_url = url_for('static', filename='uploads/' + filename)
        current_user.rejection_reason = None # Clear any previous rejection reason
        db.session.commit()
        
        flash('Documents submitted successfully! An admin will review your application soon.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('instructor_onboarding.html')

@app.route('/instructor/analytics')
@login_required
@instructor_required
def instructor_analytics():
    my = Course.query.filter_by(instructor=current_user.name).all()
    ids = [c.id for c in my]
    counts = {cid: Enrollment.query.filter_by(course_id=cid).count() for cid in ids}
    revenue_cents = sum(counts.get(c.id,0) * price_for_course_cents(c.id) for c in my)
    return render_template('instructor_analytics.html', courses=my, counts=counts, revenue_cents=revenue_cents)

# ---------------------- INSTRUCTOR ----------------------
@app.route('/instructor/courses')
@login_required
@instructor_required
def instructor_courses():
    my = Course.query.filter_by(instructor=current_user.name).order_by(Course.id.desc()).all()
    return render_template('instructor_courses.html', courses=my)

@app.route('/instructor/courses/new', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_course_new():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        short_desc = request.form.get('short_desc','').strip()
        long_desc = request.form.get('long_desc','').strip()
        thumb_url = (request.form.get('thumbnail','') or '').strip()
        thumb_file = request.files.get('thumbnail_file')
        
        if not title or not short_desc or not long_desc:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('instructor_course_new', back=request.args.get('back')))
            
        kwargs = dict(title=title, short_desc=short_desc, long_desc=long_desc, instructor=current_user.name)
        
        if thumb_file and thumb_file.filename:
            if not allowed_file(thumb_file.filename):
                flash('Invalid file type.', 'danger')
                return redirect(request.args.get('back') or url_for('instructor_courses'))
            filename = secure_filename(thumb_file.filename)
            thumb_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            kwargs['thumbnail'] = url_for('static', filename='uploads/' + filename)
        elif thumb_url:
            kwargs['thumbnail'] = thumb_url
            
        c = Course(**kwargs)
        db.session.add(c); db.session.commit()
        flash('Course created.', 'success')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    return render_template('instructor_course_form.html', course=None)

@app.route('/instructor/courses/<int:cid>/edit', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_course_edit(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized to edit this course.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        c.title = request.form.get('title','').strip()
        c.short_desc = request.form.get('short_desc','').strip()
        c.long_desc = request.form.get('long_desc','').strip()
        thumb_url = (request.form.get('thumbnail','') or '').strip()
        thumb_file = request.files.get('thumbnail_file')

        if thumb_file and thumb_file.filename:
            if not allowed_file(thumb_file.filename):
                flash('Invalid file type.', 'danger')
                return redirect(request.args.get('back') or url_for('instructor_courses'))
            filename = secure_filename(thumb_file.filename)
            thumb_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            c.thumbnail = url_for('static', filename='uploads/' + filename)
        elif thumb_url:
            c.thumbnail = thumb_url

        if not c.title or not c.short_desc or not c.long_desc:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('instructor_course_edit', cid=cid, back=request.args.get('back')))
        db.session.commit(); flash('Course updated.', 'success')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    return render_template('instructor_course_form.html', course=c)

@app.route('/instructor/courses/<int:cid>/delete', methods=['POST'])
@login_required
@instructor_required
def instructor_course_delete(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized to delete this course.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    # remove enrollments referencing this course to avoid FK constraint issues
    Enrollment.query.filter_by(course_id=c.id).delete()
    db.session.delete(c)
    db.session.commit()
    flash('Course deleted.', 'success')
    back = request.args.get('back')
    return redirect(back or url_for('instructor_courses'))

@app.route('/instructor/courses/<int:cid>/lessons')
@login_required
@instructor_required
def instructor_lessons(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    lessons = Lesson.query.filter_by(course_id=c.id).order_by(Lesson.position.asc()).all()
    return render_template('instructor_lessons.html', course=c, lessons=lessons)

@app.route('/instructor/courses/<int:cid>/lessons/new', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_lesson_new(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        content = request.form.get('content','').strip()
        video_url = (request.form.get('video_url','') or '').strip()
        position = int(request.form.get('position','0') or 0)
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('instructor_lesson_new', cid=cid, back=request.args.get('back')))
        db.session.add(Lesson(course_id=c.id, title=title, content=content, video_url=normalize_to_embed(video_url) or None, position=position))
        db.session.commit(); flash('Lesson created.', 'success')
        return redirect(url_for('instructor_lessons', cid=cid, back=request.args.get('back')))
    return render_template('instructor_lesson_form.html', course=c, lesson=None)

@app.route('/instructor/lessons/<int:lid>/edit', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_lesson_edit(lid):
    l = db.get_or_404(Lesson, lid)
    c = db.get_or_404(Course, l.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        l.title = request.form.get('title','').strip()
        l.content = request.form.get('content','').strip()
        l.video_url = normalize_to_embed((request.form.get('video_url','') or '').strip()) or None
        l.position = int(request.form.get('position','0') or 0)
        if not l.title or not l.content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('instructor_lesson_edit', lid=lid, back=request.args.get('back')))
        db.session.commit(); flash('Lesson updated.', 'success')
        return redirect(url_for('instructor_lessons', cid=c.id, back=request.args.get('back')))
    return render_template('instructor_lesson_form.html', course=c, lesson=l)

@app.route('/instructor/lessons/<int:lid>/delete', methods=['POST'])
@login_required
@instructor_required
def instructor_lesson_delete(lid):
    l = db.get_or_404(Lesson, lid)
    c = db.get_or_404(Course, l.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    db.session.delete(l); db.session.commit(); flash('Lesson deleted.', 'success')
    return redirect(url_for('instructor_lessons', cid=c.id, back=request.args.get('back')))

# ---------------------- INSTRUCTOR QUIZZES ----------------------
@app.route('/instructor/courses/<int:cid>/quizzes')
@login_required
@instructor_required
def instructor_quizzes(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    quizzes = Quiz.query.filter_by(course_id=c.id).all()
    return render_template('instructor_quizzes.html', course=c, quizzes=quizzes)

@app.route('/instructor/courses/<int:cid>/quizzes/new', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_quiz_new(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('instructor_quiz_new', cid=cid, back=request.args.get('back')))
        qz = Quiz(course_id=c.id, title=title)
        db.session.add(qz); db.session.commit()
        flash('Quiz created.', 'success')
        return redirect(url_for('instructor_quizzes', cid=c.id, back=request.args.get('back')))
    return render_template('instructor_quiz_form.html', course=c, quiz=None)

@app.route('/instructor/quizzes/<int:qid>/edit', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_quiz_edit(qid):
    qz = db.get_or_404(Quiz, qid)
    c = db.get_or_404(Course, qz.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        qz.title = request.form.get('title','').strip()
        if not qz.title:
            flash('Title is required.', 'danger')
            return redirect(url_for('instructor_quiz_edit', qid=qid, back=request.args.get('back')))
        db.session.commit(); flash('Quiz updated.', 'success')
        return redirect(url_for('instructor_quizzes', cid=c.id, back=request.args.get('back')))
    return render_template('instructor_quiz_form.html', course=c, quiz=qz)

@app.route('/instructor/quizzes/<int:qid>/delete', methods=['POST'])
@login_required
@instructor_required
def instructor_quiz_delete(qid):
    qz = db.get_or_404(Quiz, qid)
    c = db.get_or_404(Course, qz.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    db.session.delete(qz); db.session.commit(); flash('Quiz deleted.', 'success')
    return redirect(url_for('instructor_quizzes', cid=c.id, back=request.args.get('back')))

@app.route('/instructor/quizzes/<int:qid>/questions')
@login_required
@instructor_required
def instructor_questions(qid):
    qz = db.get_or_404(Quiz, qid)
    c = db.get_or_404(Course, qz.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    return render_template('instructor_questions.html', course=c, quiz=qz, questions=qz.questions)

@app.route('/instructor/quizzes/<int:qid>/questions/new', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_question_new(qid):
    qz = db.get_or_404(Quiz, qid)
    c = db.get_or_404(Course, qz.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        text = request.form.get('text','').strip()
        option_a = request.form.get('option_a','').strip()
        option_b = request.form.get('option_b','').strip()
        option_c = request.form.get('option_c','').strip()
        option_d = request.form.get('option_d','').strip()
        correct = request.form.get('correct','').strip().upper()
        if not text or not option_a or not option_b or not option_c or not option_d or correct not in ['A','B','C','D']:
            flash('All fields are required and correct answer must be A/B/C/D.', 'danger')
            return redirect(url_for('instructor_question_new', qid=qid, back=request.args.get('back')))
        db.session.add(Question(quiz_id=qz.id, text=text, option_a=option_a, option_b=option_b, option_c=option_c, option_d=option_d, correct=correct))
        db.session.commit(); flash('Question created.', 'success')
        return redirect(url_for('instructor_questions', qid=qid, back=request.args.get('back')))
    return render_template('instructor_question_form.html', course=c, quiz=qz, question=None)

@app.route('/instructor/questions/<int:quesid>/edit', methods=['GET','POST'])
@login_required
@instructor_required
def instructor_question_edit(quesid):
    qs = db.get_or_404(Question, quesid)
    qz = db.get_or_404(Quiz, qs.quiz_id)
    c = db.get_or_404(Course, qz.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    if request.method == 'POST':
        qs.text = request.form.get('text','').strip()
        qs.option_a = request.form.get('option_a','').strip()
        qs.option_b = request.form.get('option_b','').strip()
        qs.option_c = request.form.get('option_c','').strip()
        qs.option_d = request.form.get('option_d','').strip()
        qs.correct = request.form.get('correct','').strip().upper()
        if not qs.text or not qs.option_a or not qs.option_b or not qs.option_c or not qs.option_d or qs.correct not in ['A','B','C','D']:
            flash('All fields are required and correct answer must be A/B/C/D.', 'danger')
            return redirect(url_for('instructor_question_edit', quesid=quesid, back=request.args.get('back')))
        db.session.commit(); flash('Question updated.', 'success')
        return redirect(url_for('instructor_questions', qid=qz.id, back=request.args.get('back')))
    return render_template('instructor_question_form.html', course=c, quiz=qz, question=qs)

@app.route('/instructor/questions/<int:quesid>/delete', methods=['POST'])
@login_required
@instructor_required
def instructor_question_delete(quesid):
    qs = db.get_or_404(Question, quesid)
    qz = db.get_or_404(Quiz, qs.quiz_id)
    c = db.get_or_404(Course, qz.course_id)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        back = request.args.get('back')
        return redirect(back or url_for('instructor_courses'))
    db.session.delete(qs); db.session.commit(); flash('Question deleted.', 'success')
    return redirect(url_for('instructor_questions', qid=qz.id, back=request.args.get('back')))

# ---------------------- ADMIN ----------------------
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    courses = Course.query.order_by(Course.id.desc()).all()
    return render_template('admin_courses.html', courses=courses)

@app.route('/admin/users/<int:uid>/role', methods=['POST'])
@login_required
@admin_required
def admin_change_role(uid):
    u = db.get_or_404(User, uid)
    new_role = request.form.get('role', '').strip()
    if new_role in ['student','instructor','admin']:
        u.role = new_role
        db.session.commit()
        flash('Role updated.', 'success')
    else:
        flash('Invalid role.', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:uid>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(uid):
    u = db.get_or_404(User, uid)
    if u.email == 'admin@edulearn.com':
        flash('Cannot delete the default admin.', 'danger')
        return redirect(url_for('admin_users'))
    # remove related dependencies first to avoid FK issues
    Enrollment.query.filter_by(student_id=u.id).delete()
    Review.query.filter_by(user_id=u.id).delete()
    Favorite.query.filter_by(user_id=u.id).delete()
    Note.query.filter_by(user_id=u.id).delete()
    QuizAttempt.query.filter_by(user_id=u.id).delete()
    db.session.delete(u)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/approvals')
@login_required
@admin_required
def admin_approvals():
    pending_users = User.query.filter_by(role='pending_instructor').filter(User.verification_doc_url.isnot(None)).all()
    return render_template('admin_approvals.html', pending_users=pending_users)

@app.route('/admin/approvals/<int:uid>/approve', methods=['POST'])
@login_required
@admin_required
def admin_approve_instructor(uid):
    u = db.get_or_404(User, uid)
    if u.role == 'pending_instructor':
        u.role = 'instructor'
        u.rejection_reason = None
        db.session.commit()
        flash(f'Instructor {u.name} approved.', 'success')
    else:
        flash('User is not a pending instructor.', 'danger')
    return redirect(url_for('admin_approvals'))

@app.route('/admin/approvals/<int:uid>/reject', methods=['POST'])
@login_required
@admin_required
def admin_reject_instructor(uid):
    u = db.get_or_404(User, uid)
    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Rejection reason is required.', 'danger')
        return redirect(url_for('admin_approvals'))
        
    if u.role == 'pending_instructor':
        # Keep them as pending_instructor but clear their documents and set rejection reason
        u.verification_doc_url = None
        u.rejection_reason = reason
        db.session.commit()
        flash(f'Instructor {u.name} rejected.', 'success')
    else:
        flash('User is not a pending instructor.', 'danger')
        
    return redirect(url_for('admin_approvals'))

# ---------------------- CLI ----------------------
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

# ---------------------- CLI ----------------------
@app.cli.command('initdb')
def initdb():
    db.create_all(); print('DB initialized.')

@app.cli.command('seed')
def seed():
    db.create_all()
    # admin
    if not User.query.filter_by(email='admin@edulearn.com').first():
        admin = User(name='Admin', email='admin@edulearn.com', password_hash=generate_password_hash('admin123'), role='admin')
        db.session.add(admin); db.session.commit()
    # users
    if not User.query.filter_by(email='instructor@edulearn.com').first():
        inst = User(name='Lead Instructor', email='instructor@edulearn.com', password_hash=generate_password_hash('password'), role='instructor')
        stu = User(name='Student One', email='student@edulearn.com', password_hash=generate_password_hash('password'), role='student')
        db.session.add_all([inst, stu]); db.session.commit()
    # course + 10 lessons + 10 quizzes (5 Q each)
    if Course.query.count() == 0:
        c = Course(title='Full‑Stack Web Development', short_desc='Learn HTML, CSS, JS, Flask, and SQL.',
                   long_desc='A hands‑on program covering frontend and backend. Includes projects and quizzes.',
                   instructor='Jane Doe')
        db.session.add(c); db.session.commit()
        for i in range(1, 11):
            db.session.add(Lesson(course_id=c.id, title=f'Lesson {i}: Module {i}', position=i,
                                  content=f'<p>Rich content for module {i} with code snippets and examples.</p>',
                                  video_url='https://player.vimeo.com/video/357274789'))
        # 10 quizzes
        for qi in range(1, 11):
            quiz = Quiz(course_id=c.id, title=f'Quiz {qi}: Module {qi} Check')
            db.session.add(quiz); db.session.commit()
            for i in range(1, 6):
                correct = random.choice(['A','B','C','D'])
                db.session.add(Question(quiz_id=quiz.id, text=f'Q{i}. Concept check for module {qi}.',
                                        option_a='Option A', option_b='Option B', option_c='Option C', option_d='Option D', correct=correct))
        db.session.commit()
    # Ensure at least 10 varied demo courses exist
    sample_courses = [
        ("Python for Beginners", "Start coding in Python from scratch.", "A gentle introduction to Python covering syntax, data structures, and projects.", "Alice Kim"),
        ("Data Science Bootcamp", "End-to-end DS workflow.", "Learn data wrangling, visualization, and modeling with real datasets.", "Dr. Ravi Singh"),
        ("Machine Learning A–Z", "Supervised and unsupervised.", "Hands-on ML with scikit-learn, covering regression, classification, and clustering.", "Maria Gomez"),
        ("Cybersecurity Fundamentals", "Protect systems and data.", "Threats, vulnerabilities, and best practices for securing applications.", "Ethan Park"),
        ("Cloud Computing with AWS", "Deploy in the cloud.", "Core AWS services, IAM, EC2, S3, and serverless basics.", "Noah Williams"),
        ("UI/UX Design Masterclass", "Design delightful products.", "User research, wireframing, prototyping, and usability testing.", "Sara Lee"),
        ("Digital Marketing 101", "Grow your audience.", "SEO, SEM, social media strategy, and email marketing fundamentals.", "David Chen"),
        ("Financial Analysis with Excel", "Make data-driven decisions.", "Modeling, dashboards, and scenario analysis with Excel.", "Priya Patel"),
        ("English Communication Skills", "Speak with confidence.", "Improve speaking, listening, and presentation skills.", "John Miller"),
        ("Personal Productivity", "Get more done.", "Time management, focus techniques, and workflow systems.", "Emma Davis"),
    ]
    thumbs = [
        'https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1551281044-8d8d4e89f2f4?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1510511459019-5dda7724fd87?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1557800636-894a64c1696f?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1543286386-2e659306cd6c?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?q=80&w=1200&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=1200&auto=format&fit=crop',
    ]
    cur = Course.query.count()
    if cur < 10:
        to_add = 10 - cur
        for i in range(to_add):
            title, sd, ld, instr = sample_courses[i % len(sample_courses)]
            thumb = thumbs[i % len(thumbs)]
            db.session.add(Course(title=title, short_desc=sd, long_desc=ld, instructor=instr, thumbnail=thumb))
        db.session.commit()
    # Seed coupons
    if not Coupon.query.filter_by(code='SAVE10').first():
        db.session.add(Coupon(code='SAVE10', percent_off=10, active=True, expires_at=datetime.datetime.utcnow()+datetime.timedelta(days=365)))
    if not Coupon.query.filter_by(code='HALF').first():
        db.session.add(Coupon(code='HALF', percent_off=50, active=True))
    if not Coupon.query.filter_by(code='WELCOME5').first():
        db.session.add(Coupon(code='WELCOME5', amount_off_cents=500, active=True))
    
    # Seed Badges
    badges = [
        ('First Step', 'Completed your first lesson', 'fa-shoe-prints', 50),
        ('Quiz Master', 'Scored 100% on a quiz', 'fa-brain', 100),
        ('Night Owl', 'Studied after midnight', 'fa-moon', 50),
        ('Dedicated Learner', 'Completed a full course', 'fa-graduation-cap', 500)
    ]
    for name, desc, icon, bonus in badges:
        if not Badge.query.filter_by(name=name).first():
            db.session.add(Badge(name=name, description=desc, icon=icon, xp_bonus=bonus))

    db.session.commit()
    print('Seeded data.')
    # Enrich after seeding so newly created courses get detailed content
    try:
        enrich_courses()
    except Exception as e:
        print('Enrich after seed skipped:', e)

@app.cli.command('enrich')
def enrich_cli():
    """Run content enrichment idempotently for all courses."""
    with app.app_context():
        try:
            enrich_courses()
            print('Enrichment complete.')
        except Exception as e:
            print('Enrichment failed:', e)

# ---------------------- CONTENT ENRICHMENT ----------------------
def enrich_courses():
    """Idempotently enrich courses with detailed descriptions, lessons, and baseline quizzes.
    - Extends short descriptions into multi-section long descriptions.
    - Ensures each course has at least a target number of lessons with rich HTML content.
    - Ensures at least 10 quizzes with sample questions if fewer exist (idempotent add-only).
    The routine is safe to re-run: it only updates when content is too short or missing.
    """
    DEFAULT_VIDEO = 'https://player.vimeo.com/video/123456789'
    GENERIC_DEFAULT_THUMB = 'https://images.unsplash.com/photo-1513258496099-48168024aec0?q=80&w=1200&auto=format&fit=crop'
    DATASCI_DEFAULT_THUMB = 'https://images.unsplash.com/photo-1556157382-4b8c5d0c7851?q=80&w=1200&auto=format&fit=crop'

    # Load list of popular YouTube channel IDs per category for lesson video embeds.
    # Each channel ID should be a standard YouTube channel ID (starts with 'UC').
    # We embed the channel's uploads playlist via https://www.youtube.com/embed/videoseries?list=UU<channel_id_without_UC>
    def load_video_channels():
        path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'video_channels.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}

    video_channels = load_video_channels()

    def embed_from_channel_id(ch_id: str) -> str | None:
        if not ch_id:
            return None
        # Allow passing a direct embed URL too
        if ch_id.startswith('http://') or ch_id.startswith('https://'):
            return ch_id
        # Convert channel ID to uploads playlist embed
        if ch_id.startswith('UC') and len(ch_id) > 2:
            return f'https://www.youtube.com/embed/videoseries?list=UU{ch_id[2:]}'
        return None

    # moved normalize_to_embed to global scope

    def youtube_search_embed(query: str) -> str:
        q = quote_plus(query.strip())
        # Search results playlist embed
        return f'https://www.youtube.com/embed?listType=search&list={q}'

    def load_video_topic_map():
        path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'video_topics_map.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # normalize keys to lowercase for matching
                    return {k.lower(): v for k, v in data.items()}
        except Exception:
            pass
        return {}

    topic_map = load_video_topic_map()

    # Curated intro video mapping by course category (first lesson + preview)
    def load_curated_intro_map():
        path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'video_curated_intro.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # normalize keys to lowercase
                    return {str(k).lower(): v for k, v in data.items()}
        except Exception:
            pass
        return {}

    curated_intro_map = load_curated_intro_map()

    # Built-in safe defaults (edit via JSON file to customize)
    DEFAULT_CURATED_INTRO = {
        # Python: Learn Python – Full Course for Beginners (freeCodeCamp)
        'python': 'https://www.youtube.com/watch?v=rfscVS0vtbw',
        # Cybersecurity: Cyber Security Full Course for Beginner
        'security': 'https://www.youtube.com/watch?v=U_P23SqJaDc',
        # General/CS foundations: CrashCourse CS #1 – Early Computing
        'general': 'https://www.youtube.com/watch?v=O5nskjZ_GoI',
    }

    def curated_intro_for(cat_key: str) -> str | None:
        ck = (cat_key or '').lower()
        url = curated_intro_map.get(ck) or DEFAULT_CURATED_INTRO.get(ck)
        return normalize_to_embed(url) if url else None

    # Simple JSON cache for dynamic search/API results to avoid re-querying repeatedly
    def load_video_cache():
        path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'video_cache.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data, path
        except Exception:
            pass
        return {}, path

    def save_video_cache(cache: dict, path: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass

    video_cache, cache_path = load_video_cache()
    cache_dirty = False

    def yt_api_key() -> str | None:
        k = os.environ.get('YOUTUBE_API_KEY') or app.config.get('YOUTUBE_API_KEY')
        return k.strip() if isinstance(k, str) and k.strip() else None

    def yt_api_search_best_video(query: str) -> str | None:
        key = yt_api_key()
        if not key:
            return None
        try:
            q = quote_plus(query.strip())
            url = (
                "https://www.googleapis.com/youtube/v3/search?"
                f"part=snippet&maxResults=1&type=video&safeSearch=moderate&videoEmbeddable=true&relevanceLanguage=en&q={q}&key={key}"
            )
            with urllib.request.urlopen(url, timeout=10) as resp:
                body = resp.read()
            data = json.loads(body.decode('utf-8'))
            items = data.get('items') or []
            if not items:
                return None
            vid = (((items[0] or {}).get('id') or {}).get('videoId'))
            if not vid:
                return None
            return f'https://www.youtube.com/embed/{vid}'
        except Exception:
            return None

    def video_for(cat_key: str, index: int) -> str:
        # choose channel list by category or fallback to default/popular
        chans = video_channels.get(cat_key) or video_channels.get('default') or []
        if not chans:
            return DEFAULT_VIDEO
        pick = chans[index % len(chans)]
        url = embed_from_channel_id(pick)
        return url or DEFAULT_VIDEO

    def topic_from_title(title: str) -> str:
        if not title:
            return ''
        m = re.match(r"^\s*Lesson\s*\d+\s*:\s*(.+)$", title, flags=re.IGNORECASE)
        return m.group(1) if m else title

    def video_for_topic(cat_key: str, topic: str, course_title: str) -> str:
        nonlocal cache_dirty
        key_variants = [
            f"{cat_key}::{topic}".lower(),
            topic.lower(),
        ]
        # 1) explicit mapping
        for kv in key_variants:
            if kv in topic_map:
                result = normalize_to_embed(topic_map[kv]) or DEFAULT_VIDEO
                print(f"  [VIDEO_DEBUG] topic_map HIT: '{kv}' => {result}")
                return result
        # 2) cached API/search results
        query = f"{topic} {course_title} tutorial"
        cached = video_cache.get(query.lower())
        if cached:
            result = normalize_to_embed(cached) or DEFAULT_VIDEO
            print(f"  [VIDEO_DEBUG] cache HIT: '{query.lower()}' => {result}")
            return result
        # 3) YouTube Data API (if key provided)
        api_embed = yt_api_search_best_video(query)
        if api_embed:
            video_cache[query.lower()] = api_embed
            cache_dirty = True
            print(f"  [VIDEO_DEBUG] YT API: '{query}' => {api_embed}")
            return api_embed
        # 4) dynamic search embed
        se = youtube_search_embed(query)
        if se:
            video_cache[query.lower()] = se
            cache_dirty = True
            print(f"  [VIDEO_DEBUG] search embed: '{query}' => {se}")
            return se
        # 5) fallback to channel playlist
        result = video_for(cat_key, 0)
        print(f"  [VIDEO_DEBUG] channel fallback: {result}")
        return result

    # -------- Topic-aligned Quiz Generation --------
    def load_quiz_topic_bank():
        path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'quiz_topics_map.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {k.lower(): v for k, v in data.items()}
        except Exception:
            pass
        return {}

    quiz_topic_bank = load_quiz_topic_bank()

    def _mcq(text, A, B, C, D, correct='A'):
        return {
            'text': text,
            'option_a': A,
            'option_b': B,
            'option_c': C,
            'option_d': D,
            'correct': correct
        }

    def _cat_label(cat_key: str) -> str:
        labels = {
            'fullstack': 'full‑stack web development',
            'python': 'Python programming',
            'datasci': 'data science',
            'ml': 'machine learning',
            'security': 'cybersecurity',
            'cloud': 'cloud computing',
            'uiux': 'UI/UX design',
            'marketing': 'digital marketing',
            'finance': 'financial analysis',
            'english': 'communication skills',
            'productivity': 'personal productivity',
            'general': 'technology'
        }
        return labels.get(cat_key, 'technology')

    def _heuristic_questions(cat_key: str, topic: str, tpl_obj: dict) -> list:
        tl = (topic or '').lower()
        # Python-focused heuristics
        if cat_key == 'python':
            if 'syntax' in tl or 'repl' in tl:
                return [
                    _mcq('What does REPL stand for?', 'Read–Eval–Print Loop', 'Run–Execute–Program Loop', 'Read–Execute–Program List', 'Runtime–Error–Print Log'),
                    _mcq("Which is valid Python to print 'Hello'?", "print('Hello')", "echo 'Hello'", "console.log('Hello')", "printf('Hello')"),
                    _mcq('Which is NOT a valid Python identifier?', '2var', '_value', 'value2', 'value_2'),
                    _mcq('What indicates a code block in Python?', 'Indentation', 'Braces {}', 'Begin/End keywords', 'Semicolons'),
                    _mcq('What prompt is shown in the interactive Python shell?', '>>>', '$', '#', 'py>')
                ]
            if 'variable' in tl or 'data type' in tl or 'types' in tl:
                return [
                    _mcq('Which built-in type in Python is mutable?', 'list', 'tuple', 'str', 'int'),
                    _mcq('Which collection disallows duplicate keys?', 'dict', 'list', 'set', 'tuple'),
                    _mcq('Which expression creates a dictionary?', "{'a': 1}", "['a', 1]", "('a', 1)", '{a:1, a:2}'),
                    _mcq('Which function returns the type of x?', 'type(x)', 'cast(x)', 'classof(x)', 'dtype(x)'),
                    _mcq("Which converts the string '42' to an int?", "int('42')", "str(42)", "float('42')", "toint('42')")
                ]
            if 'control flow' in tl or 'loop' in tl or 'condition' in tl:
                return [
                    _mcq('Which keyword closes an if/elif chain?', 'else', 'end', 'fi', 'endif'),
                    _mcq('Which statement exits the current loop?', 'break', 'exit', 'stop', 'quit'),
                    _mcq('Which statement skips to the next iteration?', 'continue', 'skip', 'pass', 'next'),
                    _mcq('Which function commonly produces a sequence of integers in for-loops?', 'range', 'seq', 'series', 'enumerate'),
                    _mcq('Which operator is used for conditional expressions (ternary)?', 'x if cond else y', 'cond ? x : y', 'if (cond) x; else y', 'x when cond else y')
                ]
            if 'function' in tl:
                return [
                    _mcq('How do you define a function?', 'def name(...):', 'function name(...)', 'fn name {...}', 'define name():'),
                    _mcq('Where are default argument values evaluated?', 'At function definition time', 'At each call', 'Only on first call', 'At interpreter startup'),
                    _mcq('What ends a function and returns a value?', 'return', 'yield', 'break', 'stop'),
                    _mcq('What is the first parameter of instance methods by convention?', 'self', 'this', 'me', 'obj'),
                    _mcq('Which creates an anonymous function?', 'lambda x: x+1', 'fn(x) => x+1', 'def(x){x+1}', 'function(x){return x+1;}')
                ]
            if 'data structure' in tl or 'list' in tl or 'dict' in tl or 'set' in tl:
                return [
                    _mcq('Which structure automatically removes duplicates?', 'set', 'list', 'tuple', 'dict'),
                    _mcq('Which is a valid list slice?', 'nums[1:4]', 'nums(1..4)', 'slice(nums,1,4)', 'nums[1..4]'),
                    _mcq('Which checks membership?', 'x in items', 'has(items, x)', 'items.contains(x)', 'items.has(x)'),
                    _mcq('Dictionary keys must be...', 'hashable', 'mutable', 'lists', 'duplicated'),
                    _mcq('Which copies a list shallowly?', 'nums[:]', 'copy(nums, deep=True)', 'deepcopy(nums)', 'nums.copy(deep=True)')
                ]
            if 'module' in tl or 'package' in tl:
                return [
                    _mcq('Which imports only sqrt from math?', 'from math import sqrt', 'import sqrt from math', 'use math.sqrt', 'get math.sqrt'),
                    _mcq('What file marks a package in older Python projects?', '__init__.py', 'package.json', 'setup.cfg', 'pyproject.toml'),
                    _mcq('Which installs dependencies from a file?', 'pip install -r requirements.txt', 'pip push requirements.txt', 'pip add requirements.txt', 'pip build -r requirements.txt'),
                    _mcq('How do you alias a module when importing?', 'import numpy as np', 'alias numpy = np', 'from numpy -> np', 'require numpy as np'),
                    _mcq('Which shows module attributes?', 'dir(module)', 'list(module)', 'show(module)', 'inspect(module)')
                ]
            if 'file' in tl or 'error' in tl:
                return [
                    _mcq('Which safely manages file resources?', "with open('a.txt') as f:", "open('a.txt'); close(f)", 'using(open) as f:', 'safeopen a.txt as f'),
                    _mcq('Which exception is raised when a file is missing?', 'FileNotFoundError', 'MissingFileError', 'IOClosedError', 'NameError'),
                    _mcq('Which opens a file for appending text?', "open('a.txt','a')", "open('a.txt','w+')", "open('a.txt','x')", "open('a.txt')"),
                    _mcq('Which clause runs regardless of exceptions?', 'finally', 'except', 'else', 'ensure'),
                    _mcq('Which logs the traceback of an exception?', 'import traceback; traceback.print_exc()', 'print(error.trace())', 'log(exception)', 'error.stack()')
                ]
            if 'oop' in tl or 'class' in tl:
                return [
                    _mcq('How do you define a class?', 'class Point:', 'defclass Point:', 'class Point(): end', 'create class Point'),
                    _mcq('What initializes new instances?', '__init__', '__start__', '__make__', '__create__'),
                    _mcq('What is method overriding?', 'Redefining a parent method in a subclass', 'Creating two methods with same name in one class', 'Writing methods without bodies', 'Defining methods outside classes'),
                    _mcq('What is polymorphism?', 'Using a unified interface for different types', 'Encrypting class methods', 'Compiling classes to bytecode', 'Auto-saving object state'),
                    _mcq('Which makes an attribute private by convention?', '_name', '__name__', 'private name', 'name!')
                ]
            if 'virtual' in tl or 'cli' in tl or 'environment' in tl:
                return [
                    _mcq('How do you create a virtual environment?', 'python -m venv .venv', 'pip create venv', 'python venv new', 'venv init'),
                    _mcq('How do you activate a venv on Windows (PowerShell)?', '. .venv/Script/Activate.ps1', 'source .venv/bin/activate', 'activate venv', 'pip activate'),
                    _mcq('Which freezes dependencies?', 'pip freeze > requirements.txt', 'pip save requirements.txt', 'pip lock', 'pip pin all'),
                    _mcq('Which parses CLI arguments?', 'argparse', 'requests', 'pytest', 'pickle'),
                    _mcq('Where should secrets like API keys live?', 'Environment variables/config', 'Hardcoded in code', 'In the README', 'Printed to logs')
                ]
            # default Python
            return [
                _mcq(f'Which is true about {topic}?', 'It is a core concept in Python', 'It is a network cable', 'It is a CPU brand', 'It is a file system'),
                _mcq('Which file runs a module as a script?', "if __name__ == '__main__':", 'main()', '__run__()', '__script__ == True'),
                _mcq('Which tool formats Python code?', 'black', 'docker', 'make', 'curl'),
                _mcq('Which test framework is common in Python?', 'pytest', 'mocha', 'junit', 'rspec'),
                _mcq('Which version manager creates isolated envs?', 'venv', 'git', 'ssh', 'scp')
            ]

        # Data science heuristics
        if cat_key == 'datasci':
            if 'pandas' in tl or 'numpy' in tl or 'data (' in tl:
                return [
                    _mcq('Which library provides DataFrame objects?', 'pandas', 'numpy', 'matplotlib', 'requests'),
                    _mcq('Which shows the first rows of a DataFrame df?', 'df.head()', 'df.start()', 'df.first()', 'df.show(5)'),
                    _mcq('Which handles missing values?', 'df.dropna()', 'df.drop()', 'df.remove()', 'df.clean()'),
                    _mcq('Which merges two DataFrames on a key?', 'pd.merge(a,b,on="id")', 'a.join(b, left_index=True)', 'concat(a,b,axis=1) only', 'union(a,b)'),
                    _mcq('Which reduces memory by type downcasting?', 'astype()', 'resize()', 'compress()', 'optimize()')
                ]
            if 'clean' in tl or 'wrangl' in tl:
                return [
                    _mcq('Which removes duplicate rows?', 'df.drop_duplicates()', 'df.unique()', 'df.dedup()', 'df.rmdup()'),
                    _mcq('Which fills missing values?', 'df.fillna(0)', 'df.fillmissing(0)', 'df.nafill(0)', 'df.replace_na(0)'),
                    _mcq('Which converts a column to datetime?', 'pd.to_datetime(df["col"])', 'df["col"].todate()', 'date(df["col"])', 'parse_date(df.col)'),
                    _mcq('Which reshapes long to wide?', 'pivot_table', 'melt', 'stack', 'explode'),
                    _mcq('Which standardizes column names?', 'df.columns = df.columns.str.lower()', 'df.columns.lower()', 'lower(df.columns)', 'setlower(df.columns)')
                ]
            if 'eda' in tl or 'visual' in tl:
                return [
                    _mcq('Which plot best shows distribution of a single variable?', 'Histogram', 'Scatter plot', 'Line chart', 'Heatmap'),
                    _mcq('Which library builds statistical plots quickly?', 'seaborn', 'opencv', 'plotly-dash', 'bokeh-server'),
                    _mcq('Which method shows correlation matrix?', 'df.corr()', 'df.covar()', 'df.correlation()', 'df.matrix()'),
                    _mcq('Which plot is best for time series trends?', 'Line chart', 'Pie chart', 'Strip plot', 'Violin plot'),
                    _mcq('What is a common EDA step?', 'Check missingness and outliers', 'Train a deep CNN', 'Deploy to Kubernetes', 'Tune a load balancer')
                ]
            if 'sql' in tl:
                return [
                    _mcq('Which SQL clause filters rows?', 'WHERE', 'GROUP BY', 'ORDER BY', 'SELECT'),
                    _mcq('Which aggregates by categories?', 'GROUP BY', 'FILTER BY', 'ROLLUP', 'PARTITION'),
                    _mcq('Which joins tables by key?', 'JOIN ... ON', 'MERGE TABLE', 'CONNECT BY', 'LINK ... USING'),
                    _mcq('Which returns distinct values?', 'SELECT DISTINCT', 'SELECT UNIQUE', 'SELECT ONLY', 'SELECT DIFFERENT'),
                    _mcq('Which sorts results?', 'ORDER BY', 'SORT BY', 'ARRANGE BY', 'ALIGN BY')
                ]
            if 'statistic' in tl:
                return [
                    _mcq('Which is robust to outliers?', 'Median', 'Mean', 'Variance', 'Sum'),
                    _mcq('What does a p-value represent?', 'Evidence against the null hypothesis', 'Probability the null is true', 'Type II error rate', 'Confidence level'),
                    _mcq('Which reduces variance by averaging models?', 'Bagging', 'Boosting', 'Regularization', 'Dropout'),
                    _mcq('Which standardizes features?', 'Z-score scaling', 'Min-max difference only', 'One-hot encoding', 'Clustering'),
                    _mcq('Which tests difference in means?', 't-test', 'chi-square test', 'ANOVA only', 'U-test only')
                ]
            if 'feature' in tl:
                return [
                    _mcq('Which technique transforms categorical variables?', 'One-hot encoding', 'L2 regularization', 'Standard scaling', 'Bagging'),
                    _mcq('Which handles skewed numeric features?', 'Log transform', 'Median absolute deviation', 'SMOTE', 'PCA'),
                    _mcq('Which reduces dimensionality?', 'PCA', 'k-means', 'Naive Bayes', 'Random Forest'),
                    _mcq('Which is a leakage risk?', 'Using target info in features', 'Using cross-validation', 'Shuffling data', 'Scaling features'),
                    _mcq('Which pipeline step prevents data leakage?', 'Fit transformers on train only', 'Fit on full data first', 'Normalize after test split', 'Impute using test stats')
                ]
            if 'intro to ml' in tl or ('ml' in tl and 'intro' in tl):
                return [
                    _mcq('Which splits data into train/test?', 'train_test_split', 'split_train_test', 'cv_split', 'kfold_split'),
                    _mcq('Which problem predicts a continuous value?', 'Regression', 'Classification', 'Clustering', 'Association rules'),
                    _mcq('Which is a common baseline model?', 'Linear/Logistic regression', 'GAN', 'Transformer', 'LSTM'),
                    _mcq('Which prevents overfitting?', 'Regularization', 'Data leakage', 'Using test data for training', 'Ignoring cross-validation'),
                    _mcq('Which metric is for classification?', 'F1-score', 'RMSE', 'MAE', 'R^2')
                ]
            if 'evaluation' in tl or 'validation' in tl:
                return [
                    _mcq('Which method estimates generalization error?', 'k-fold cross-validation', 'Training accuracy', 'Test on training data', 'Eyeballing charts'),
                    _mcq('Which matrix summarizes classification results?', 'Confusion matrix', 'Jacobian matrix', 'Hessian matrix', 'Gram matrix'),
                    _mcq('Which helps on imbalanced data?', 'Stratified sampling', 'Using accuracy only', 'Shuffling labels', 'Oversampling test set'),
                    _mcq('Which is a regression metric?', 'RMSE', 'AUC', 'F1-score', 'Log-loss'),
                    _mcq('Which curve shows trade-off between TPR and FPR?', 'ROC curve', 'Precision-recall curve only', 'Lift chart only', 'Pareto chart')
                ]
            # default DS
            catlab = _cat_label(cat_key)
            outs = (tpl_obj.get('outcomes') or ['Communicate insights clearly'])[0]
            tool = (tpl_obj.get('tools') or ['pandas'])[0]
            return [
                _mcq(f'Which statement about {topic} is true in {catlab}?', f'It is a core concept in {catlab}', 'It is a GPU brand', 'It is a cable type', 'It is a file format only'),
                _mcq('Which library/tool is most related here?', tool, 'SSH', 'Photoshop', 'PowerPoint'),
                _mcq('What is a good first step with a new dataset?', 'Inspect shape and missingness', 'Deploy models', 'Set up Kubernetes', 'Tweak learning rate'),
                _mcq('Which is NOT a best practice?', 'Ignoring data leakage', 'Versioning notebooks', 'Documenting assumptions', 'Validating metrics'),
                _mcq('Which learning outcome does this topic support?', outs, 'Reduce memory speed', 'Improve screen resolution', 'Change keyboard layout')
            ]

        # Machine learning heuristics
        if cat_key == 'ml':
            if 'supervised' in tl:
                return [
                    _mcq('What distinguishes supervised learning?', 'Labeled data', 'No labels', 'Only clustering', 'Only reinforcement signals'),
                    _mcq('Which is a regression algorithm?', 'Linear regression', 'Naive Bayes (multinomial)', 'k-means', 'Apriori'),
                    _mcq('Which is a classification metric?', 'AUC', 'RMSE', 'MAE', 'R^2'),
                    _mcq('Which split helps evaluate models?', 'Train/validation/test', 'Train/test only always', 'Use full data for training', 'Tune on test set'),
                    _mcq('Which reduces variance at risk of bias?', 'Underfitting', 'Overfitting', 'Cross-validation', 'Data augmentation')
                ]
            if 'cross-validation' in tl or 'metrics' in tl:
                return [
                    _mcq('Which method repeats training on folds?', 'k-fold cross-validation', 'Single holdout', 'Bootstrap only', 'Leave-one-out only'),
                    _mcq('Which metric measures regression error?', 'RMSE', 'AUC', 'F1', 'Precision'),
                    _mcq('Which uses a separate validation set?', 'Early stopping', 'Grid search on test', 'Bagging on test', 'Test-time training'),
                    _mcq('Which balances precision and recall?', 'F1-score', 'Accuracy', 'Support', 'Log-loss'),
                    _mcq('Which evaluation pitfall must be avoided?', 'Leakage between train and test', 'Stratification', 'Shuffling data', 'Scaling features')
                ]
            if 'feature' in tl or 'pipeline' in tl:
                return [
                    _mcq('Which step handles missing values?', 'Imputation', 'Regularization', 'Ensembling', 'Batching'),
                    _mcq('Which scales numeric features to zero mean and unit variance?', 'StandardScaler', 'RobustScaler centers by median only', 'MinMaxScaler to [-1,1]', 'Normalizer per sample only'),
                    _mcq('Which prevents leakage in pipelines?', 'Fit transformers on training folds only', 'Fit before splitting', 'Tune on test', 'Peek at labels during transform'),
                    _mcq('Which reduces dimensionality?', 'PCA', 'Random Forest', 'kNN', 'Naive Bayes'),
                    _mcq('Which combines transformations and model into one object?', 'Pipeline', 'Estimator', 'Transformer', 'FeatureUnion only')
                ]
            if 'svm' in tl or 'tree' in tl or 'ensemble' in tl:
                return [
                    _mcq('SVMs are best described as...', 'Margin-based classifiers', 'Generative models', 'Distance trees', 'Additive rules'),
                    _mcq('Decision trees tend to...', 'Overfit without pruning', 'Underfit always', 'Require feature scaling strictly', 'Only work on images'),
                    _mcq('Random Forests reduce variance by...', 'Averaging many trees', 'Using a single deep tree', 'Boosting weak learners sequentially', 'Dropping features at test time'),
                    _mcq('Gradient Boosting builds models...', 'Sequentially to correct errors', 'In parallel independently', 'By random search only', 'By PCA first always'),
                    _mcq('Which kernel is common in SVM?', 'RBF', 'Fourier', 'Sigmoid only', 'Laplacian only')
                ]
            if 'unsupervised' in tl or 'cluster' in tl or 'dimred' in tl:
                return [
                    _mcq('Unsupervised learning uses...', 'Unlabeled data', 'Labels only', 'Rewards only', 'Simulated data only'),
                    _mcq('Which is a clustering algorithm?', 'k-means', 'Logistic regression', 'SVM', 'Naive Bayes'),
                    _mcq('Which reduces dimensionality?', 'PCA', 'Lasso', 'Ridge', 'ElasticNet'),
                    _mcq('Which chooses k in k-means heuristically?', 'Elbow method', 'Grid on labels', 'Use test AUC', 'Bagging folds'),
                    _mcq('Which embedding preserves local structure?', 't-SNE', 'Linear regression', 'kNN', 'Random Forest')
                ]
            if 'overfitting' in tl or 'regularization' in tl:
                return [
                    _mcq('Which penalty shrinks coefficients toward zero?', 'L2 (Ridge)', 'Dropout', 'Bagging', 'Batch Norm'),
                    _mcq('Which detects overfitting during training?', 'Gap between train and val error', 'Low bias', 'High bias only', 'More data'),
                    _mcq('Which technique combats overfitting?', 'Early stopping', 'Data leakage', 'Testing on train', 'Using more epochs indiscriminately'),
                    _mcq('Which increases bias but reduces variance?', 'Stronger regularization', 'Bagging', 'Stacking', 'Feature engineering'),
                    _mcq('Which is a hyperparameter often tuned?', 'Regularization strength', 'Loss gradient', 'Label entropy', 'Sample IDs')
                ]
            if 'explain' in tl:
                return [
                    _mcq('Which method explains feature impact locally?', 'SHAP', 'Dropout', 'Adam', 'NMS'),
                    _mcq('What does feature importance indicate?', 'Relative contribution to predictions', 'Training speed', 'Memory use', 'Disk size'),
                    _mcq('Which improves interpretability?', 'Simpler models when possible', 'More layers always', 'Less validation', 'More leakage'),
                    _mcq('Which plot shows partial dependence?', 'PDP', 'ROC', 'PRC', 'Confusion matrix'),
                    _mcq('Which checks fairness issues?', 'Bias and variance across groups', 'Train on test set', 'Remove cross-validation', 'Ignore metrics')
                ]
            # default ML
            catlab = _cat_label(cat_key)
            outs = (tpl_obj.get('outcomes') or ['Train and evaluate ML models'])[0]
            tool = (tpl_obj.get('tools') or ['scikit-learn'])[0]
            return [
                _mcq(f'Which describes {topic} in {catlab}?', f'A core method in {catlab}', 'A hardware connector', 'An OS kernel', 'A file extension'),
                _mcq('Which library is most relevant?', tool, 'OpenSSL', 'React', 'Excel'),
                _mcq('Which prevents evaluation bias?', 'Stratified splits', 'Peeking at test', 'Tuning on test', 'Ignoring class imbalance'),
                _mcq('Which is NOT recommended?', 'Using leaked features', 'Record keeping of experiments', 'Versioning data', 'Checking assumptions'),
                _mcq('Mastering this topic helps you...', outs, 'Change monitor color depth', 'Replace a network card', 'Resize disk partitions')
            ]

        # Generic fallback
        catlab = _cat_label(cat_key)
        outs = (tpl_obj.get('outcomes') or ['Apply concepts to real projects'])[0]
        tool = (tpl_obj.get('tools') or ['Git'])[0]
        return [
            _mcq(f'Which statement about {topic} is most accurate?', f'It is a key concept in {catlab}', 'It is a type of cable', 'It is a CPU brand', 'It is a file format only'),
            _mcq('Which tool is commonly used with this topic?', tool, 'Calculator', 'Clipboard', 'Screensaver'),
            _mcq('Which practice helps you learn this topic?', 'Build small projects and iterate', 'Memorize every term before practice', 'Avoid feedback', 'Skip exercises'),
            _mcq('Which is NOT a best practice?', 'Ignoring errors and warnings', 'Writing tests', 'Version control', 'Documenting decisions'),
            _mcq('Which outcome does this topic support?', outs, 'Lower screen brightness', 'Change wallpaper', 'Mute speakers')
        ]

    def generate_questions_for_topic(cat_key: str, topic: str, tpl_obj: dict, course_title: str) -> list:
        # 1) explicit bank lookup
        kvs = [f"{cat_key}::{topic}".lower(), topic.lower()]
        for kv in kvs:
            if kv in quiz_topic_bank:
                items = quiz_topic_bank[kv]
                if isinstance(items, list):
                    normalized = []
                    for it in items[:5]:
                        try:
                            normalized.append({
                                'text': it['text'],
                                'option_a': it.get('option_a') or it.get('A') or it.get('a'),
                                'option_b': it.get('option_b') or it.get('B') or it.get('b'),
                                'option_c': it.get('option_c') or it.get('C') or it.get('c'),
                                'option_d': it.get('option_d') or it.get('D') or it.get('d'),
                                'correct': (it.get('correct') or 'A').strip().upper()[0]
                            })
                        except Exception:
                            continue
                    if len(normalized) >= 3:  # accept if at least 3 well-formed
                        # pad to 5 with heuristics if needed
                        while len(normalized) < 5:
                            extra = _heuristic_questions(cat_key, topic, tpl_obj)[0]
                            normalized.append(extra)
                        return normalized[:5]
        # 2) heuristics
        return _heuristic_questions(cat_key, topic, tpl_obj)

    def classify(title: str) -> str:
        t = (title or '').lower()
        if 'full' in t and 'stack' in t: return 'fullstack'
        if 'python' in t and 'begin' in t: return 'python'
        if 'data science' in t: return 'datasci'
        if 'machine learning' in t: return 'ml'
        if 'cyber' in t: return 'security'
        if 'aws' in t or 'cloud' in t: return 'cloud'
        if 'ui/ux' in t or 'ux' in t or 'ui' in t: return 'uiux'
        if 'marketing' in t: return 'marketing'
        if 'excel' in t or 'financial' in t: return 'finance'
        if 'english' in t or 'communication' in t: return 'english'
        if 'productivity' in t: return 'productivity'
        return 'general'

    TEMPLATES = {
        'fullstack': {
            'modules': [
                'Modern HTML & Semantic Structure',
                'Responsive CSS (Flexbox, Grid) & Accessibility',
                'JavaScript ES6+ and DOM APIs',
                'Version Control with Git & GitHub Flow',
                'Frontend Components and UI Systems',
                'Flask Fundamentals and Jinja Templating',
                'Relational Databases (SQL, SQLite) & ORM',
                'RESTful APIs, Auth, and Sessions',
                'Testing (pytest/unittest) and QA Automation',
                'Deployment (Gunicorn/Nginx), Docker Basics',
                'Performance, Caching, and Observability',
                'CI/CD and Team Practices'
            ],
            'projects': ['Blog + Admin Panel', 'REST API + Single-Page UI'],
            'tools': ['VS Code', 'Git/GitHub', 'Flask', 'Jinja2', 'SQLite/PostgreSQL', 'Docker', 'pytest', 'Nginx'],
            'outcomes': [
                'Build and deploy a secure full-stack web app',
                'Design REST APIs and client integrations',
                'Write tests and set up CI pipelines',
                'Optimize performance and troubleshoot issues'
            ],
            'prereqs': ['Basic computer literacy', 'Beginner programming comfort']
        },
        'python': {
            'modules': [
                'Python Syntax and REPL', 'Variables and Data Types', 'Control Flow', 'Functions',
                'Data Structures (Lists, Dicts, Sets)', 'Modules and Packages', 'File I/O and Errors', 'OOP Basics',
                'Virtual Environments and CLI Apps', 'Mini Projects and Best Practices'
            ],
            'projects': ['CLI To-Do App', 'Log Parser/Analyzer'],
            'tools': ['Python 3.10+', 'pip/venv', 'Black/Flake8', 'VS Code'],
            'outcomes': [
                'Write clear Python scripts and modules', 'Use virtualenv and manage dependencies',
                'Solve problems with idiomatic data structures'
            ],
            'prereqs': ['No prior coding required']
        },
        'datasci': {
            'modules': [
                'Python for Data (NumPy, Pandas)', 'Data Cleaning and Wrangling', 'EDA and Visualization',
                'SQL for Analytics', 'Statistics for Data Science', 'Feature Engineering', 'Intro to ML',
                'Model Evaluation and Validation', 'Storytelling with Data', 'Deploy/Share Insights'
            ],
            'projects': ['Sales Forecasting', 'Customer Churn Analysis'],
            'tools': ['Pandas', 'NumPy', 'Matplotlib/Seaborn', 'SQL', 'scikit-learn'],
            'outcomes': ['Analyze datasets end-to-end', 'Build baseline ML models', 'Communicate insights clearly'],
            'prereqs': ['Comfort with basic Python']
        },
        'ml': {
            'modules': [
                'Supervised Learning (Regression/Classification)', 'Cross-Validation and Metrics', 'Feature Engineering & Pipelines',
                'SVM, Trees, and Ensembles', 'Unsupervised Learning (Clustering/DimRed)', 'Overfitting, Regularization',
                'Model Explainability', 'Intro to MLOps and Deployment'
            ],
            'projects': ['Credit Risk Classifier', 'Image Clustering'],
            'tools': ['scikit-learn', 'Pandas', 'NumPy', 'joblib'],
            'outcomes': ['Train and evaluate ML models', 'Select features and tune hyperparameters'],
            'prereqs': ['Python and basic linear algebra']
        },
        'security': {
            'modules': [
                'Security Mindset and Threat Modeling', 'Networking Basics and TCP/IP', 'OWASP Top 10', 'Cryptography Basics',
                'Secure Coding in Web Apps', 'Identity and Access Management', 'Logging/Monitoring', 'Incident Response'
            ],
            'projects': ['OWASP Top 10 Audit', 'Log Monitoring Playbook'],
            'tools': ['Burp Suite', 'OWASP ZAP', 'Wireshark', 'Hashing/Encryption libs'],
            'outcomes': ['Identify common web vulnerabilities', 'Implement mitigations and monitor risks'],
            'prereqs': ['Basic web concepts']
        },
        'cloud': {
            'modules': [
                'AWS IAM and Security Basics', 'Networking and VPC', 'EC2 and Load Balancing', 'S3 and Object Storage',
                'RDS and Managed Databases', 'Serverless (Lambda, API Gateway)', 'Caching and CDN (CloudFront)', 'Observability (CloudWatch)',
                'Infrastructure as Code (CloudFormation/Terraform)'
            ],
            'projects': ['Serverless Image Resizer', 'Three-Tier Web App on AWS'],
            'tools': ['AWS Console/CLI', 'Terraform', 'CloudFormation'],
            'outcomes': ['Deploy secure, scalable workloads', 'Automate infra with IaC'],
            'prereqs': ['General IT knowledge']
        },
        'uiux': {
            'modules': [
                'Design Thinking and Process', 'User Research Methods', 'Personas and Journeys', 'Information Architecture',
                'Wireframing and Interaction Design', 'Prototyping (Low/High Fidelity)', 'Design Systems and Components', 'Usability Testing',
                'Handoff and Collaboration'
            ],
            'projects': ['Mobile App Prototype', 'Design System Starter'],
            'tools': ['Figma', 'Miro', 'Notion', 'Accessibility Guidelines (WCAG)'],
            'outcomes': ['Produce research-backed designs', 'Prototype and test effectively'],
            'prereqs': ['None; curiosity and empathy']
        },
        'marketing': {
            'modules': [
                'Marketing Fundamentals and Funnels', 'SEO Basics', 'SEM/PPC Campaigns', 'Content Strategy',
                'Social Media and Community', 'Email Marketing and Automation', 'Analytics and Attribution', 'A/B Testing and CRO'
            ],
            'projects': ['SEO Content Plan', 'PPC Campaign Audit'],
            'tools': ['Google Analytics', 'Search Console', 'Ads Manager', 'Email Platforms'],
            'outcomes': ['Plan and execute campaigns', 'Measure performance with analytics'],
            'prereqs': ['Basic web literacy']
        },
        'finance': {
            'modules': [
                'Excel Refresher and Shortcuts', 'Formulas and Functions', 'Pivot Tables and Charts', 'Financial Statements',
                'Ratio and Cohort Analysis', 'DCF and Valuation', 'Scenario and Sensitivity', 'Dashboards and Reporting'
            ],
            'projects': ['3-Statement Model', 'DCF Valuation Sheet'],
            'tools': ['Microsoft Excel', 'Power Query'],
            'outcomes': ['Build financial models', 'Communicate insights via dashboards'],
            'prereqs': ['Basic math and Excel']
        },
        'english': {
            'modules': [
                'Pronunciation and Intonation', 'Vocabulary Building', 'Grammar in Use', 'Active Listening',
                'Presentation Skills', 'Business Writing', 'Interview and Meeting Practice', 'Negotiation and Feedback'
            ],
            'projects': ['Recorded Presentation', 'Business Email Portfolio'],
            'tools': ['Pronunciation apps', 'Style guides'],
            'outcomes': ['Speak clearly and confidently', 'Write professional emails and reports'],
            'prereqs': ['Basic English understanding']
        },
        'productivity': {
            'modules': [
                'Goal Setting and Priorities', 'Timeboxing and Calendars', 'Task Systems (GTD, Kanban)', 'Focus and Deep Work',
                'Habit Formation', 'Weekly and Quarterly Reviews', 'Automation and Tools', 'Collaboration and Boundaries'
            ],
            'projects': ['Personal Productivity System', 'Weekly Review Template'],
            'tools': ['Notion', 'Todoist', 'Calendars', 'Automations'],
            'outcomes': ['Design a sustainable workflow', 'Reduce context switching and burnout'],
            'prereqs': ['None']
        },
        'general': {
            'modules': ['Foundations', 'Core Concepts', 'Hands-on Project', 'Best Practices'],
            'projects': ['Capstone'],
            'tools': ['Common tooling'],
            'outcomes': ['Gain practical skills'],
            'prereqs': ['None']
        }
    }

    enriched_count = 0
    for course in Course.query.all():
        key = classify(course.title)
        tpl = TEMPLATES.get(key)
        if not tpl:
            continue

        # Assign a category-specific default thumbnail for Data Science courses
        # Only if currently missing or using the generic model default (idempotent)
        if key == 'datasci':
            cur_thumb = (course.thumbnail or '').strip()
            if not cur_thumb or cur_thumb == GENERIC_DEFAULT_THUMB:
                course.thumbnail = DATASCI_DEFAULT_THUMB

        # Long description enrichment (only if currently short)
        if not course.long_desc or len(course.long_desc) < 500:
            syllabus_preview = ', '.join(tpl['modules'][:8])
            outcomes_text = '\n- '.join(tpl['outcomes'])
            projects_text = '; '.join(tpl['projects'])
            tools_text = ', '.join(tpl['tools'])
            prereq_text = ', '.join(tpl['prereqs'])

            course.long_desc = (
                f"{course.title} is a comprehensive, outcomes-focused program. You will build real projects,\n"
                f"develop practical skills, and learn industry best practices from end to end.\n\n"
                f"What you'll learn:\n- {outcomes_text}\n\n"
                f"Syllabus highlights: {syllabus_preview}.\n\n"
                f"Projects: {projects_text}.\n"
                f"Tools covered: {tools_text}.\n"
                f"Prerequisites: {prereq_text}.\n"
                f"Who is this for: learners seeking a structured, hands-on path to mastery."
            )
            enriched_count += 1

        # Ensure a baseline number of lessons using module names as lesson titles
        existing_count = len(course.lessons)
        target = len(tpl['modules'])
        if existing_count < target:
            start_pos = existing_count + 1
            for i in range(existing_count, target):
                mod = tpl['modules'][i]
                lesson_title = f"Lesson {i+1}: {mod}"
                content_html = (
                    f"<p>{mod} in {course.title}: concepts, best practices, and a practical lab.</p>"
                    f"<ul><li>Core concepts</li><li>Hands-on exercise</li><li>Review checklist</li></ul>"
                )
                # Use curated intro for the very first lesson if available; otherwise topic-aligned fallback
                intro_url = curated_intro_for(key) if i == 0 else None
                video_url = intro_url or video_for_topic(key, mod, course.title)
                db.session.add(Lesson(course_id=course.id, title=lesson_title, position=start_pos + (i - existing_count), content=content_html, video_url=video_url))

        # Assign curated videos to existing lessons that are missing a video or still use the default placeholder
        try:
            sorted_lessons = sorted(course.lessons, key=lambda l: (l.position or 0, l.id or 0))
        except Exception:
            sorted_lessons = list(course.lessons)
        for idx, l in enumerate(sorted_lessons):
            current = (l.video_url or '').strip()
            current_lc = current.lower()
            # Ensure curated intro on the first lesson (overrides other sources)
            if idx == 0:
                cur_intro = curated_intro_for(key)
                if cur_intro:
                    cur_norm = (normalize_to_embed(current) or '').lower()
                    if cur_norm != cur_intro.lower():
                        l.video_url = cur_intro
                    # curated applied; move to next lesson
                    continue
            # Upgrade placeholders/weak embeds for all lessons (including first if no curated available)
            if (
                (not current_lc)
                or ('vimeo.com' in current_lc)
                or ('youtube.com/embed/videoseries' in current_lc)
                or ('/embed?listtype=search' in current_lc)
                or (current_lc == (DEFAULT_VIDEO or '').lower())
            ):
                topic = topic_from_title(l.title or f"Lesson {idx+1}")
                l.video_url = video_for_topic(key, topic, course.title)
        # Ensure at least 10 quizzes exist (idempotent add-only)
        existing_quiz_count = Quiz.query.filter_by(course_id=course.id).count()
        if existing_quiz_count < 10:
            for qn in range(existing_quiz_count + 1, 11):
                title_mod = None
                try:
                    title_mod = tpl['modules'][(qn - 1) % target]
                except Exception:
                    title_mod = None
                quiz_title = f"Quiz {qn}: {title_mod}" if title_mod else f"Quiz {qn}"
                qz = Quiz(course_id=course.id, title=quiz_title)
                db.session.add(qz)
                # Flush so we can reference qz.id for questions
                db.session.flush()
                # Placeholder questions will be replaced below with topic-aligned items
                for qi in range(1, 6):
                    db.session.add(Question(
                        quiz_id=qz.id,
                        text=f"Q{qi}. Concept check for {course.title}.",
                        option_a="Option A",
                        option_b="Option B",
                        option_c="Option C",
                        option_d="Option D",
                        correct="A"
                    ))

        # Upgrade/align quizzes to topic-specific questions (idempotent)
        quizzes = Quiz.query.filter_by(course_id=course.id).order_by(Quiz.id.asc()).all()
        for qi, qz in enumerate(quizzes[:min(10, len(quizzes))]):
            topic_title = tpl['modules'][qi % target]
            desired_title = f"Quiz {qi+1}: {topic_title}"
            # Detect placeholders or misaligned titles
            is_placeholder = (len(qz.questions) < 5) or all(('concept check for' in (qs.text or '').lower()) for qs in qz.questions)
            is_misaligned = (':' not in (qz.title or '')) or (qz.title != desired_title)
            if is_placeholder or is_misaligned:
                qs = generate_questions_for_topic(key, topic_title, tpl, course.title)
                # Replace questions
                for old in list(qz.questions):
                    db.session.delete(old)
                db.session.flush()
                for item in qs[:5]:
                    try:
                        db.session.add(Question(
                            quiz_id=qz.id,
                            text=item['text'],
                            option_a=item['option_a'],
                            option_b=item['option_b'],
                            option_c=item['option_c'],
                            option_d=item['option_d'],
                            correct=item['correct']
                        ))
                    except Exception:
                        # Fallback to a safe placeholder to avoid empty quizzes
                        db.session.add(Question(
                            quiz_id=qz.id,
                            text=f"Concept check: {topic_title}",
                            option_a="Correct",
                            option_b="Incorrect 1",
                            option_c="Incorrect 2",
                            option_d="Incorrect 3",
                            correct='A'
                        ))
                qz.title = desired_title

    db.session.commit()
    app.logger.info(f'Enriched courses: {enriched_count} updated, lessons ensured where missing.')
    # Persist cache updates if any
    if cache_dirty:
        save_video_cache(video_cache, cache_path)

@app.before_request
def _enrich_once_on_request():
    # In production/staging, ensure enrichment runs once on the first request; skip during tests
    if app.config.get('TESTING') or app.config.get('_ENRICH_DONE'):
        return
    try:
        enrich_courses()
        app.config['_ENRICH_DONE'] = True
    except Exception as e:
        app.logger.warning('Content enrichment skipped: %s', e)

# ---------------------- AI FEATURES (MOCK) ----------------------
class MockAIService:
    @staticmethod
    def generate_quiz(content):
        # deterministically generate questions based on content length or keywords
        # mocking a call to an LLM
        questions = []
        topics = ['Key Concept', 'Advanced Topic', 'Best Practice', 'Common Pitfall', 'Real-world Application']
        for i, t in enumerate(topics):
            questions.append({
                'text': f"AI Generated: What is the significance of {t} in this context?",
                'option_a': f"It explains {t} clearly.",
                'option_b': f"It contradicts {t}.",
                'option_c': f"It is unrelated to {t}.",
                'option_d': "None of the above.",
                'correct': 'A'
            })
        return questions

    @staticmethod
    def chat(message):
        msg = message.lower()
        if 'hello' in msg or 'hi' in msg:
            return "Hello! I am your AI learning assistant. How can I help you regarding this course?"
        if 'explain' in msg:
            return "I can certainly explain that concept. Could you provide more specific details about what you're stuck on?"
        if 'quiz' in msg:
            return "Quizzes are a great way to test your knowledge! Check the Quizzes tab."
        if 'python' in msg:
            return "Python is a versatile language used for web dev, data science, and more. Keep practicing!"
        return "That's an interesting question. Try checking the lesson content or asking in the discussion forum for more peer insights."

@app.route('/instructor/course/<int:cid>/ai-generate-quiz', methods=['POST'])
@login_required
@instructor_required
def ai_generate_quiz_route(cid):
    c = db.get_or_404(Course, cid)
    if c.instructor != current_user.name and current_user.role != 'admin':
        flash('Not authorized.', 'danger')
        return redirect(url_for('instructor_courses'))
    # mock generation from course description or first lesson
    content = c.long_desc
    questions = MockAIService.generate_quiz(content)
    
    # Create a new quiz
    quiz = Quiz(course_id=cid, title=f"AI Generated Quiz: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    db.session.add(quiz)
    db.session.commit()
    
    for q in questions:
        db.session.add(Question(
            quiz_id=quiz.id,
            text=q['text'],
            option_a=q['option_a'],
            option_b=q['option_b'],
            option_c=q['option_c'],
            option_d=q['option_d'],
            correct=q['correct']
        ))
    db.session.commit()
    flash('AI Quiz generated successfully!', 'success')
    return redirect(url_for('instructor_questions', qid=quiz.id))

# ---------------------- ATTENDANCE SYSTEM ----------------------
@app.route('/instructor/attendance')
@login_required
@instructor_required
def instructor_attendance():
    """List courses the instructor can manage attendance for."""
    if current_user.role == 'admin':
        courses = Course.query.all()
    else:
        courses = Course.query.filter_by(instructor=current_user.name).all()
    return render_template('instructor_attendance_list.html', courses=courses)

@app.route('/instructor/courses/<int:cid>/attendance', methods=['GET', 'POST'])
@login_required
@instructor_required
def mark_attendance(cid):
    """Mark attendance for a specific course and date."""
    course = db.get_or_404(Course, cid)
    date_str = request.args.get('date', datetime.date.today().isoformat())
    selected_date = datetime.date.fromisoformat(date_str)
    
    # Check if user is instructor for this course
    if current_user.role != 'admin' and course.instructor != current_user.name:
        abort(403)
        
    enrollments = Enrollment.query.filter_by(course_id=cid).all()
    students = [db.session.get(User, e.student_id) for e in enrollments]
    
    # Fetch existing records for this date
    existing_records = {r.student_id: r.status for r in Attendance.query.filter_by(course_id=cid, date=selected_date).all()}
    
    if request.method == 'POST':
        # Bulk mark attendance
        for student in students:
            status = request.form.get(f'status_{student.id}', 'Absent')
            record = Attendance.query.filter_by(student_id=student.id, course_id=cid, date=selected_date).first()
            if record:
                record.status = status
            else:
                db.session.add(Attendance(student_id=student.id, course_id=cid, date=selected_date, status=status))
        db.session.commit()
        flash(f'Attendance for {date_str} saved successfully.', 'success')
        return redirect(url_for('mark_attendance', cid=cid, date=date_str))
        
    return render_template('instructor_attendance_mark.html', course=course, students=students, selected_date=selected_date, existing_records=existing_records)

@app.route('/instructor/courses/<int:cid>/attendance/history')
@login_required
@instructor_required
def attendance_history(cid):
    """View attendance history for a course."""
    course = db.get_or_404(Course, cid)
    if current_user.role != 'admin' and course.instructor != current_user.name:
        abort(403)
        
    records = Attendance.query.filter_by(course_id=cid).order_by(Attendance.date.desc()).all()
    # Group by date for history view
    history = {}
    for r in records:
        if r.date not in history:
            history[r.date] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
        history[r.date]['total'] += 1
        history[r.date][r.status.lower()] += 1
        
    return render_template('instructor_attendance_history.html', course=course, history=history)

@app.route('/student/attendance')
@login_required
def student_attendance():
    """Student dashboard for attendance."""
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    attendance_data = []
    threshold = get_attendance_threshold()
    
    for e in enrollments:
        course = db.session.get(Course, e.course_id)
        total_days = Attendance.query.filter_by(course_id=e.course_id).group_by(Attendance.date).count()
        present_days = Attendance.query.filter_by(student_id=current_user.id, course_id=e.course_id, status='Present').count()
        late_days = Attendance.query.filter_by(student_id=current_user.id, course_id=e.course_id, status='Late').count()
        
        # Late counts as half presence or similar? Let's say Present + Late
        attended = present_days + late_days
        percentage = (attended / total_days * 100) if total_days > 0 else 100
        
        attendance_data.append({
            'course': course,
            'percentage': round(percentage, 1),
            'total': total_days,
            'attended': attended,
            'below_threshold': percentage < threshold
        })
        
    return render_template('student_attendance.html', attendance_data=attendance_data, threshold=threshold)

@app.route('/admin/attendance/report')
@admin_required
def admin_attendance_report():
    """Global attendance report for admins."""
    courses = Course.query.all()
    report_data = []
    for c in courses:
        total_records = Attendance.query.filter_by(course_id=c.id).count()
        present_records = Attendance.query.filter_by(course_id=c.id, status='Present').count()
        avg_pct = (present_records / total_records * 100) if total_records > 0 else 0
        report_data.append({
            'course': c,
            'avg_pct': round(avg_pct, 1),
            'enrollments': Enrollment.query.filter_by(course_id=c.id).count()
        })
    return render_template('admin_attendance_report.html', report_data=report_data)


@app.route('/api/chat/<int:cid>', methods=['POST'])
@login_required
def api_chat(cid):
    if not gemini_client:
        return jsonify({'status': 'error', 'reply': "AI Study Buddy is currently unavailable."})
        
    # Check enrollment
    if not Enrollment.query.filter_by(student_id=current_user.id, course_id=cid).first() and current_user.role != 'admin':
        return jsonify({'status': 'error', 'reply': "You must be enrolled to use the Study Buddy."})
        
    data = request.get_json()
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'status': 'error', 'reply': "Please ask a question."})
        
    # Gather course context (simplified RAG by stuffing context)
    lessons = Lesson.query.filter_by(course_id=cid).order_by(Lesson.position.asc()).all()
    course = db.session.get(Course, cid)
    
    context = ""
    for l in lessons:
        # truncate massive content just in case, though 1M token limit is huge
        context += f"--- Lesson: {l.title} ---\n{l.content}\n\n"
        
    prompt = f"You are an AI Study Buddy for the course '{course.title}'. Answer the student's question strictly based on the provided Course Content below. If the answer is not in the content or if the question is off-topic, politely say you only answer questions related to the course material. Keep your response encouraging, concise, and helpful.\n\nCOURSE CONTENT:\n{context}\n\nSTUDENT QUESTION: {msg}"
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return jsonify({'status': 'ok', 'reply': response.text})
    except Exception as e:
        print(f"Gemini Chat error: {e}")
        return jsonify({'status': 'error', 'reply': "Sorry, I had trouble thinking about that. Please try again."})

if __name__ == '__main__':
    with app.app_context():
        # Only run these setups if we are actually starting the server, not just running a CLI command.
        import sys
        if len(sys.argv) <= 1:
            db.create_all()
            # Enrich course content on startup (idempotent)
            try:
                enrich_courses()
            except Exception as e:
                app.logger.warning('Content enrichment skipped: %s', e)
            # ensure default admin exists
            if not User.query.filter_by(email='admin@edulearn.com').first():
                db.session.add(User(name='Admin', email='admin@edulearn.com', password_hash=generate_password_hash('admin123'), role='admin'))
                db.session.commit()
            # ensure we have at least 10 demo courses
            if Course.query.count() < 10:
                # reuse seed logic for courses only
                sample_courses = [
                    ("Python for Beginners", "Start coding in Python from scratch.", "A gentle introduction to Python covering syntax, data structures, and projects.", "Alice Kim"),
                    ("Data Science Bootcamp", "End-to-end DS workflow.", "Learn data wrangling, visualization, and modeling with real datasets.", "Dr. Ravi Singh"),
                    ("Machine Learning A–Z", "Supervised and unsupervised.", "Hands-on ML with scikit-learn, covering regression, classification, and clustering.", "Maria Gomez"),
                    ("Cybersecurity Fundamentals", "Protect systems and data.", "Threats, vulnerabilities, and best practices for securing applications.", "Ethan Park"),
                    ("Cloud Computing with AWS", "Deploy in the cloud.", "Core AWS services, IAM, EC2, S3, and serverless basics.", "Noah Williams"),
                    ("UI/UX Design Masterclass", "Design delightful products.", "User research, wireframing, prototyping, and usability testing.", "Sara Lee"),
                    ("Digital Marketing 101", "Grow your audience.", "SEO, SEM, social media strategy, and email marketing fundamentals.", "David Chen"),
                    ("Financial Analysis with Excel", "Make data-driven decisions.", "Modeling, dashboards, and scenario analysis with Excel.", "Priya Patel"),
                    ("English Communication Skills", "Speak with confidence.", "Improve speaking, listening, and presentation skills.", "John Miller"),
                    ("Personal Productivity", "Get more done.", "Time management, focus techniques, and workflow systems.", "Emma Davis"),
                ]
                thumbs = [
                    'https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1551281044-8d8d4e89f2f4?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1510511459019-5dda7724fd87?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1557800636-894a64c1696f?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1543286386-2e659306cd6c?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?q=80&w=1200&auto=format&fit=crop',
                    'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=1200&auto=format&fit=crop',
                ]
                cur = Course.query.count()
                to_add = 10 - cur
                for i in range(to_add):
                    title, sd, ld, instr = sample_courses[i % len(sample_courses)]
                    thumb = thumbs[i % len(thumbs)]
                    db.session.add(Course(title=title, short_desc=sd, long_desc=ld, instructor=instr, thumbnail=thumb))
                db.session.commit()
            # Enrich again after seeding to cover newly added demo courses
            try:
                enrich_courses()
                app.config['_ENRICH_DONE'] = True
            except Exception as e:
                app.logger.warning('Post-seed enrichment skipped: %s', e)
    app.run(debug=True)
