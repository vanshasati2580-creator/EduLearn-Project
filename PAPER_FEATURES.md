# EduLearn: A Feature-Rich Full-Stack Online Learning Platform with Gamification, Adaptive Content Enrichment, and AI-Assisted Pedagogy

**Authors:** Aryan Sanjay Kalmegh, Rahul Kumar Tiwari, Sumit S Khandare, Vansh Asati, Shivam Deshmukh, Snehal Mohod

---

## Abstract

This paper presents **EduLearn**, a comprehensive full-stack web-based learning management system (LMS) designed to simulate a production-grade e-learning environment. The platform integrates course management, video-based instruction, interactive assessments, a gamification engine, e-commerce functionality, and an AI-powered conversational assistant within a unified architecture. Built upon the Flask micro-framework with SQLAlchemy ORM and SQLite, EduLearn demonstrates how modern web technologies can be leveraged to deliver a scalable, feature-complete educational platform. The system supports three distinct user roles—Student, Instructor, and Administrator—each governed by role-based access control (RBAC). A key innovation is the **Content Enrichment Engine**, an idempotent, rule-based system that automatically generates structured syllabi, lesson content, topic-aligned assessments, and resolves multimedia resources through a multi-tier fallback mechanism. The gamification subsystem rewards learner engagement through experience points (XP), achievement badges, and competitive leaderboards, drawing from established motivational design frameworks. The platform encompasses 13 relational database models, over 40 RESTful routes, 26 server-rendered templates, and a rich client-side interaction layer featuring glassmorphism design, dark/light theming, scroll-driven animations, and A/B testing instrumentation.

**Keywords:** Learning Management System, E-Learning, Flask, Gamification, Content Enrichment, Web Application, Role-Based Access Control, Educational Technology

---

## 1. Introduction

### 1.1 Background and Motivation

The global e-learning market has witnessed exponential growth, driven by the increasing demand for accessible, flexible, and personalized education. Modern learners expect platforms that combine rich multimedia content, interactive assessments, social learning features, and motivational mechanisms within a seamless digital experience. However, many existing systems either lack comprehensive feature integration or impose prohibitive licensing costs, creating a need for open, extensible, and well-architected educational platforms.

### 1.2 Objectives

The primary objectives of the EduLearn platform are:

1. To design and implement a **multi-role, full-stack LMS** supporting the complete lifecycle of online education—from course creation and content delivery to assessment, certification, and revenue analytics.
2. To develop an **automated Content Enrichment Engine** capable of generating structured course content, resolving multimedia resources, and producing domain-specific assessments without manual intervention.
3. To integrate a **gamification framework** that employs experience points, badges, and leaderboards to enhance learner motivation and engagement.
4. To provide a **mock AI assistant** architecture demonstrating the integration pathway for conversational AI and automated quiz generation in educational contexts.
5. To deliver a **premium user experience** through modern frontend design patterns including glassmorphism, responsive theming, micro-animations, and accessibility compliance.

### 1.3 Scope

EduLearn is designed as a demonstrative full-stack application encompassing 10 pre-seeded courses across diverse domains including Python programming, Data Science, Machine Learning, Cybersecurity, Cloud Computing, and UI/UX Design. The platform supports real-time student progress tracking, multi-course shopping cart with coupon-based discounts, mock payment processing with industry-standard card validation, and automated certificate generation upon course completion.

---

## 2. System Architecture

### 2.1 Architectural Overview

EduLearn follows a **monolithic server-side rendered (SSR) architecture** built on the Flask WSGI micro-framework. The system employs the Model-View-Controller (MVC) paradigm, where SQLAlchemy declarative models define the data layer, Jinja2 templates handle presentation, and Flask route handlers serve as controllers.

**Table 1: Architectural Layer Summary**

