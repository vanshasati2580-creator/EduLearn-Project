# EduLearn: A Full-Stack E-Learning Platform with Gamification, Adaptive Content Enrichment, and AI-Assisted Pedagogy

## Project Thesis Summary

**Authors:** Aryan Sanjay Kalmegh, Rahul Kumar Tiwari, Sumit S Khandare, Vansh Asati, Shivam Deshmukh, Snehal Mohod

**Date:** March 2026

---

## Abstract

EduLearn is a comprehensive, full-stack web-based Learning Management System (LMS) designed and developed to simulate a production-grade e-learning environment. The platform integrates course management, video-based instruction, interactive assessments, a gamification engine, e-commerce functionality, an attendance system, and an AI-powered study assistant within a unified, server-side rendered (SSR) architecture. Built with the Flask micro-framework, SQLAlchemy ORM, and SQLite, the system demonstrates how modern web technologies can be leveraged to deliver a scalable, feature-complete educational platform. A key innovation is the **Content Enrichment Engine** — an idempotent, rule-based pipeline that automatically generates structured syllabi, lesson content, topic-aligned assessments, and resolves multimedia resources through a multi-tier fallback mechanism. The gamification subsystem rewards learner engagement through experience points (XP), achievement badges, and competitive leaderboards, drawing from established motivational design frameworks. The platform encompasses **14 relational database models**, over **40 RESTful routes**, **37 server-rendered templates**, and a rich client-side interaction layer featuring glassmorphism design, dark/light theming, scroll-driven animations, and A/B testing instrumentation.

**Keywords:** Learning Management System, E-Learning, Flask, Gamification, Content Enrichment, Web Application, Role-Based Access Control, Educational Technology, AI-Assisted Learning

---

## 1. Introduction

### 1.1 Background and Motivation

The global e-learning market continues to experience exponential growth, driven by the increasing demand for accessible, flexible, and personalized education. Modern learners expect platforms that combine rich multimedia content, interactive assessments, social learning features, and motivational mechanisms within a seamless digital experience. However, many existing systems either lack comprehensive feature integration or impose prohibitive licensing costs, creating a need for open, extensible, and well-architected educational platforms.

### 1.2 Problem Statement

Despite the rapid advancement of web technologies, building a cohesive e-learning platform that integrates video-based lessons, interactive quizzes, gamification, e-commerce, and artificial intelligence remains a significant engineering challenge. Most open-source LMS solutions lack:

- **Automated Content Generation** — Manual content creation is time-consuming and error‑prone.
- **Gamification Integration** — Engagement-boosting mechanics are typically afterthoughts.
- **AI-Assisted Pedagogy** — Personalized learning support powered by generative AI.
- **Modern UX Design** — Premium, animated, and accessible user interfaces.

EduLearn addresses all four gaps within a single, cohesive architecture.

### 1.3 Objectives

1. To design and implement a **multi-role, full-stack LMS** supporting the complete lifecycle of online education — from course creation and content delivery to assessment, certification, and revenue analytics.
2. To develop an **automated Content Enrichment Engine** capable of generating structured course content, resolving multimedia resources, and producing domain-specific assessments without manual intervention.
3. To integrate a **gamification framework** employing experience points, badges, and leaderboards to enhance learner motivation and engagement.
4. To deploy a **Gemini-powered AI Study Buddy** for conversational tutoring and an AI-based refresher system for struggling students.
5. To deliver a **premium user experience** through modern frontend design patterns including glassmorphism, responsive theming, micro-animations, and accessibility compliance.

### 1.4 Scope

EduLearn is designed as a demonstrative full-stack application encompassing 10+ courses across diverse domains including Python, Data Science, Machine Learning, Cybersecurity, Cloud Computing, UI/UX Design, Digital Marketing, Finance, English Communication, and Personal Productivity. The platform supports real-time student progress tracking, attendance management, a multi-course shopping cart with coupon-based discounts, mock payment processing with Luhn algorithm validation, and automated certificate generation upon course completion.

---

## 2. System Architecture

### 2.1 Architectural Overview

EduLearn follows a **monolithic server-side rendered (SSR) architecture** using the Flask WSGI micro‑framework. The system adopts the Model-View-Controller (MVC) paradigm, where SQLAlchemy declarative models define the data layer, Jinja2 templates handle presentation, and Flask route handlers serve as controllers.

