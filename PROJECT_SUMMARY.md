# 📚 EduLearn — Full-Stack Online Learning Platform

> A feature-rich, full-stack e-learning web application built with **Flask**, **SQLAlchemy**, and **SQLite**, featuring course management, video lessons, quizzes, gamification, payments, and an AI assistant.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Tech Stack](#-tech-stack)
3. [Project Structure](#-project-structure)
4. [Database Models](#-database-models)
5. [Features & Modules](#-features--modules)
6. [User Roles & Permissions](#-user-roles--permissions)
7. [Routes & API Endpoints](#-routes--api-endpoints)
8. [Content Enrichment Engine](#-content-enrichment-engine)
9. [Gamification System](#-gamification-system)
10. [AI Features (Mock)](#-ai-features-mock)
11. [Default Credentials](#-default-credentials)
12. [Setup & Running](#-setup--running)
13. [Testing](#-testing)
14. [Team](#-team)

---

## 🔎 Project Overview

**EduLearn** is a comprehensive online learning platform that simulates a production-grade e-learning system. It supports multiple user roles (Student, Instructor, Admin), course creation and management, video-based lessons with embedded YouTube players, interactive quizzes, a shopping cart with coupon support, a mock checkout with Luhn-validated credit cards, a gamification/badge system, leaderboards, certificates, discussion forums, course reviews, wishlists, timestamped notes, flashcards, and an AI chatbot assistant.

The application auto-seeds itself with **10 demo courses** spanning topics like Python, Data Science, Machine Learning, Cybersecurity, Cloud Computing, UI/UX, and more — each enriched with detailed syllabi, lessons, quizzes, and curated YouTube video embeds.

---

## 🛠 Tech Stack

| Layer         | Technology                                                     |
|---------------|----------------------------------------------------------------|
| **Backend**   | Python 3, Flask 2.3.3, Flask-Login 0.6.3, Flask-SQLAlchemy 3.1.1 |
| **Database**  | SQLite (via SQLAlchemy ORM)                                    |
| **Frontend**  | Jinja2 templates, HTML5, Vanilla CSS, Vanilla JavaScript       |
| **Auth**      | Werkzeug password hashing, Flask-Login session management      |
| **Video**     | YouTube embed (iframe), curated/search-based video resolution  |
| **Icons**     | Font Awesome                                                   |
| **Images**    | Unsplash (course thumbnails)                                   |

---

## 📁 Project Structure

```
EduLearn_Full/
├── app.py                    # Main application (routes, models, enrichment — 2157 lines)
├── requirements.txt          # Python dependencies
├── check_videos.py           # Utility script to verify video URLs
├── README.md                 # Original readme
├── instance/
│   └── edulearn_full.db      # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css         # Global stylesheet (29 KB)
│   ├── js/
│   │   └── app.js            # Client-side JavaScript (26 KB)
│   ├── data/
│   │   ├── video_channels.json       # YouTube channel IDs per category
│   │   ├── video_topics_map.json     # Topic → YouTube embed URL mappings
│   │   ├── video_curated_intro.json  # Curated intro video URLs per category
│   │   └── video_cache.json          # Runtime cache for API/search results
│   └── uploads/              # User-uploaded course thumbnail images
├── templates/                # 26 Jinja2 HTML templates
│   ├── base.html             # Base layout (navbar, flash messages, footer)
│   ├── index.html            # Homepage (trending, new, continue learning)
│   ├── login.html / register.html
│   ├── dashboard.html        # Student dashboard
│   ├── course_detail.html    # Course landing page (22 KB — feature-rich)
│   ├── lesson.html           # Video lesson player with notes
│   ├── quiz.html             # Quiz taking interface
│   ├── checkout.html / cart.html
│   ├── certificate.html      # Completion certificate
│   ├── search.html / wishlist.html
│   ├── leaderboard.html      # XP-based leaderboard
│   ├── about.html            # Team page
│   ├── admin_users.html / admin_courses.html
│   ├── instructor_*.html     # 7 instructor management templates
│   └── ...
├── tests/
│   ├── test_features.py      # Feature tests
│   ├── test_course_page_ui.py # UI tests for course pages
│   └── test_about_page.py    # About page tests
└── uploads/                  # Additional uploads directory
```

---

## 🗄 Database Models

The application defines **13 database models** using SQLAlchemy:

| Model          | Purpose                                          | Key Fields                                                 |
|----------------|--------------------------------------------------|------------------------------------------------------------|
| `User`         | User accounts (student/instructor/admin)         | `name`, `email`, `password_hash`, `role`, `xp`             |
| `Course`       | Courses with metadata                            | `title`, `short_desc`, `long_desc`, `thumbnail`, `instructor` |
| `Lesson`       | Individual lessons within courses                | `course_id`, `title`, `content` (HTML), `video_url`, `position` |
| `Quiz`         | Quizzes per course                               | `course_id`, `title`                                       |
| `Question`     | MCQ questions (4 options, A–D)                   | `quiz_id`, `text`, `option_a`–`option_d`, `correct`        |
| `Enrollment`   | Student-course enrollment records                | `student_id`, `course_id`, `progress`, `created_at`        |
| `Discussion`   | Course discussion forum posts                    | `course_id`, `author`, `content`, `created_at`             |
| `Review`       | Course ratings & comments (1–5 stars)            | `course_id`, `user_id`, `rating`, `comment`                |
| `Favorite`     | Wishlist items (unique per user+course)           | `user_id`, `course_id`                                     |
| `Coupon`       | Discount coupons (percent or fixed amount)       | `code`, `percent_off`, `amount_off_cents`, `active`, `expires_at`, `max_uses` |
| `Note`         | Timestamped student notes on lessons             | `user_id`, `lesson_id`, `timestamp_seconds`, `text`        |
| `Badge`        | Achievement badges definition                   | `name`, `description`, `icon`, `xp_bonus`                  |
| `UserBadge`    | Earned badges (many-to-many join)                | `user_id`, `badge_id`, `earned_at`                         |

### Entity Relationships

```
User ──┬── Enrollment ──── Course ──┬── Lesson
       ├── UserBadge ──── Badge     ├── Quiz ──── Question
       ├── Review                   ├── Discussion
       ├── Favorite                 └── (Coupon — standalone)
       └── Note ──── Lesson
```

---

## ✨ Features & Modules

### 🎓 Student Features
- **Course Catalog** — Browse, search, and filter courses on the homepage
- **Trending & New Courses** — Auto-ranked by enrollment count
- **Continue Learning** — Resume from last enrolled courses
- **Course Detail Page** — Full syllabus, preview video, reviews, curriculum with progress checkmarks, related courses, social proof (enrollment count)
- **Video Lessons** — Embedded YouTube player with lesson navigation sidebar
- **Timestamped Notes** — Save notes tied to video timestamps; create/delete via API
- **Flashcards** — Auto-generated from quiz questions (API endpoint)
- **Quizzes** — Multiple-choice with instant scoring
- **Discussion Forum** — Post comments on each course
- **Reviews & Ratings** — 1–5 star reviews with breakdown chart
- **Wishlist / Favorites** — Save courses for later
- **Shopping Cart** — Multi-course cart with coupon support
- **Checkout** — Mock payment with Luhn credit card validation and coupon discounts
- **Certificates** — Auto-generated on 100% course completion
- **Leaderboard** — XP-based ranking of top students
- **AI Chatbot** — Mock conversational assistant

### 👩‍🏫 Instructor Features
- **Course Management** — Create, edit, and delete owned courses
- **Lesson Management** — Add/edit/delete lessons with video URLs (auto-normalized to YouTube embeds)
- **Quiz Management** — Create quizzes, add/edit/delete MCQ questions
- **AI Quiz Generation** — Mock AI-powered quiz generation from course content
- **Analytics Dashboard** — View enrollment counts and estimated revenue per course
- **Thumbnail Upload** — Upload images or provide URLs for course thumbnails

### 🛡 Admin Features
- **User Management** — View all users, change roles, delete users
- **Course Management** — View and manage all courses
- **Protected Admin** — Default admin account cannot be deleted

---

## 👥 User Roles & Permissions

| Role          | Capabilities                                                            |
|---------------|-------------------------------------------------------------------------|
| **Student**   | Browse, enroll, watch lessons, take quizzes, earn XP/badges, post reviews, manage wishlist & cart |
| **Instructor**| All student capabilities + create/manage own courses, lessons, quizzes, view analytics |
| **Admin**     | All instructor capabilities + manage all users (role changes, deletion), manage all courses |

Access control is enforced via `@login_required`, `@admin_required`, and `@instructor_required` decorators.

---

## 🌐 Routes & API Endpoints

### Public Routes
| Route                        | Method | Description                    |
|------------------------------|--------|--------------------------------|
| `/`                          | GET    | Homepage                       |
| `/about`                     | GET    | About / team page              |
| `/register`                  | GET/POST | User registration            |
| `/login`                     | GET/POST | User login                   |
| `/logout`                    | GET    | Logout                         |
| `/course/<cid>`              | GET    | Course detail page             |
| `/search`                    | GET    | Search courses                 |
| `/leaderboard`               | GET    | XP leaderboard                 |

### Student Routes (login required)
| Route                             | Method | Description                     |
|-----------------------------------|--------|---------------------------------|
| `/dashboard`                      | GET    | Student dashboard               |
| `/enroll/<cid>`                   | POST   | Enroll in a course              |
| `/lesson/<lid>`                   | GET    | View a lesson                   |
| `/quiz/<qid>`                     | GET    | View a quiz                     |
| `/quiz/<qid>/submit`             | POST   | Submit quiz answers             |
| `/checkout/<cid>`                 | GET/POST | Checkout page                 |
| `/course/<cid>/discuss`           | POST   | Post a discussion               |
| `/course/<cid>/review`            | POST   | Submit/update a review          |
| `/favorite/<cid>/toggle`          | POST   | Toggle wishlist                 |
| `/wishlist`                       | GET    | View wishlist                   |
| `/cart` / `/cart/add` / `/cart/remove` | Various | Shopping cart operations   |
| `/cart/checkout`                  | POST   | Cart checkout                   |
| `/certificate/<cid>`             | GET    | View completion certificate     |

### API Endpoints
| Route                             | Method | Description                     |
|-----------------------------------|--------|---------------------------------|
| `/api/note/save`                  | POST   | Save a timestamped note (JSON)  |
| `/api/note/delete/<nid>`          | POST   | Delete a note                   |
| `/api/flashcards/<cid>`           | GET    | Get flashcards for a course     |
| `/api/chat`                       | POST   | AI chatbot endpoint (JSON)      |

### Instructor Routes
| Route                                              | Method   | Description                |
|----------------------------------------------------|----------|----------------------------|
| `/instructor/courses`                              | GET      | List own courses           |
| `/instructor/courses/new`                          | GET/POST | Create a course            |
| `/instructor/courses/<cid>/edit`                   | GET/POST | Edit a course              |
| `/instructor/courses/<cid>/delete`                 | POST     | Delete a course            |
| `/instructor/courses/<cid>/lessons`                | GET      | List lessons               |
| `/instructor/courses/<cid>/lessons/new`            | GET/POST | Add a lesson               |
| `/instructor/lessons/<lid>/edit`                   | GET/POST | Edit a lesson              |
| `/instructor/lessons/<lid>/delete`                 | POST     | Delete a lesson            |
| `/instructor/courses/<cid>/quizzes`                | GET      | List quizzes               |
| `/instructor/courses/<cid>/quizzes/new`            | GET/POST | Create a quiz              |
| `/instructor/quizzes/<qid>/edit`                   | GET/POST | Edit a quiz                |
| `/instructor/quizzes/<qid>/delete`                 | POST     | Delete a quiz              |
| `/instructor/quizzes/<qid>/questions`              | GET      | List questions             |
| `/instructor/quizzes/<qid>/questions/new`          | GET/POST | Add a question             |
| `/instructor/questions/<quesid>/edit`              | GET/POST | Edit a question            |
| `/instructor/questions/<quesid>/delete`            | POST     | Delete a question          |
| `/instructor/course/<cid>/ai-generate-quiz`        | POST     | AI-generate a quiz         |
| `/instructor/analytics`                            | GET      | Revenue & enrollment stats |

### Admin Routes
| Route                          | Method | Description           |
|--------------------------------|--------|-----------------------|
| `/admin/users`                 | GET    | List all users        |
| `/admin/users/<uid>/role`      | POST   | Change user role      |
| `/admin/users/<uid>/delete`    | POST   | Delete a user         |
| `/admin/courses`               | GET    | List all courses      |

### CLI Commands
| Command          | Description                                    |
|------------------|------------------------------------------------|
| `flask initdb`   | Initialize the database                        |
| `flask seed`     | Seed demo data (users, courses, badges, coupons) |
| `flask enrich`   | Run content enrichment on all courses          |

---

## 🔄 Content Enrichment Engine

The `enrich_courses()` function is a sophisticated, **idempotent** content generation system that runs on startup and on first request. It:

1. **Classifies courses** into categories (fullstack, python, datasci, ml, security, cloud, uiux, marketing, finance, english, productivity) using keyword matching on titles
2. **Generates rich long descriptions** from category-specific templates including syllabus highlights, learning outcomes, project descriptions, tools, and prerequisites
3. **Creates lessons** aligned to predefined module syllabi (8–12 lessons per course) with HTML content
4. **Resolves video URLs** through a multi-tier fallback system:
   - Curated intro videos for first lessons
   - Topic-specific mappings from `video_topics_map.json`
   - Cached API/search results from `video_cache.json`
   - YouTube Data API (if `YOUTUBE_API_KEY` is configured)
   - YouTube search embeds
   - Channel playlist fallback from `video_channels.json`
5. **Generates topic-aligned quizzes** with heuristic MCQ question banks covering 100+ unique questions across Python, Data Science, ML, and other domains
6. **Upgrades placeholder quizzes** to subject-specific content (idempotent — only replaces generic "concept check" placeholders)

---

## 🏆 Gamification System

| Badge              | Condition                           | XP Bonus |
|--------------------|-------------------------------------|----------|
| **First Step**     | Complete your first lesson          | 50 XP    |
| **Quiz Master**    | Score 100% on any quiz              | 100 XP   |
| **Night Owl**      | Study between 12 AM and 4 AM (UTC) | 50 XP    |
| **Dedicated Learner** | Complete an entire course        | 500 XP   |

Additional XP rewards:
- **+10 XP** per new lesson completed
- **+100 XP** for a perfect quiz score
- **+20 XP** for passing a quiz (≥ 50%)

The **Leaderboard** ranks the top 20 students by total XP.

---

## 🤖 AI Features (Mock)

The `MockAIService` class provides two simulated AI capabilities:

- **Quiz Generation** — Generates 5 MCQ questions from course content (deterministic mock)
- **Chat Assistant** — Keyword-based chatbot responding to greetings, explanations, quiz queries, and Python questions

These are designed as placeholder integrations ready to be connected to real LLM APIs.

---

## 🔑 Default Credentials

| Role       | Email                      | Password    |
|------------|----------------------------|-------------|
| Admin      | `admin@edulearn.com`       | `admin123`  |
| Instructor | `instructor@edulearn.com`  | `password`  |
| Student    | `student@edulearn.com`     | `password`  |

> ⚠️ These are seeded via `flask seed` or on first startup.

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.10+

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The server starts at **http://127.0.0.1:5000** with debug mode enabled.

On first startup, the app automatically:
1. Creates the SQLite database (`instance/edulearn_full.db`)
2. Creates a default admin account
3. Seeds 10 demo courses if none exist
4. Runs the content enrichment engine

### Optional Seeding

```bash
flask seed    # Full seed: users, courses, coupons, badges
flask enrich  # Re-run content enrichment
flask initdb  # Initialize DB schema only
```

### Optional Configuration

Set `YOUTUBE_API_KEY` as an environment variable to enable real YouTube video search for lesson content.

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Individual test files
python -m pytest tests/test_features.py
python -m pytest tests/test_course_page_ui.py
python -m pytest tests/test_about_page.py
```

---

## 👨‍💻 Team

| Name                   |
|------------------------|
| Aryan Sanjay Kalmegh   |
| Rahul Kumar Tiwari     |
| Sumit S Khandare       |
| Vansh Asati            |
| Shivam Deshmukh        |
| Snehal Mohod           |

---

## 📊 Project Stats

| Metric               | Value       |
|----------------------|-------------|
| Total Lines of Code  | ~2,157 (app.py) + ~29 KB CSS + ~26 KB JS |
| Database Models      | 13          |
| Templates            | 26          |
| Routes               | 40+         |
| Demo Courses         | 10          |
| Quiz Questions       | 100+        |
| Coupons (Seeded)     | 3 (SAVE10, HALF, WELCOME5) |