| Layer            | Technology               | Role                                      |
|------------------|--------------------------|-------------------------------------------|
| Application      | Flask 2.3.3 (Python 3)   | HTTP routing, business logic, API layer   |
| ORM              | Flask-SQLAlchemy 3.1.1   | Object-relational mapping, query building |
| Database         | SQLite 3                 | Persistent relational data storage        |
| Authentication   | Flask-Login 0.6.3        | Session management, user identity         |
| Security         | Werkzeug 3.0.3           | Password hashing (PBKDF2), file safety    |
| Templating       | Jinja2                   | Server-side HTML rendering                |
| Frontend         | Bootstrap 5.3.2, Vanilla CSS/JS | Responsive UI, interactions        |
| Typography       | Google Fonts (Inter, Playfair Display) | Visual hierarchy, readability |

### 2.2 Data Model

The relational schema comprises **13 interconnected models** that capture the full domain of an e-learning ecosystem.

**Table 2: Entity Overview**

| Entity       | Attributes                                                | Relationships                        |
|--------------|-----------------------------------------------------------|--------------------------------------|
| User         | name, email, password_hash, role, xp                      | → Enrollment, UserBadge, Review, Note, Favorite |
| Course       | title, short_desc, long_desc, thumbnail, instructor       | → Lesson, Quiz, Discussion           |
| Lesson       | title, content (HTML), video_url, position                | ← Course; → Note                     |
| Quiz         | title                                                      | ← Course; → Question                 |
| Question     | text, option_a–d, correct (A/B/C/D)                       | ← Quiz                               |
| Enrollment   | student_id, course_id, progress, created_at               | ← User, Course                       |
| Discussion   | author, content, created_at                                | ← Course                             |
| Review       | rating (1–5), comment, created_at                          | ← User, Course                       |
| Favorite     | user_id, course_id (unique constraint)                     | ← User, Course                       |
| Coupon       | code, percent_off, amount_off_cents, active, expires_at    | Standalone                           |
| Note         | timestamp_seconds, text, created_at                        | ← User, Lesson                       |
| Badge        | name, description, icon, xp_bonus                          | → UserBadge                          |
| UserBadge    | user_id, badge_id, earned_at                               | ← User, Badge (many-to-many join)    |

**Figure 1: Entity-Relationship Diagram**

```
User ──┬── Enrollment ──── Course ──┬── Lesson ──── Note
       ├── UserBadge ──── Badge     ├── Quiz ──── Question
       ├── Review                   ├── Discussion
       └── Favorite                 └── (Coupon — standalone)
```

### 2.3 Role-Based Access Control (RBAC)

The system implements a hierarchical three-tier RBAC model enforced through custom Python decorators.

**Table 3: Role Hierarchy and Permissions**

| Role        | Permissions                                                                 |
|-------------|-----------------------------------------------------------------------------|
| Student     | Browse catalog, enroll, view lessons, take quizzes, manage cart/wishlist, post reviews/discussions, earn XP and badges |
| Instructor  | All Student permissions + create/edit/delete own courses, lessons, and quizzes; view enrollment analytics and revenue reports |
| Admin       | All Instructor permissions + manage all users (role changes, account deletion), manage all courses across the platform |

Access control is enforced at the route level via three decorators:
- `@login_required` — ensures authenticated session
- `@instructor_required` — restricts to instructor and admin roles
- `@admin_required` — restricts to admin role exclusively

---

## 3. Feature Description

### 3.1 Course Discovery and Catalog Management

The homepage implements an intelligent course discovery system that presents content through multiple algorithmic lenses:

- **Trending Courses**: The top six courses ranked by aggregate enrollment count, with a fallback to most recently created courses when insufficient enrollment data exists.
- **New & Noteworthy**: The six most recently created courses, displayed chronologically.
- **Continue Learning**: For authenticated users, the three most recently enrolled courses with real-time progress percentages calculated as `(lessons_completed / total_lessons) × 100`.
- **Featured Instructors**: The top three instructors ranked by total enrollments across all their courses, with representative course samples.
- **Full-Text Search**: Multi-field search across course titles, short descriptions, and long descriptions using case-insensitive pattern matching (`ILIKE`).

### 3.2 Course Detail and Content Delivery