| Layer            | Technology               | Role                                      |
|------------------|--------------------------|-------------------------------------------|
| Application      | Flask 2.3.3 (Python 3.10+) | HTTP routing, business logic, API layer |
| ORM              | Flask-SQLAlchemy 3.1.1   | Object-relational mapping, query building |
| Database         | SQLite 3                 | Persistent relational data storage        |
| Authentication   | Flask-Login 0.6.3        | Session management, user identity         |
| Security         | Werkzeug 3.0.3           | Password hashing (PBKDF2-SHA256), file safety |
| AI Integration   | Google Gemini (gemini‑2.5‑flash) | Study buddy, quiz generation, refreshers |
| Templating       | Jinja2                   | Server-side HTML rendering                |
| Frontend         | Bootstrap 5.3.2 + Vanilla CSS/JS | Responsive UI, interactions        |
| Typography       | Google Fonts (Inter, Playfair Display) | Visual hierarchy, readability |

### 2.2 Project Structure

```
EduLearn/
├── app.py                    # Main application (~2,590 lines)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (API keys)
├── theme_config.json         # Active theme configuration
├── instance/
│   └── edulearn_full.db      # SQLite database (auto-created)
├── static/
│   ├── css/style.css         # Global stylesheet (~29 KB)
│   ├── js/app.js             # Client-side JavaScript (~26 KB)
│   ├── data/                 # JSON config: video channels, topics, cache
│   └── uploads/              # User-uploaded files
├── templates/                # 37 Jinja2 HTML templates
│   ├── base.html             # Master layout (navbar, footer, chatbot)
│   ├── index.html            # Homepage (hero, trending, testimonials)
│   ├── course_detail.html    # Feature-rich course landing page (~22 KB)
│   ├── lesson.html           # Video player + code sandbox + notes
│   ├── instructor_*.html     # Instructor management suite
│   ├── admin_*.html          # Admin management suite
│   └── ...                   # Auth pages, dashboard, quiz, cart, etc.
├── tests/
│   ├── test_features.py      # Feature tests (7 test cases)
│   ├── test_course_page_ui.py # UI tests for course pages
│   └── test_about_page.py   # About page tests
└── uploads/                  # Additional uploads directory
```

### 2.3 Data Model

The relational schema comprises **14 interconnected models** that capture the full domain of an e-learning ecosystem:

| Entity           | Purpose                                           | Key Fields                                             |
|------------------|---------------------------------------------------|--------------------------------------------------------|
| `User`           | User accounts (student/instructor/admin)          | `name`, `email`, `password_hash`, `role`, `xp`, `department`, `verification_doc_url` |
| `Course`         | Courses with metadata                             | `title`, `short_desc`, `long_desc`, `thumbnail`, `instructor` |
| `Lesson`         | Individual lessons within courses                 | `course_id`, `title`, `content` (HTML), `video_url`, `position` |
| `Quiz`           | Quizzes per course                                | `course_id`, `title`                                   |
| `Question`       | MCQ questions (4 options, A–D)                    | `quiz_id`, `text`, `option_a`–`option_d`, `correct`   |
| `Enrollment`     | Student-course enrollment records                 | `student_id`, `course_id`, `progress`, `created_at`   |
| `Discussion`     | Course discussion forum posts                     | `course_id`, `author`, `content`, `created_at`         |
| `Review`         | Course ratings & comments (1–5 stars)             | `course_id`, `user_id`, `rating`, `comment`            |
| `Favorite`       | Wishlist items (unique per user+course)            | `user_id`, `course_id`                                 |
| `Coupon`         | Discount coupons (percent or fixed amount)         | `code`, `percent_off`, `amount_off_cents`, `active`    |
| `Note`           | Timestamped student notes on lessons               | `user_id`, `lesson_id`, `timestamp_seconds`, `text`   |
| `Badge`          | Achievement badge definitions                      | `name`, `description`, `icon`, `xp_bonus`              |
| `UserBadge`      | Earned badges (many-to-many join)                  | `user_id`, `badge_id`, `earned_at`                     |
| `QuizAttempt`    | Tracks quiz scores and pass/fail status            | `user_id`, `quiz_id`, `score`, `total`, `passed`       |
| `RefresherSuggestion` | AI-generated refresher content for failed quizzes | `attempt_id`, `content`, `videos`                |
| `Attendance`     | Student attendance records per course per date     | `student_id`, `course_id`, `date`, `status`            |

**Entity-Relationship Diagram:**

