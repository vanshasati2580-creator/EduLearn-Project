# 🛠 EduLearn — Technology Stack

> A comprehensive breakdown of every technology, library, tool, and design pattern powering the EduLearn platform.

---

## 📋 Table of Contents

1. [Stack Overview](#-stack-overview)
2. [Backend](#-backend)
3. [Database](#-database)
4. [Frontend](#-frontend)
5. [Styling & Design System](#-styling--design-system)
6. [JavaScript (Client-Side)](#-javascript-client-side)
7. [Authentication & Security](#-authentication--security)
8. [Templating Engine](#-templating-engine)
9. [Video Integration](#-video-integration)
10. [External Services & CDNs](#-external-services--cdns)
11. [Testing](#-testing)
12. [Development & Tooling](#-development--tooling)
13. [Architecture Patterns](#-architecture-patterns)
14. [Dependency Summary](#-dependency-summary)

---

## 🔎 Stack Overview

| Layer              | Technology                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------|
| **Language**       | Python 3.10+                                                                                   |
| **Web Framework**  | Flask 2.3.3                                                                                    |
| **ORM**            | Flask-SQLAlchemy 3.1.1 (SQLAlchemy)                                                           |
| **Database**       | SQLite 3 (file-based, via SQLAlchemy)                                                         |
| **Auth**           | Flask-Login 0.6.3 + Werkzeug 3.0.3 password hashing                                          |
| **Templating**     | Jinja2 (bundled with Flask)                                                                    |
| **CSS Framework**  | Bootstrap 5.3.2 (CDN)                                                                         |
| **Custom Styling** | Vanilla CSS (~633 lines, glassmorphism + dark/light theme system)                             |
| **JavaScript**     | Vanilla ES6+ (~621 lines, no frameworks)                                                      |
| **Fonts**          | Google Fonts — Inter (body) + Playfair Display (headings)                                     |
| **Icons**          | Font Awesome (via CDN)                                                                         |
| **Video**          | YouTube iframe embeds (curated + API-driven)                                                   |
| **Images**         | Unsplash (course thumbnails) + user-uploaded files                                             |
| **Testing**        | pytest                                                                                         |

---

## 🐍 Backend

### Core Framework — Flask 2.3.3

Flask is a lightweight WSGI micro-framework for Python. EduLearn uses it as the backbone for all routing, request handling, and server-side logic.

| Component             | Details                                                                                         |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Entry Point**       | `app.py` — single-file monolith (~2,157 lines)                                                |
| **App Factory**       | Direct instantiation via `Flask(__name__)`                                                     |
| **Config**            | In-app configuration (`SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `UPLOAD_FOLDER`)                |
| **Debug Mode**        | Enabled by default for development (`debug=True`)                                              |
| **Static Files**      | Served from `static/` (CSS, JS, images, JSON data)                                            |
| **File Uploads**      | Handled via `werkzeug.utils.secure_filename`, stored in `static/uploads/`                      |

### Python Standard Library Usage

The following standard library modules are used directly in `app.py`:

| Module           | Purpose                                                            |
|------------------|--------------------------------------------------------------------|
| `os`             | File path manipulation, environment variables (`YOUTUBE_API_KEY`)   |
| `json`           | Reading/writing video data JSON files                               |
| `datetime`       | Timestamps, certificate dates, coupon expiry, Night Owl badge check |
| `random`         | Shuffling quiz questions, demo data generation                      |
| `re`             | Regular expressions for content parsing and URL matching            |
| `urllib.parse`   | URL parsing (`urlparse`, `parse_qs`, `quote_plus`)                  |
| `urllib.request` | HTTP requests for YouTube API/video search fallback                 |
| `functools`      | `wraps` decorator for route decorators                              |

### Flask Extensions

| Extension             | Version | Purpose                                                      |
|-----------------------|---------|--------------------------------------------------------------|
| **Flask-SQLAlchemy**  | 3.1.1   | ORM integration — model definitions, queries, migrations      |
| **Flask-Login**       | 0.6.3   | Session-based authentication, `@login_required`, user loader  |
| **Werkzeug**          | 3.0.3   | Password hashing (`generate_password_hash`, `check_password_hash`), secure file uploads |

### Custom Decorators

```python
@login_required        # Flask-Login: requires authenticated user
@admin_required        # Custom: restricts to role == 'admin'
@instructor_required   # Custom: restricts to role in ['instructor', 'admin']
```

### CLI Commands

Flask CLI commands are registered for database management:

| Command          | Description                                        |
|------------------|----------------------------------------------------|
| `flask initdb`   | Initialize the database schema                     |
| `flask seed`     | Seed demo users, courses, badges, and coupons      |
| `flask enrich`   | Run the content enrichment engine on all courses    |

---

## 🗄 Database

### SQLite via SQLAlchemy ORM

| Property            | Value                                                           |
|---------------------|-----------------------------------------------------------------|
| **Engine**          | SQLite 3 (serverless, file-based)                               |
| **Database File**   | `instance/edulearn_full.db`                                     |
| **ORM**             | SQLAlchemy (via Flask-SQLAlchemy 3.1.1)                         |
| **Schema Approach** | Declarative models in `app.py` (13 models)                      |
| **Auto-Creation**   | Tables created automatically on first run via `db.create_all()` |
| **Relationships**   | One-to-Many, Many-to-Many (via join tables)                     |
| **Querying**        | SQLAlchemy Query API + `func` aggregations (`avg`, `count`)     |

### 13 Database Models

| Model          | Table              | Records                           |
|----------------|--------------------|------------------------------------|
| `User`         | `user`             | Students, Instructors, Admins      |
| `Badge`        | `badge`            | Achievement definitions            |
| `UserBadge`    | `user_badge`       | Earned badges (M:N join)           |
| `Course`       | `course`           | Course metadata                    |
| `Lesson`       | `lesson`           | Individual lessons                 |
| `Quiz`         | `quiz`             | Course quizzes                     |
| `Question`     | `question`         | MCQ questions (4 options A–D)      |
| `Enrollment`   | `enrollment`       | Student ↔ Course enrollment        |
| `Discussion`   | `discussion`       | Forum posts per course             |
| `Review`       | `review`           | Star ratings + comments            |
| `Favorite`     | `favorite`         | Wishlist (unique per user+course)  |
| `Coupon`       | `coupon`           | Discount codes                     |
| `Note`         | `note`             | Timestamped lesson notes           |

### Key SQLAlchemy Features Used

- **Relationship cascades** — `cascade="all, delete-orphan"` on Course → Lessons/Quizzes/Discussions
- **Unique constraints** — `UniqueConstraint('user_id', 'course_id')` on Favorites
- **Aggregate queries** — `func.avg()`, `func.count()`, `func.upper()` for ratings, enrollment stats, coupon lookup
- **Full-text search** — `ilike()` for course search across title, short_desc, long_desc
- **Compound filtering** — `or_()` for multi-field search queries

---

## 🎨 Frontend

### HTML5

- **Semantic structure** — `<main>`, `<nav>`, `<header>`, `<footer>`, `<section>`, `<article>`
- **Responsive meta** — `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **26 Jinja2 templates** in `templates/` covering all views
- **Accessible forms** — `aria-label`, `aria-controls`, `aria-pressed`, `role="search"`, `role="status"`, `aria-live="polite"`

### Template Hierarchy

```
base.html                         ← Master layout (navbar, flash toasts, footer, chatbot)
├── index.html                    ← Homepage (hero, trending, categories, testimonials)
├── login.html / register.html    ← Auth pages
├── dashboard.html                ← Student dashboard with progress bars
├── course_detail.html            ← Rich course landing page (~22 KB)
├── lesson.html                   ← Video player + notes sidebar
├── quiz.html                     ← Quiz taking interface
├── checkout.html / cart.html     ← Payment flow
├── certificate.html              ← Completion certificate
├── search.html / wishlist.html   ← Browse & save
├── leaderboard.html              ← XP rankings
├── about.html                    ← Team page
├── admin_users.html              ← User management
├── admin_courses.html            ← Course management
└── instructor_*.html (×7)        ← Course/Lesson/Quiz/Question CRUD
```

---

## 💅 Styling & Design System

### Bootstrap 5.3.2 (CDN)

- **Source**: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css`
- **JS Bundle**: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js`
- **Usage**: Grid system, responsive utilities, cards, navbars, modals, toasts, forms, accordions, badges, buttons, progress bars, tables

### Custom CSS — `style.css` (~633 lines, ~29 KB)

#### Design Tokens (CSS Custom Properties)

```css
:root {
  --blue: #0056D2;              /* Primary brand color */
  --bg: #0b1020;                /* Dark background */
  --glass: rgba(255,255,255,0.06);  /* Glassmorphism fill */
  --border: rgba(255,255,255,0.12); /* Subtle borders */
  --btn-shadow-dark: 0 10px 24px rgba(0,0,0,.35);
  --btn-shadow-blue: 0 8px 24px rgba(59,134,255,.35);
  --btn-shadow-green: 0 8px 24px rgba(34,197,94,.35);
}
```

#### Dark / Light Theme System

| Theme   | Background                              | Text Color | Glass Fill                    |
|---------|-----------------------------------------|------------|-------------------------------|
| **Dark** (default) | Radial gradient `#0b1020 → #0a0e1a` | `#eef2ff`  | `rgba(255,255,255,0.06)`     |
| **Light** | Gradient `#f8fafc → #eef2f7`         | `#0f172a`  | `rgba(255,255,255,0.9)`      |

Theme is toggled via `data-theme="light"` attribute on `<body>`, persisted in `localStorage`.

#### Key Design Patterns

| Pattern              | Implementation                                                           |
|----------------------|--------------------------------------------------------------------------|
| **Glassmorphism**    | `backdrop-filter: blur(10px)` + semi-transparent backgrounds             |
| **Floating Navbar**  | Glass navbar that shrinks, rounds, and floats on scroll (≥992px)         |
| **Scroll Progress**  | Fixed gradient bar at the top showing scroll position                    |
| **Card Animations**  | `fade-up` and `pop-card` with IntersectionObserver-triggered reveals     |
| **3D Card Tilt**     | `rotateX(.75deg) rotateY(-.75deg)` on hover                             |
| **Button Spotlight** | Radial gradient follows cursor via `--spx`/`--spy` CSS variables        |
| **Ripple Effect**    | Material Design-style ripple on button clicks                            |
| **Shiny Text**       | Animated gradient sweep on `.text-shine` elements                        |
| **Loading Spinner**  | CSS-only spinner via `::after` pseudo-element on `.btn.is-loading`       |
| **Float Animation**  | `@keyframes float` for decorative card bobbing                           |

#### Typography

| Role      | Font Family                | Weights       | Usage                     |
|-----------|----------------------------|---------------|---------------------------|
| **Body**  | Inter (Google Fonts)       | 300, 400, 600, 800 | All body text, UI elements |
| **Headings** | Playfair Display (Google Fonts) | 600, 700, 800 | h1–h6, brand logo     |
| **Fallback** | system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif | — | System font stack |

#### Accessibility Features in CSS

- `prefers-reduced-motion` — disables all animations (float, ripple, shake, card reveals, orb drift)
- Focus-visible ring — `.btn:focus-visible` with blue box-shadow
- `aria-hidden`, `role="status"`, `aria-live="polite"` for dynamic content
- High contrast ensured across both dark and light themes

---

## ⚡ JavaScript (Client-Side)

### `app.js` (~621 lines, ~26 KB) — Vanilla ES6+

No frameworks or build tools. All JS is hand-written using modern browser APIs:

#### Core Features

| Feature                    | API / Technique                                     |
|----------------------------|-----------------------------------------------------|
| **Scroll Reveal Animations** | `IntersectionObserver` with threshold `.12`         |
| **Button Ripple Effect**   | Dynamic `<span>` creation + CSS `@keyframes ripple`  |
| **Spotlight Hover**        | `pointermove` event → CSS custom properties (`--spx`, `--spy`) |
| **Scroll Progress Bar**    | `requestAnimationFrame` + `scaleX` transform         |
| **Dashboard Progress**     | Animated width + counter using `requestAnimationFrame` |
| **Dark/Light Theme**       | `localStorage` persistence + system preference detection (`prefers-color-scheme`) |
| **Floating Navbar**        | Scroll-based class toggle (`is-floating`) via `requestAnimationFrame` |
| **Credit Card Formatting** | Real-time input masking (card number, expiry, CVV)   |
| **Clipboard / Web Share**  | `navigator.share()` API with `navigator.clipboard` fallback |
| **Coupon Application**     | URL parameter injection for coupon codes             |
| **Unsplash URL Rewriting** | Broken page-link URLs → CDN direct URLs with fallback chain |

#### AI Chatbot (Inline in `base.html`)

| Feature                    | Implementation                                       |
|----------------------------|------------------------------------------------------|
| **Chat Widget**            | Fixed-position card with toggle button               |
| **Message Sending**        | `fetch('/api/chat', ...)` with JSON body              |
| **Typing Indicator**       | Dynamic `...` badge, removed on response              |
| **Message Rendering**      | Dynamic DOM creation with Bootstrap badges            |

#### Analytics System

A lightweight analytics emitter integrated throughout `app.js`:

```javascript
analytics.emit(event, payload)  // Pushes to window.dataLayer or console.log
```

**Tracked Events:**
- `login_view`, `login_submit`, `login_error`, `login_toggle_password`, `login_capslock`, `login_forgot_password`
- `sticky_cta_visibility`, `sticky_cta_assign`, `cta_click`
- `share_used`, `coupon_apply`, `add_to_cart`, `wishlist_toggle`
- `hero_assign`, `hero_cta_click`, `section_view`
- `search_submit`, `popular_query_click`, `category_click`, `course_card_click`
- `newsletter_subscribe`

#### A/B Testing Support

Two A/B test variants built into the JS:
1. **Sticky CTA Variant** — `localStorage('cta_variant')` → A or B
2. **Hero Layout Variant** — `localStorage('hero_variant')` → A or B (variant B uses green CTA)

#### Parallax Effects

- Hero section parallax: left column moves up, right column moves down on scroll
- Respects `prefers-reduced-motion` media query

---

## 🔐 Authentication & Security

| Feature                    | Technology                                           |
|----------------------------|------------------------------------------------------|
| **Session Management**     | Flask-Login 0.6.3 (`login_user`, `logout_user`, `current_user`) |
| **Password Storage**       | Werkzeug `generate_password_hash` / `check_password_hash` (PBKDF2-SHA256) |
| **CSRF Protection**        | Flask session-based with `SECRET_KEY`                |
| **Route Protection**       | `@login_required`, `@admin_required`, `@instructor_required` decorators |
| **Role-Based Access**      | Three roles: `student`, `instructor`, `admin`        |
| **File Upload Safety**     | `werkzeug.utils.secure_filename` for uploaded images |
| **Payment Validation**     | Luhn algorithm for mock credit card validation       |
| **Input Sanitization**     | Jinja2 auto-escaping for XSS prevention              |

---

## 🧩 Templating Engine

### Jinja2 (Bundled with Flask)

| Feature Used             | Example                                              |
|--------------------------|------------------------------------------------------|
| **Template Inheritance** | `{% extends 'base.html' %}` / `{% block content %}`  |
| **Variables**            | `{{ course.title }}`, `{{ price_str }}`               |
| **Conditionals**         | `{% if current_user.is_authenticated %}`              |
| **Loops**                | `{% for lesson in lessons %}`                         |
| **Filters**              | Built-in Jinja2 filters for string formatting         |
| **Flash Messages**       | `get_flashed_messages(with_categories=true)`          |
| **URL Generation**       | `{{ url_for('static', filename='css/style.css') }}`   |
| **Context Processors**   | `current_user` injected globally via Flask-Login      |

---

## 🎬 Video Integration

### YouTube Embed System

| Component                  | Details                                              |
|----------------------------|------------------------------------------------------|
| **Embed Method**           | `<iframe>` with `youtube.com/embed/{video_id}` URLs  |
| **URL Normalization**      | `normalize_to_embed()` — converts watch/shorts/youtu.be → embed |
| **Curated Videos**         | `static/data/video_curated_intro.json` — intro videos per category |
| **Topic Mapping**          | `static/data/video_topics_map.json` — topic → embed URL |
| **Channel Mapping**        | `static/data/video_channels.json` — YouTube channel IDs per category |
| **Runtime Cache**          | `static/data/video_cache.json` — cached API/search results |
| **API Key (Optional)**     | `YOUTUBE_API_KEY` env var for YouTube Data API v3 search |

### Video Resolution Fallback Chain

```
1. Curated intro video (for first lessons)
   ↓ (not found)
2. Topic-specific mapping from video_topics_map.json
   ↓ (not found)
3. Cached results from video_cache.json
   ↓ (not found)
4. YouTube Data API v3 search (if API key configured)
   ↓ (not available)
5. YouTube search embed fallback
   ↓ (not available)
6. Channel playlist fallback from video_channels.json
```

---

## 🌐 External Services & CDNs

| Service                    | URL / Source                                                      | Purpose                |
|----------------------------|-------------------------------------------------------------------|------------------------|
| **Bootstrap CSS**          | `cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css` | UI framework           |
| **Bootstrap JS**           | `cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js` | Interactive components |
| **Google Fonts**           | `fonts.googleapis.com` — Inter + Playfair Display                  | Typography             |
| **Font Awesome**           | CDN (referenced in templates)                                      | Icon library           |
| **Unsplash**               | `images.unsplash.com` — direct photo CDN                           | Course thumbnails      |
| **YouTube**                | `youtube.com/embed/` — iframe embeds                               | Video lessons          |
| **YouTube Data API v3**    | Optional — requires `YOUTUBE_API_KEY`                              | Video search           |
| **Placehold.co**           | `placehold.co` — placeholder service                               | Image fallback         |

---

## 🧪 Testing

| Tool       | Details                                                          |
|------------|------------------------------------------------------------------|
| **Framework** | pytest                                                        |
| **Location**  | `tests/` directory                                             |
| **Test Files** | `test_features.py`, `test_course_page_ui.py`, `test_about_page.py` |
| **Run Command** | `python -m pytest tests/`                                    |

---

## 🔧 Development & Tooling

| Tool / Practice      | Details                                                           |
|----------------------|-------------------------------------------------------------------|
| **Runtime**          | Python 3.10+ with Flask development server                       |
| **Dev Server**       | `python app.py` → `http://127.0.0.1:5000` (debug mode)           |
| **Package Manager**  | pip (dependencies in `requirements.txt`)                          |
| **Version Control**  | Git                                                               |
| **Asset Versioning** | Query string cache-busting (`?v=16` for CSS, `?v=11` for JS)     |
| **Database Location** | `instance/edulearn_full.db` (Flask instance folder convention)   |
| **Static Data**      | JSON files in `static/data/` for video configurations             |
| **Upload Storage**   | Local filesystem (`static/uploads/`)                              |
| **Auto-Seeding**     | Database auto-seeds on first startup (admin, courses, enrichment) |

---

## 🏗 Architecture Patterns

### Monolithic Single-File Architecture

All backend logic resides in `app.py` (~2,157 lines), organized into clear sections:

```
app.py
├── Configuration & App Setup
├── Models (13 SQLAlchemy models)
├── Auth Helpers (login_manager, decorators)
├── Business Logic Helpers (pricing, Luhn, discounts, XP, badges)
├── Public Routes (/, /about, /register, /login, etc.)
├── Student Routes (/dashboard, /lesson, /quiz, /checkout, etc.)
├── API Endpoints (/api/note, /api/flashcards, /api/chat)
├── Instructor Routes (/instructor/*)
├── Admin Routes (/admin/*)
├── Content Enrichment Engine (enrich_courses())
├── Mock AI Service (MockAIService class)
├── CLI Commands (initdb, seed, enrich)
└── Main Entry Point (app.run)
```

### Key Design Patterns Used

| Pattern                    | Implementation                                       |
|----------------------------|------------------------------------------------------|
| **MVC-like**               | Models in `app.py`, Views in `templates/`, Controllers as route functions |
| **Decorator Pattern**      | `@login_required`, `@admin_required`, `@instructor_required` |
| **Template Inheritance**   | `base.html` → child templates via Jinja2 `extends`   |
| **Repository Pattern**     | SQLAlchemy models encapsulate data access              |
| **Observer (client-side)** | `IntersectionObserver` for scroll-based reveals        |
| **Strategy Pattern**       | Multi-tier video resolution fallback chain             |
| **Event-Driven (client)**  | Analytics event emitter with `dataLayer` integration   |
| **Idempotent Operations**  | Content enrichment engine safely re-runnable           |

---

## 📦 Dependency Summary

### `requirements.txt`

```
flask==2.3.3
flask-login==0.6.3
flask-sqlalchemy==3.1.1
werkzeug==3.0.3
```

### Implicit Dependencies (installed via pip with Flask)

| Package       | Role                                  |
|---------------|---------------------------------------|
| **Jinja2**    | Template rendering engine             |
| **MarkupSafe** | Safe string handling for Jinja2      |
| **itsdangerous** | Secure token signing (sessions)   |
| **click**     | Flask CLI framework                   |
| **blinker**   | Signal support for Flask              |

### Frontend Dependencies (CDN, no npm/node)

| Package           | Version | Delivery |
|-------------------|---------|----------|
| **Bootstrap**     | 5.3.2   | CDN      |
| **Google Fonts**  | —       | CDN      |
| **Font Awesome**  | —       | CDN      |

### Dev Dependencies

| Package   | Purpose         |
|-----------|-----------------|
| **pytest** | Test runner     |

---

## 📊 Tech Stack Stats

| Metric                        | Value              |
|-------------------------------|--------------------|
| Python dependencies (direct)  | 4                  |
| Python dependencies (total)   | ~9 (with transitive) |
| Frontend dependencies (CDN)   | 3                  |
| Database models               | 13                 |
| Templates                     | 26                 |
| Custom CSS lines              | ~633               |
| Custom JS lines               | ~621               |
| Backend code lines            | ~2,157             |
| API endpoints                 | 4                  |
| Total routes                  | 40+                |
| Build tools                   | None (zero-config) |
| Node.js / npm                 | Not used           |

---

*Last updated: March 2026*