Each course is presented through a feature-rich detail page that consolidates:

- **Structured Curriculum**: An accordion-based syllabus view displaying all lessons with sequential position ordering and completion checkmarks tied to student progress.
- **Preview Video**: Automatically resolved from the first lesson containing a video URL, embedded via YouTube iframe.
- **Social Proof Metrics**: Live enrollment count, average star rating with visual breakdown (1–5 star histogram), and featured review testimonials.
- **Related Courses**: An algorithmic recommendation displaying up to six courses, prioritizing courses by the same instructor, with fallback to other recent courses.
- **Canonical URL Generation**: SEO-oriented canonical URL injection for search engine indexing.

### 3.3 Video-Based Lesson Delivery

Lessons are delivered through an embedded YouTube player with an adjacent lesson navigation sidebar. The system features:

- **URL Normalization Engine**: The `normalize_to_embed()` function intelligently converts diverse YouTube URL formats (standard watch URLs, short `youtu.be` links, Shorts URLs, existing embed URLs) into a consistent embed format suitable for iframe rendering.
- **Progress Tracking**: Each lesson view updates the student's enrollment progress to the maximum position reached, ensuring forward-only progress without regression.
- **Timestamped Notes**: Students can save notes tied to specific video timestamps via a JSON API endpoint (`/api/note/save`), enabling context-anchored annotation with creation and deletion capabilities.

### 3.4 Assessment Framework

The assessment system supports multiple-choice questionnaires (MCQs) with the following characteristics:

- **Question Structure**: Each question presents four options (A, B, C, D) with a single correct answer.
- **Instant Scoring**: Quiz submissions are evaluated server-side with immediate score feedback as `score/total` ratio.
- **Progress Visualization**: A client-side progress bar reacts to answer selections, providing real-time completion feedback.
- **Flashcard Generation**: An API endpoint (`/api/flashcards/<course_id>`) auto-generates flashcards by mapping quiz questions to their correct answers, supporting spaced repetition study techniques.

### 3.5 Gamification Engine

The gamification subsystem is designed to enhance learner motivation through three interconnected mechanisms:

#### 3.5.1 Experience Points (XP)

XP serves as the primary quantitative engagement metric, awarded through the following events:

**Table 4: XP Award Schedule**

| Trigger                     | XP Awarded | Condition                     |
|-----------------------------|------------|-------------------------------|
| Lesson completion           | +10 XP     | First time reaching a new position |
| Quiz passed                 | +20 XP     | Score ≥ 50%                   |
| Perfect quiz score          | +100 XP    | Score = 100%                  |
| First Step badge            | +50 XP     | First lesson completed        |
| Quiz Master badge           | +100 XP    | First 100% quiz               |
| Night Owl badge             | +50 XP     | Study between 00:00–04:00 UTC |
| Dedicated Learner badge     | +500 XP    | Full course completion        |

#### 3.5.2 Achievement Badges

The badge system employs an **event-driven award mechanism** where specific user actions trigger badge eligibility checks:

**Table 5: Badge Definitions**

| Badge             | Trigger Condition                       | Icon        |
|-------------------|-----------------------------------------|-------------|
| First Step        | Complete the first lesson in any course | fa-medal    |
| Quiz Master       | Achieve 100% on any quiz               | fa-medal    |
| Night Owl         | Access a lesson between 00:00–04:00 UTC| fa-medal    |
| Dedicated Learner | Complete all lessons in a course        | fa-medal    |

Badge awards are **idempotent** — the system verifies that a user does not already possess a badge before granting it, preventing duplicate awards.

#### 3.5.3 Competitive Leaderboard

A public leaderboard displays the top 20 students ranked by cumulative XP, providing social comparison and competitive motivation.

### 3.6 E-Commerce Module

#### 3.6.1 Tiered Pricing Model

Course pricing follows a deterministic tiered model based on course ID modular arithmetic:
- Tier 1: $49.00
- Tier 2: $59.00
- Tier 3: $79.00

#### 3.6.2 Shopping Cart