```
User ──┬── Enrollment ──── Course ──┬── Lesson ──── Note
       ├── UserBadge ──── Badge     ├── Quiz ──── Question
       ├── Review                   ├── Discussion
       ├── Favorite                 └── (Coupon — standalone)
       ├── Note
       ├── QuizAttempt ──── RefresherSuggestion
       └── Attendance ──── Course
```

---

## 3. Role-Based Access Control (RBAC)

The system implements a hierarchical three-tier RBAC model enforced through custom Python decorators:

| Role               | Permissions                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Student**        | Browse catalog, enroll, watch lessons, take quizzes, earn XP/badges, post reviews/discussions, manage wishlist & cart, view attendance |
| **Instructor**     | All Student permissions + create/manage own courses, lessons, and quizzes; view enrollment analytics and revenue reports; mark student attendance |
| **Pending Instructor** | Limited access during verification; must submit department & verification documents for admin approval |
| **Admin**          | All Instructor permissions + manage all users (role changes, deletion), manage all courses, approve/reject instructor applications, view global attendance reports, manage site theme |

Access control is enforced at the route level via three custom decorators: `@login_required`, `@instructor_required`, and `@admin_required`.

---

## 4. Feature Description

### 4.1 Course Discovery and Catalog Management

The homepage implements an intelligent course discovery system:
- **Trending Courses**: Top 6 courses ranked by aggregate enrollment count, with fallback to most recent courses.
- **New & Noteworthy**: Six most recently created courses, displayed chronologically.
- **Continue Learning**: For authenticated users, the 3 most recently enrolled courses with real-time progress percentages.
- **Featured Instructors**: Top 3 instructors ranked by total enrollments.
- **Full-Text Search**: Multi-field search across titles, descriptions using case-insensitive pattern matching (`ILIKE`).
- **Wishlist / Favorites**: Toggle courses in a personal wishlist.

### 4.2 Course Detail and Content Delivery

Each course presents a comprehensive detail page including:
- **Structured Curriculum**: Accordion-based syllabus with completion checkmarks.
- **Preview Video**: Auto-resolved from the first lesson's video URL.
- **Social Proof Metrics**: Enrollment count, average star rating with breakdown histogram, featured testimonials.
- **Related Courses**: Up to 6 courses, prioritizing co-instructor courses.
- **Canonical URL**: SEO-oriented canonical URL injection.

### 4.3 Video-Based Lesson Delivery

- **YouTube Embed System**: `normalize_to_embed()` function converts diverse YouTube URL formats (watch, shorts, youtu.be, existing embed) into consistent embed URLs.
- **Progress Tracking**: Forward-only progress that records highest lesson position reached.
- **Timestamped Notes**: JSON API for saving and deleting notes tied to specific video timestamps.
- **Code Sandbox**: Integrated Ace Editor for programming courses with language auto-detection based on course category.

### 4.4 Assessment Framework

- **Multiple-Choice Quizzes**: 4-option MCQ with single correct answer.
- **Instant Scoring**: Server-side evaluation with immediate feedback.
- **AI Mock Tests**: Gemini-powered dynamic quiz generation from lesson content.
- **AI Refresher System**: When a student fails a quiz, Gemini generates personalized study material explaining the concepts they struggled with.
- **Flashcard API**: Auto-generates flashcards from quiz question/answer pairs.

### 4.5 Gamification Engine

#### 4.5.1 Experience Points (XP)

| Trigger                     | XP Awarded |
|-----------------------------|------------|
| New lesson completed        | +10 XP     |
| Quiz passed (≥50%)         | +20 XP     |
| Perfect quiz score          | +100 XP    |
| First Step badge            | +50 XP     |
| Quiz Master badge           | +100 XP    |
| Night Owl badge             | +50 XP     |
| Dedicated Learner badge     | +500 XP    |

#### 4.5.2 Achievement Badges

| Badge             | Trigger Condition                       |
|-------------------|-----------------------------------------|
| First Step        | Complete the first lesson in any course |
| Quiz Master       | Achieve 100% on any quiz               |
| Night Owl         | Access a lesson between 00:00–04:00 UTC |
| Dedicated Learner | Complete all lessons in a course        |

Badge awards are **idempotent** — the system prevents duplicate awards.

#### 4.5.3 Leaderboard

A public leaderboard ranks the top 20 students by cumulative XP.

### 4.6 E-Commerce Module

