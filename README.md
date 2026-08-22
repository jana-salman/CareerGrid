# CareerGrid

CareerGrid is an AI-powered career exploration and job simulation platform designed to help students and early-career users experience realistic workplace tasks before choosing or pursuing a career.

Users can explore career paths, complete interactive workplace simulations, receive AI-generated performance feedback, practice job interviews, and track their progress through a personalized dashboard.

## Problem Statement

Many students choose career paths without having a clear understanding of what the actual day-to-day work looks like.

Traditional career guidance often focuses on descriptions, personality tests, or job listings, but does not allow users to experience realistic job tasks.

CareerGrid addresses this problem by allowing users to practice realistic workplace scenarios in an interactive simulated environment and receive personalized AI-powered feedback.

## Objectives

CareerGrid aims to:

- Help users understand what different careers are actually like.
- Provide realistic and interactive job simulations instead of quiz-style career tests.
- Use AI to dynamically generate workplace scenarios.
- Evaluate user performance and provide personalized feedback.
- Allow users to practice job interviews related to their chosen career.
- Track simulation history and performance over time.
- Help users identify strengths and areas that need improvement.

## Features

### User Authentication
- User registration and login.
- Secure password hashing.
- Firebase-based user persistence.
- Authenticated user sessions.

### Career Exploration
- Browse supported career paths.
- View available positions within each career.
- Select companies and job roles.

### Interactive Workplace Simulations
Users complete realistic workplace tasks through a simulated desktop environment.

The workspace can contain applications such as:

- Mail
- Browser
- Files
- VS Code
- Terminal
- GitHub
- Team Chat

Instead of answering traditional quiz questions, users investigate problems, interact with workplace tools, make decisions, and submit their work.

### AI-Generated Scenarios
CareerGrid uses generative AI to create realistic workplace scenarios based on the selected career and position.

Generated scenarios may include:

- Manager instructions
- Emails
- Source files
- Bugs or workplace problems
- Browser content
- Terminal tasks
- GitHub workflows
- Expected solutions and evaluation criteria

### AI Performance Evaluation
After completing a simulation, the user's work is evaluated and a performance report is generated.

The report can include:

- Overall score
- Performance breakdown
- Strengths
- Areas for improvement
- Recommended next steps
- Personalized career advice

### AI Career Advisor
Users can request contextual assistance during a simulation when they are unsure how to continue.

### AI Job Interview
After completing a workplace simulation, users can practice a career-specific job interview.

The interview system:

- Generates questions based on the selected career.
- Takes the completed simulation into account.
- Avoids unnecessarily repeating skills already demonstrated in the simulation.
- Supports voice-based answers.
- Transcribes responses.
- Evaluates interview performance.
- Generates personalized feedback.

### User Dashboard
Users can view:

- Previous simulation attempts
- Completed simulations
- Performance scores
- Career history
- Interview results
- Simulation status


## User Flow

Register / Login
       ↓
Home Page
       ↓
Explore Careers
       ↓
Select Career
       ↓
Select Position
       ↓
Select Company
       ↓
Generate AI Workplace Scenario
       ↓
Complete Interactive Simulation
       ↓
Submit Work
       ↓
AI Performance Evaluation
       ↓
Performance Report
       ↓
AI Job Interview
       ↓
Interview Feedback
       ↓
Dashboard / Career Progress


---

# Technologies used

## Technologies Used

### Backend
- Python
- Flask

### Frontend
- HTML5
- CSS3
- JavaScript
- Jinja2

### Database & Authentication
- Firebase
- Firebase Admin SDK
- Firebase Realtime Database
- Werkzeug password hashing

### Artificial Intelligence
- Google Gemini API
- Structured AI response generation
- Pydantic validation

### External APIs
- Adzuna Jobs API

### Development Tools
- Git
- GitHub
- Visual Studio Code
- Python Virtual Environment

## Project Architecture

CareerGrid follows a service-based Flask architecture.

CareerGrid/
│
├── app.py
│
├── routes/
│   └── auth.py
│
├── services/
│   ├── scenario generation
│   ├── evaluation
│   ├── interview
│   ├── advisor
│   └── Firebase storage
│
├── schemas/
│   └── AI response validation schemas
│
├── templates/
│   ├── authentication pages
│   ├── career pages
│   ├── dashboard
│   ├── simulation
│   └── interview pages
│
├── static/
│   ├── css/
│   └── js/
│
└── tests/


---

#  Explain the AI architecture

## AI Integration

Artificial intelligence is used in several stages of CareerGrid.

### Scenario Generation

The AI generates workplace scenarios based on:

- Career
- Position
- Company
- Difficulty
- Simulation requirements

The generated response follows a predefined structured format.

### Structured Output Validation

AI responses are validated before they are used by the application.

Validation helps prevent:

- Invalid file paths
- Missing scenario information
- Invalid JSON structures
- Unsafe terminal commands
- Accidental exposure of expected solutions
- Oversized generated files

### Performance Evaluation

When users submit their simulation work, CareerGrid compares their actions and submitted work against hidden evaluation criteria.

The AI then produces structured feedback including scores, strengths, weaknesses, and recommendations.

### Interview Generation

Interview questions are generated based on the user's career and previous simulation experience.

The system attempts to assess additional skills rather than simply repeating tasks already evaluated during the workplace simulation.

## Scenario Security and Evaluation Design

CareerGrid separates scenario information into public and private components.

### Public Scenario Data

Information that the user is allowed to see, such as:

- Emails
- Files
- Task instructions
- Browser content
- Workplace messages

### Private Evaluation Data

Information used internally for evaluation, such as:

- Expected solution
- Required evidence
- Evaluation criteria
- Scoring information

Private evaluation data is not intentionally exposed to the user during the simulation.

## Installation

### 1. Clone the repository
git clone https://github.com/jana-salman/CareerGrid.git
cd CareerGrid

python -m venv venv
venv\Scripts\activate

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt


---

# 11. Environment variables


## Environment Variables

Create a `.env` file in the project root.

Example:

```env
FLASK_SECRET_KEY=your_secret_key

GEMINI_API_KEY=your_gemini_api_key

ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key

FIREBASE_DATABASE_URL=your_firebase_database_url


> Never commit API keys, `.env` files, or Firebase private credentials to GitHub.

## Running CareerGrid
After installing the dependencies and configuring the environment variables:
python app.py
Then open:
http://127.0.0.1:5000



---

#Screenshots

## Screenshots

### Home Page

![CareerGrid Home](docs/images/home.png)

### Career Selection

![Career Selection](docs/images/careers.png)

### Workplace Simulation

![Simulation Desktop](docs/images/simulation.png)

### Performance Report

![Performance Report](docs/images/report.png)

### AI Interview

![AI Interview](docs/images/interview.png)

### Dashboard

![Dashboard](docs/images/dashboard.png)


## Supported Career Simulations

### Software Development
- Backend Developer
- Frontend Developer

## Testing

CareerGrid includes automated tests for important application functionality.

The test suite covers areas such as:

- Scenario generation validation
- Scenario storage
- Public/private scenario separation
- AI evaluation
- Simulation workflows
- Invalid AI responses
- Security-related validation

Run the test suite using:
pytest

## Current Limitations

CareerGrid is currently a prototype and has several areas for future improvement:

- The number of supported careers is currently limited.
- More extensive automated testing is planned.