The cart subsystem operates via Flask server-side sessions:
- Multi-course cart with add/remove operations
- Aggregate pricing with real-time total computation
- Coupon code integration at the cart level

#### 3.6.3 Coupon and Discount System

The discount engine supports two coupon types with composable application:
- **Percentage discount**: Calculated as `(price × percent_off) / 100`
- **Fixed amount discount**: Direct cent-based deduction
- **Validation checks**: Active status, expiration date, and maximum usage limits
- **Case-insensitive matching**: Coupon codes are matched using SQL `UPPER()` normalization

#### 3.6.4 Mock Payment Processing

The checkout flow implements a realistic payment validation pipeline:
- **Luhn Algorithm**: Industry-standard credit card number validation (PAN verification)
- **Input Formatting**: Client-side real-time formatting for card number (grouped as 4-4-4-4), expiry (MM/YY), and CVV (3–4 digits)
- **Post-Payment Enrollment**: Successful payment automatically creates enrollment records and increments coupon usage counters

### 3.7 Certification System

Certificates are generated automatically upon 100% course completion (all lessons viewed). Each certificate contains:
- A unique identifier in the format `CERT-{course_id}-{user_id}-{date}`
- Student name and course title
- Completion date

### 3.8 Social and Collaborative Features

#### 3.8.1 Discussion Forums

Each course provides a threaded discussion forum where enrolled students can post text-based comments. Posts are displayed in reverse chronological order with author attribution.

#### 3.8.2 Reviews and Ratings

Enrolled students may submit star ratings (1–5 scale) with optional text comments. The system:
- Computes and displays aggregate average ratings per course
- Generates a star breakdown histogram (count per star level)
- Highlights top-rated reviews as featured testimonials
- Supports review updates (upsert behavior — same user can modify their rating)

#### 3.8.3 Wishlist / Favorites

Users can toggle courses in their personal wishlist via a dedicated API endpoint, with a unique constraint preventing duplicate entries.

### 3.9 Content Enrichment Engine

The **Content Enrichment Engine** is a sophisticated, idempotent content generation pipeline that constitutes one of the platform's key technical innovations. It operates in the following stages:

#### 3.9.1 Course Classification

Courses are classified into 11 domain categories using keyword-based heuristic matching on course titles:

**Table 6: Domain Classification Categories**

| Category       | Example Domains                              |
|----------------|----------------------------------------------|
| fullstack      | Full-Stack Web Development, MERN, Django      |
| python         | Python Programming, Automation                |
| datasci        | Data Science, Data Analysis, Statistics        |
| ml             | Machine Learning, Deep Learning, NLP           |
| security       | Cybersecurity, Ethical Hacking, Cryptography   |
| cloud          | Cloud Computing, AWS, DevOps                   |
| uiux           | UI/UX Design, Figma, Prototyping               |
| marketing      | Digital Marketing, SEO, Content Strategy       |
| finance        | Finance, Accounting, Investment                |
| english        | English Communications, Business Writing       |
| productivity   | Productivity, Time Management, Leadership      |

#### 3.9.2 Content Generation Pipeline

For each classified course, the engine:

1. **Generates Rich Descriptions**: Category-specific templates produce long-form descriptions including syllabus highlights, learning outcomes, capstone project descriptions, required tools, and prerequisite knowledge.
2. **Creates Structured Lessons**: 8–12 lessons per course, aligned to predefined module syllabi with HTML-formatted content and sequential positioning.
3. **Resolves Video Resources**: A **six-tier fallback mechanism** resolves video URLs:
   - *Tier 1*: Curated introductory videos for first lessons (from `video_curated_intro.json`)
   - *Tier 2*: Topic-specific video mappings (from `video_topics_map.json`)
   - *Tier 3*: Cached API/search results (from `video_cache.json`)
   - *Tier 4*: YouTube Data API v3 search (when API key is configured)
   - *Tier 5*: YouTube search embed fallback
   - *Tier 6*: Channel playlist fallback (from `video_channels.json`)