- **Tiered Pricing**: Deterministic pricing based on course ID ($49, $59, or $79).
- **Shopping Cart**: Session-based multi-course cart with add/remove operations.
- **Coupon System**: Supports percentage and fixed-amount discounts with expiry and usage limits.
- **Mock Checkout**: Luhn algorithm-based credit card validation with real-time input formatting (card number, expiry, CVV).
- **Enrollment Protection**: Direct enrollment is blocked for paid courses; users must go through checkout.

### 4.7 Certification System

Certificates are auto-generated upon 100% course completion with:
- Unique ID format: `CERT-{course_id}-{user_id}-{YYYYMMDD}`
- Student name, course title, and completion date.

### 4.8 Attendance System

- **Instructor View**: Mark daily attendance (Present/Absent/Late) for enrolled students.
- **Attendance History**: Per-course historical view grouped by date.
- **Student Dashboard**: Personal attendance percentage per course with threshold warnings (default 75%).
- **Admin Report**: Platform-wide attendance analytics.

### 4.9 Instructor Verification System

- **Tiered Registration**: Instructors with `.edu` or `.ac.in` emails are auto-approved; others enter a `pending_instructor` state.
- **Onboarding Portal**: Pending instructors submit department info and verification documents.
- **Admin Approval/Rejection**: Admins review, approve, or reject with reason.
- **Secure File Upload**: Validation enforces allowed file extensions (PNG, JPG, JPEG, GIF, PDF).

### 4.10 AI-Powered Features (Google Gemini Integration)

| Feature               | Description                                             |
|-----------------------|---------------------------------------------------------|
| **AI Study Buddy**    | Course-aware chatbot using Gemini 2.5 Flash; answers questions based on lesson content (simplified RAG approach) |
| **AI Mock Tests**     | Generates 3 MCQ questions from lesson text on demand    |
| **AI Refresher**      | Generates personalized study material for failed quiz topics |
| **AI Quiz Generation**| Instructor-triggered quiz generation from course descriptions (mock fallback available) |

### 4.11 Theme System

Administrators can switch between 4 site-wide color themes:
- Ocean Blue, Emerald Green, Crimson Red, Sunset Orange

Theme preferences are stored in `theme_config.json` and injected via Jinja2 context processors.

---

## 5. Frontend Design and User Experience

### 5.1 Design Philosophy

The frontend implements a **premium glassmorphism design system**:
- Semi-transparent surfaces with `backdrop-filter: blur()` for depth perception.
- Dark-first design with a full light theme variant.
- CSS custom properties (design tokens) for consistent theming.
- Editorial typography: Inter (body) and Playfair Display (headings).

### 5.2 Micro-Interactions and Animations

| Feature                      | Technique                                         |
|------------------------------|---------------------------------------------------|
| Scroll-triggered reveals     | `IntersectionObserver` with threshold-based triggers |
| Button ripple effect         | Dynamic DOM creation + CSS keyframes              |
| Cursor-following spotlight   | Pointer tracking via CSS custom properties        |
| Scroll progress indicator    | `requestAnimationFrame`-driven transform scaling  |
| Parallax hero section        | Scroll-based `translateY` transforms              |
| Dark/Light theme toggle      | `localStorage` persistence + system preference    |
| Credit card input masking    | Real-time regex-based input formatting            |
| 3D card tilt                 | CSS `rotateX`/`rotateY` transforms on hover       |

### 5.3 Accessibility

- WAI-ARIA compliance: `aria-label`, `aria-controls`, `aria-pressed`, `aria-live`.
- `prefers-reduced-motion` media query disabling all animations.
- Focus-visible styling for keyboard navigation.
- Semantic HTML5 elements (`<main>`, `<nav>`, `<header>`, `<footer>`).

### 5.4 Analytics and A/B Testing

A lightweight analytics emitter tracks 20+ user interaction events via a `dataLayer`-compatible interface. Two A/B test variants are instrumented for CTA styling and hero layout.

---

## 6. Security Measures

| Measure                      | Implementation                                    |
|------------------------------|---------------------------------------------------|
| Password storage             | PBKDF2-SHA256 via Werkzeug                        |
| Session security             | Flask secret-key signed cookies                   |
| XSS prevention               | Jinja2 auto-escaping on all template outputs      |
| File upload validation       | Extension whitelist (`png`, `jpg`, `jpeg`, `gif`, `pdf`) + `secure_filename()` |
| Payment validation           | Luhn algorithm for card number verification       |
| Direct enrollment protection | Paid courses require checkout flow                |
| IDOR prevention              | Enrollment-gated APIs for flashcards; ownership checks on instructor routes |
| Role enforcement             | Server-side decorator-based access control        |
| Cascade deletion             | Proper cleanup of Reviews, Notes, Favorites, QuizAttempts on user deletion |

