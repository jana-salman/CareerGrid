"""Predefined interview questions for the Backend Developer live demo."""

from ai_prompt.rubrics.interview_v1 import build_backend_demo_interview_rubrics
from services.ai.interview_service import calculate_answer_time


def get_backend_demo_interview() -> dict:
    """Return four public questions and matching server-only rubrics."""

    definitions = [
        {
            "category": "introduction",
            "difficulty": "easy",
            "target_words": 90,
            "question": "Tell me about yourself and what interests you about backend development.",
        },
        {
            "category": "project_experience",
            "difficulty": "medium",
            "target_words": 140,
            "question": "Tell me about a project you worked on that you're proud of. What was your role, what technologies did you use, and what challenges did you face?",
        },
        {
            "category": "behavioral",
            "difficulty": "medium",
            "target_words": 130,
            "question": "Tell me about a time you faced a technical problem that you did not immediately know how to solve. How did you approach it?",
        },
        {
            "category": "problem_solving",
            "difficulty": "medium",
            "target_words": 150,
            "question": "A backend service suddenly starts returning unexpected 500 errors in production. Walk me through how you would investigate the issue before making a code change.",
        },
    ]

    public_questions = []
    private_rubrics = build_backend_demo_interview_rubrics()

    for question_id, definition in enumerate(definitions, start=1):
        public_questions.append(
            {
                "id": question_id,
                "category": definition["category"],
                "question": definition["question"],
                "difficulty": definition["difficulty"],
                "target_words": definition["target_words"],
                "time_limit_seconds": calculate_answer_time(
                    definition["target_words"],
                    definition["difficulty"],
                ),
            }
        )
    return {
        "interview_title": "Backend Developer Interview — TechNova",
        "opening_message": (
            "Welcome to your TechNova Backend Developer interview. "
            "Take a moment to organize each answer and respond as you would in "
            "a professional interview."
        ),
        "public_questions": public_questions,
        "private_rubrics": private_rubrics,
    }