4. **Generates Assessments**: Topic-aligned MCQ questions from a heuristic question bank covering 100+ unique questions across multiple subject domains.

#### 3.9.3 Idempotency Guarantees

The enrichment process is designed to be safely re-runnable:
- Existing lessons and quizzes are not duplicated on repeated execution
- Only generic placeholder quizzes (identified by pattern matching) are upgraded to domain-specific content
- Video URL resolution caches results to minimize external API calls

### 3.10 AI-Assisted Features (Mock Architecture)

The `MockAIService` class provides two simulated AI capabilities designed as integration-ready placeholders:

#### 3.10.1 Automated Quiz Generation

The mock quiz generator produces five MCQ questions from course content using deterministic templates. This module is architecturally designed for replacement with real LLM-based generation (e.g., GPT-4, Gemini) without structural changes to the routing or database layer.

#### 3.10.2 Conversational AI Assistant

A floating chatbot widget provides keyword-based conversational responses:
- Responds to greetings, explanations, quiz-related queries, and Python programming questions
- Communicates via a JSON API endpoint (`/api/chat`)
- Implements a typing indicator and message history within the chat session

### 3.11 Instructor Analytics Dashboard

Instructors have access to an analytics view that aggregates:
- **Per-Course Enrollment Counts**: Total students enrolled in each course owned by the instructor.
- **Revenue Estimates**: Computed as `Σ (enrollment_count × course_price)` across all owned courses.

### 3.12 Administrative Control Panel

Administrators have access to platform-wide management capabilities:
- **User Management**: View all registered users, modify user roles (student ↔ instructor ↔ admin), delete user accounts.
- **Course Oversight**: Browse and manage all courses regardless of ownership.
- **Protected Admin Account**: The default admin account is safeguarded from deletion.

---

## 4. Frontend Design and User Experience

### 4.1 Design Philosophy

The frontend implements a **premium glassmorphism design system** with the following characteristics:
- Semi-transparent surfaces with `backdrop-filter: blur()` for depth perception
- Dark-first design with a full light theme variant toggled via `data-theme` attribute
- Curated color palette using CSS custom properties (design tokens)
- Editorial typography pairing: Inter (body) and Playfair Display (headings) from Google Fonts

### 4.2 Responsive Design

The application uses Bootstrap 5.3.2's grid system and breakpoint utilities to ensure responsive behavior across viewports. Key responsive features include:
- Floating pill-shaped navbar at desktop widths (≥992px)
- Collapsible mobile navigation via hamburger toggle
- Adaptive course card grids and hero layouts

### 4.3 Micro-Interactions and Animations

The client-side JavaScript layer (~621 lines) implements rich interactive behaviors:

**Table 7: Client-Side Interaction Features**

| Feature                      | Technique                                        |
|------------------------------|--------------------------------------------------|
| Scroll-triggered reveals     | IntersectionObserver with threshold-based triggers |
| Button ripple effect         | Dynamic DOM element creation with CSS animation    |
| Cursor-following spotlight   | Pointer tracking via CSS custom properties         |
| Scroll progress indicator    | requestAnimationFrame-driven transform scaling     |
| Parallax hero                | Scroll-based translateY transforms                 |
| Dark/Light theme toggle      | localStorage persistence + system preference       |
| Credit card input masking    | Real-time regex-based input formatting             |
| 3D card tilt                 | CSS rotateX/rotateY transforms on hover            |

### 4.4 Accessibility

The platform implements WAI-ARIA compliance through:
- `aria-label`, `aria-controls`, `aria-pressed`, and `aria-live` attributes
- `prefers-reduced-motion` media query support disabling all animations
- Focus-visible styling for keyboard navigation
- Semantic HTML5 elements (`<main>`, `<nav>`, `<header>`, `<footer>`)

### 4.5 Analytics and A/B Testing Instrumentation