---

## 7. Content Enrichment Engine

The Content Enrichment Engine is a sophisticated, **idempotent** content generation pipeline that:

1. **Classifies Courses** into 11 domain categories using keyword-based heuristic matching on titles.
2. **Generates Rich Descriptions** from category-specific templates including syllabus highlights, learning outcomes, project descriptions, tools, and prerequisites.
3. **Creates Structured Lessons**: 8–12 lessons per course with HTML-formatted content.
4. **Resolves Video URLs** through a six-tier fallback:
   - Curated intro videos → Topic-specific mappings → Cached results → YouTube Data API → YouTube search embeds → Channel playlist fallback.
5. **Generates Topic-Aligned Quizzes** with a heuristic MCQ question bank covering 100+ unique questions.
6. **Upgrades Placeholder Content** by detecting and replacing generic quiz questions with domain-specific content.

**Idempotency Guarantees**: Safe to re-run; existing content is never duplicated; only placeholder content is upgraded.

---

## 8. Technology Stack Summary

| Component        | Technology            | Version / Size |
|------------------|-----------------------|----------------|
| Language         | Python                | 3.10+          |
| Web Framework    | Flask                 | 2.3.3          |
| ORM              | Flask-SQLAlchemy      | 3.1.1          |
| Authentication   | Flask-Login           | 0.6.3          |
| HTTP Utilities   | Werkzeug              | 3.0.3          |
| AI Integration   | Google Gemini (genai) | latest         |
| Env Management   | python-dotenv         | latest         |
| Database         | SQLite                | 3              |
| CSS Framework    | Bootstrap             | 5.3.2 (CDN)   |
| Custom CSS       | Vanilla CSS           | ~633 LOC       |
| Client JS        | Vanilla ES6+          | ~621 LOC       |
| Templating       | Jinja2                | Bundled        |
| Typography       | Google Fonts          | Inter + Playfair Display |
| Video Platform   | YouTube iframe embed  | —              |
| Testing          | pytest                | —              |

---

## 9. Quantitative Metrics

| Metric                      | Value              |
|-----------------------------|--------------------|
| Backend source lines        | ~2,590             |
| Custom CSS lines            | ~633               |
| Custom JavaScript lines     | ~621               |
| Database models             | 14+                |
| HTML templates              | 37                 |
| RESTful routes              | 40+                |
| API endpoints               | 5+                 |
| Pre-seeded courses          | 10                 |
| Quiz questions (generated)  | 100+               |
| Seeded discount coupons     | 3                  |
| Achievement badges          | 4                  |
| Python dependencies (direct)| 6                  |
| Frontend CDN dependencies   | 3                  |
| Build tools required        | None (zero-config) |

---

## 10. Testing

### 10.1 Test Framework

Tests are implemented using **pytest** and located in the `tests/` directory:

| Test File                 | Scope                                              |
|---------------------------|----------------------------------------------------|
| `test_features.py`       | Reviews, certificates, analytics, cart/checkout, registration, enrichment (7 test cases) |
| `test_course_page_ui.py` | Course detail page UI rendering and data presence  |
| `test_about_page.py`     | About page team member rendering                   |

### 10.2 Test Execution

```bash
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database with `StaticPool` connection management to ensure test isolation.

---

## 11. Setup and Reproduction

### Prerequisites

- Python 3.10 or higher

### Installation

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The application automatically:
1. Creates the SQLite database (`instance/edulearn_full.db`)
2. Seeds a default admin account
3. Populates 10 demonstration courses if none exist
4. Executes the Content Enrichment Engine

Access the platform at **http://127.0.0.1:5000**

### Default Credentials

| Role       | Email                     | Password   |
|------------|---------------------------|------------|
| Admin      | admin@edulearn.com        | admin123   |
| Instructor | instructor@edulearn.com   | password   |
| Student    | student@edulearn.com      | password   |

---

## 12. Results and Demonstration

The completed platform successfully demonstrates:

1. **End-to-end learner journey**: Registration → course discovery → enrollment (free or paid via cart/checkout) → video lessons with timestamped notes → code sandbox for programming courses → quizzes with AI refreshers → XP & badge awards → certificate generation.

2. **Instructor workflow**: Course creation with thumbnail upload → lesson management with YouTube auto-normalization → quiz CRUD → AI quiz generation → enrollment analytics with revenue projections → student attendance marking.

3. **Administrative oversight**: User management → role changes → instructor verification (approve/reject) → course oversight → global attendance reports → site theme management.

4. **Content automation**: The Content Enrichment Engine auto-populates 10+ courses with structured lessons, curated videos, and domain-specific quiz content across 11 subject categories.

5. **AI-powered learning**: Gemini integration provides course-aware chatbot tutoring, dynamic mock test generation, and personalized refresher content for struggling students.

---

## 13. Future Work

| Enhancement                  | Description                                              |
|------------------------------|----------------------------------------------------------|
| Real Payment Gateway         | Integrate Stripe or Razorpay for actual payment processing |
| PostgreSQL Migration         | Transition from SQLite for concurrent multi-user support |
| Video Analytics              | Watch-time tracking and engagement heatmaps             |
| Adaptive Learning Paths      | Performance-based personalized course recommendations   |
| Mobile Application           | React Native or Flutter companion app                    |
| Real-Time Notifications      | WebSocket-based push notifications                      |
| Multi-Language Support       | i18n/l10n for regional expansion                        |
| SCORM Compliance             | Interoperability with existing LMS ecosystems           |
| Advanced AI Features         | Assignment grading, plagiarism detection, adaptive quizzes |
| Database Migrations          | Flask-Migrate for schema evolution management           |

---

## 14. Conclusion

EduLearn successfully demonstrates that a feature-complete, aesthetically refined, and architecturally sound learning management system can be built using a lightweight Python web stack. The platform's **Content Enrichment Engine** proves the viability of automated, idempotent content generation for educational applications, while the **gamification subsystem** implements established motivational design patterns to drive learner engagement. The **Gemini AI integration** establishes practical pathways for conversational tutoring and adaptive assessment. With approximately 2,590 lines of backend code, 14+ database models, 37 templates, and 40+ routes, EduLearn serves as both a practical educational tool and a comprehensive reference implementation for full-stack web application development.

---

## 15. References

1. Grinberg, M. (2018). *Flask Web Development: Developing Web Applications with Python* (2nd ed.). O'Reilly Media.
2. Deterding, S., Dixon, D., Khaled, R., & Nacke, L. (2011). From Game Design Elements to Gamefulness: Defining "Gamification." *Proceedings of the 15th International Academic MindTrek Conference*, 9–15.
3. Dicheva, D., Dichev, C., Agre, G., & Angelova, G. (2015). Gamification in Education: A Systematic Mapping Study. *Educational Technology & Society*, 18(3), 75–88.
4. Pallets Projects. (2023). Flask Documentation (Version 2.3.x). https://flask.palletsprojects.com/
5. SQLAlchemy Authors. (2023). SQLAlchemy Documentation. https://docs.sqlalchemy.org/
6. Bootstrap Team. (2023). Bootstrap 5.3 Documentation. https://getbootstrap.com/docs/5.3/
7. Luhn, H.P. (1960). Computer for Verifying Numbers. US Patent 2,950,048.
8. W3C. (2023). WAI-ARIA Authoring Practices 1.2. https://www.w3.org/WAI/ARIA/apg/
9. Google. (2024). Gemini API Documentation. https://ai.google.dev/docs

---

## Appendix A: Team Members

| Name                   |
|------------------------|
| Aryan Sanjay Kalmegh   |
| Rahul Kumar Tiwari     |
| Sumit S Khandare       |
| Vansh Asati            |
| Shivam Deshmukh        |
| Snehal Mohod           |

---

## Appendix B: Database Schema Diagram

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│      User        │────→│  Enrollment  │←────│     Course      │
│─────────────────│     │──────────────│     │─────────────────│
│ id               │     │ id           │     │ id              │
│ name             │     │ student_id   │     │ title           │
│ email            │     │ course_id    │     │ short_desc      │
│ password_hash    │     │ progress     │     │ long_desc       │
│ role             │     │ created_at   │     │ thumbnail       │
│ department       │     └──────────────┘     │ instructor      │
│ verification_doc │                          └───────┬─────────┘
│ xp               │                                  │
└──────┬──────────┘                                  │
       │                                              ├──→ Lesson ←── Note
       ├──→ UserBadge ←── Badge                      ├──→ Quiz ──→ Question
       ├──→ Review                                   ├──→ Discussion
       ├──→ Favorite                                 └──→ Attendance
       ├──→ Note
       └──→ QuizAttempt ──→ RefresherSuggestion

                     ┌─────────────┐
                     │   Coupon     │  (standalone)
                     │─────────────│
                     │ code         │
                     │ percent_off  │
                     │ amount_off   │
                     │ active       │
                     │ expires_at   │
                     │ max_uses     │
                     └─────────────┘
```