A lightweight analytics emitter tracks 20+ user interaction events (login flows, CTA clicks, search behavior, cart actions) via a `dataLayer`-compatible interface. Two A/B test variants are instrumented:
- **Sticky CTA Variant**: Randomized button styling for course purchase prompts
- **Hero Layout Variant**: Randomized hero section accent color (blue vs. green)

---

## 5. Technical Implementation

### 5.1 Technology Stack Summary

**Table 8: Complete Technology Stack**

| Component        | Technology            | Version  |
|------------------|-----------------------|----------|
| Language         | Python                | 3.10+    |
| Web Framework    | Flask                 | 2.3.3    |
| ORM              | Flask-SQLAlchemy      | 3.1.1    |
| Authentication   | Flask-Login           | 0.6.3    |
| HTTP Utilities   | Werkzeug              | 3.0.3    |
| Database         | SQLite                | 3        |
| CSS Framework    | Bootstrap             | 5.3.2    |
| Custom CSS       | Vanilla CSS           | ~633 LOC |
| Client JS        | Vanilla ES6+          | ~621 LOC |
| Templating       | Jinja2                | Bundled  |
| Typography       | Google Fonts          | —        |
| Video Platform   | YouTube (iframe embed) | —       |
| Testing          | pytest                | —        |

### 5.2 Codebase Metrics

**Table 9: Project Quantitative Metrics**

| Metric                      | Value       |
|-----------------------------|-------------|
| Backend source lines        | ~2,157      |
| Custom CSS lines            | ~633        |
| Custom JavaScript lines     | ~621        |
| Database models             | 13          |
| HTML templates              | 26          |
| RESTful routes              | 40+         |
| API endpoints               | 4           |
| Pre-seeded courses          | 10          |
| Quiz questions (generated)  | 100+        |
| Seeded discount coupons     | 3           |
| Python dependencies (direct)| 4           |
| Frontend CDN dependencies   | 3           |
| Build tools required        | None        |

### 5.3 Security Measures

| Measure                    | Implementation                              |
|----------------------------|---------------------------------------------|
| Password storage           | PBKDF2-SHA256 via Werkzeug                   |
| Session security           | Flask secret key-based signed cookies        |
| XSS prevention             | Jinja2 auto-escaping on all template outputs |
| File upload safety          | `secure_filename()` sanitization             |
| Payment validation          | Luhn algorithm for card number verification  |
| Role enforcement            | Server-side decorator-based access control   |

---

## 6. Results and Demonstration

The completed platform successfully demonstrates:

1. **End-to-end learner journey**: A student can register, browse courses, search by keyword, enroll (via direct enrollment or cart-based checkout with coupon discounts), watch video lessons with timestamped notes, take quizzes, earn XP and badges, review courses, participate in discussions, generate flashcards, track progress on a dashboard, and receive a certificate upon completion.

2. **Instructor workflow**: An instructor can create courses with thumbnail uploads, add sequenced lessons with auto-normalized YouTube videos, create quizzes with MCQ questions, utilize AI-generated quiz drafts, and monitor enrollment analytics with revenue projections.

3. **Administrative oversight**: An admin can manage all users, modify roles, delete accounts (with protection for the default admin), and oversee all courses platform-wide.

4. **Content automation**: The Content Enrichment Engine successfully auto-populates 10 courses with structured lessons, curated videos, and domain-specific quiz content across 11 subject categories, demonstrating the viability of rule-based content generation for educational platforms.

5. **Engagement metrics**: The gamification system awards XP and badges across four distinct achievement categories, with a competitive leaderboard ranking the top 20 learners.

---

## 7. Future Work

Several extensions are planned to evolve the platform:

1. **LLM Integration**: Replace the `MockAIService` with production LLM APIs (e.g., OpenAI GPT-4, Google Gemini) for intelligent quiz generation and conversational tutoring.
2. **Real Payment Gateway**: Integrate Stripe or Razorpay for actual payment processing.
3. **PostgreSQL Migration**: Transition from SQLite to PostgreSQL for concurrent multi-user support and production deployment.
4. **Video Analytics**: Implement watch-time tracking and engagement heatmaps on lesson videos.
5. **Adaptive Learning Paths**: Use learner performance data to recommend personalized course sequences.
6. **Mobile Application**: Develop a companion mobile app using React Native or Flutter.
7. **Real-Time Notifications**: Implement WebSocket-based push notifications for badge awards, discussion replies, and course announcements.
8. **Plagiarism Detection**: Add automated plagiarism checking for discussion forum posts and assignment submissions.
9. **Multi-Language Support**: Internationalize the platform with i18n/l10n support for regional expansion.
10. **SCORM Compliance**: Implement SCORM (Sharable Content Object Reference Model) compatibility for interoperability with existing LMS ecosystems.

---

## 8. Conclusion

EduLearn successfully demonstrates that a feature-complete, aesthetically refined, and architecturally sound learning management system can be built using a lightweight Python web stack. The platform's **Content Enrichment Engine** proves the viability of automated, idempotent content generation for educational applications, while the **gamification subsystem** implements established motivational design patterns to drive learner engagement. The mock AI architecture establishes clear integration pathways for future LLM-powered educational features. With over 2,150 lines of backend code, 13 database models, 26 templates, and 40+ routes, EduLearn serves as both a practical educational tool and a comprehensive reference implementation for full-stack web application development.

---

## References

1. Grinberg, M. (2018). *Flask Web Development: Developing Web Applications with Python* (2nd ed.). O'Reilly Media.
2. Deterding, S., Dixon, D., Khaled, R., & Nacke, L. (2011). From Game Design Elements to Gamefulness: Defining "Gamification." *Proceedings of the 15th International Academic MindTrek Conference*, 9–15.
3. Dicheva, D., Dichev, C., Agre, G., & Angelova, G. (2015). Gamification in Education: A Systematic Mapping Study. *Educational Technology & Society*, 18(3), 75–88.
4. Pallets Projects. (2023). Flask Documentation (Version 2.3.x). https://flask.palletsprojects.com/
5. SQLAlchemy Authors. (2023). SQLAlchemy Documentation. https://docs.sqlalchemy.org/
6. Bootstrap Team. (2023). Bootstrap 5.3 Documentation. https://getbootstrap.com/docs/5.3/
7. Luhn, H.P. (1960). Computer for Verifying Numbers. US Patent 2,950,048.
8. W3C. (2023). WAI-ARIA Authoring Practices 1.2. https://www.w3.org/WAI/ARIA/apg/

---

## Appendix A: System Setup and Reproduction

### Prerequisites
- Python 3.10 or higher

### Installation and Execution
```bash
pip install -r requirements.txt
python app.py
```

The application automatically:
1. Creates the SQLite database (`instance/edulearn_full.db`)
2. Seeds a default administrator account
3. Populates 10 demonstration courses
4. Executes the Content Enrichment Engine

Access the platform at `http://127.0.0.1:5000`.

### Default Credentials

| Role       | Email                     | Password   |
|------------|---------------------------|------------|
| Admin      | admin@edulearn.com        | admin123   |
| Instructor | instructor@edulearn.com   | password   |
| Student    | student@edulearn.com      | password   |

---

## Appendix B: Database Schema Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    User      │────→│  Enrollment  │←────│   Course    │
│─────────────│     │──────────────│     │─────────────│
│ id           │     │ id           │     │ id          │
│ name         │     │ student_id   │     │ title       │
│ email        │     │ course_id    │     │ short_desc  │
│ password_hash│     │ progress     │     │ long_desc   │
│ role         │     │ created_at   │     │ thumbnail   │
│ xp           │     └──────────────┘     │ instructor  │
└──────┬──────┘                           └──────┬──────┘
       │                                         │
       ├──→ UserBadge ←── Badge                  ├──→ Lesson ←── Note
       ├──→ Review                               ├──→ Quiz ──→ Question
       ├──→ Favorite                             └──→ Discussion
       └──→ Note
                                    ┌─────────────┐
                                    │   Coupon     │
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

*Manuscript prepared: March 2026*