---

## Appendix C: Complete Route Map

### Public Routes
| Route              | Method   | Description          |
|--------------------|----------|----------------------|
| `/`                | GET      | Homepage             |
| `/about`           | GET      | About / Team page    |
| `/register`        | GET/POST | User registration    |
| `/login`           | GET/POST | User login           |
| `/logout`          | GET      | Logout               |
| `/course/<cid>`    | GET      | Course detail page   |
| `/search`          | GET      | Search courses       |
| `/leaderboard`     | GET      | XP leaderboard       |

### Student Routes (login required)
| Route                       | Method   | Description               |
|-----------------------------|----------|---------------------------|
| `/dashboard`                | GET      | Student dashboard         |
| `/enroll/<cid>`             | POST     | Enroll in a course        |
| `/lesson/<lid>`             | GET      | View a lesson             |
| `/lesson/<lid>/mock-test`   | GET      | AI-generated mock test    |
| `/quiz/<qid>`               | GET      | View a quiz               |
| `/quiz/<qid>/submit`        | POST     | Submit quiz answers       |
| `/refresher/<rid>`          | GET      | View AI refresher         |
| `/checkout/<cid>`           | GET/POST | Checkout page             |
| `/course/<cid>/discuss`     | POST     | Post a discussion         |
| `/course/<cid>/review`      | POST     | Submit/update a review    |
| `/favorite/<cid>/toggle`    | POST     | Toggle wishlist           |
| `/wishlist`                 | GET      | View wishlist             |
| `/cart`                     | GET      | View cart                 |
| `/cart/checkout`            | POST     | Cart checkout             |
| `/certificate/<cid>`        | GET      | Completion certificate    |
| `/student/attendance`       | GET      | View attendance records   |

### API Endpoints
| Route                       | Method | Description                |
|-----------------------------|--------|----------------------------|
| `/api/note/save`            | POST   | Save timestamped note      |
| `/api/note/delete/<nid>`    | POST   | Delete a note              |
| `/api/flashcards/<cid>`     | GET    | Get flashcards (enrolled)  |
| `/api/chat/<cid>`           | POST   | AI Study Buddy chatbot     |

### Instructor Routes
| Route                                        | Method   | Description           |
|----------------------------------------------|----------|-----------------------|
| `/instructor/onboarding`                     | GET/POST | Verification portal   |
| `/instructor/courses`                        | GET      | List own courses      |
| `/instructor/courses/new`                    | GET/POST | Create a course       |
| `/instructor/courses/<cid>/edit`             | GET/POST | Edit a course         |
| `/instructor/courses/<cid>/delete`           | POST     | Delete a course       |
| `/instructor/courses/<cid>/lessons`          | GET      | List lessons          |
| `/instructor/courses/<cid>/lessons/new`      | GET/POST | Add a lesson          |
| `/instructor/analytics`                      | GET      | Revenue & stats       |
| `/instructor/attendance`                     | GET      | Attendance portal     |
| `/instructor/courses/<cid>/attendance`       | GET/POST | Mark attendance       |
| `/instructor/course/<cid>/ai-generate-quiz`  | POST     | AI quiz generation    |

### Admin Routes
| Route                          | Method | Description              |
|--------------------------------|--------|--------------------------|
| `/admin/users`                 | GET    | List all users           |
| `/admin/users/<uid>/role`      | POST   | Change user role         |
| `/admin/users/<uid>/delete`    | POST   | Delete a user            |
| `/admin/courses`               | GET    | List all courses         |
| `/admin/approvals`             | GET    | Pending instructor list  |
| `/admin/approvals/<uid>/approve` | POST | Approve instructor     |
| `/admin/approvals/<uid>/reject`| POST   | Reject instructor        |
| `/admin/theme`                 | GET/POST | Manage site theme      |
| `/admin/attendance/report`     | GET    | Global attendance report |

---

*Thesis summary prepared: March 2026*
