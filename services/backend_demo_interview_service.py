"""Predefined interview questions for the Backend Developer live demo."""

from services.interview_service import calculate_answer_time


def get_backend_demo_interview() -> dict:
    """Return four public questions and matching server-only rubrics."""

    definitions = [
        {
            "category": "introduction",
            "difficulty": "easy",
            "target_words": 90,
            "question": "Tell me about yourself and what interests you about backend development.",
            "excellent": [
                "A concise professional introduction",
                "Relevant technical background or experience",
                "Genuine interest in backend development",
                "Interest in problem solving, APIs, data, or backend systems",
                "A desire to learn and grow",
            ],
            "important": [
                "professional focus",
                "technical background",
                "backend interest",
                "problem solving or backend systems",
                "learning mindset",
            ],
            "red_flags": [
                "The answer is completely unrelated to the role",
                "No explanation of interest in backend development",
                "An extremely vague or incoherent response",
            ],
        },
        {
            "category": "project_experience",
            "difficulty": "medium",
            "target_words": 140,
            "question": "Tell me about a project you worked on that you're proud of. What was your role, what technologies did you use, and what challenges did you face?",
            "excellent": [
                "Clearly identifies a real project and its purpose or problem",
                "Explains the candidate's personal role and contribution",
                "Mentions relevant technologies without requiring a fixed stack",
                "Describes at least one meaningful challenge",
                "Explains how the challenge was approached",
                "Reflects on the result or what was learned",
                "Communicates the experience clearly",
            ],
            "important": [
                "project purpose",
                "personal contribution",
                "technologies",
                "challenge and approach",
                "result or learning",
            ],
            "red_flags": [
                "Cannot identify a project or personal contribution",
                "Lists technologies without explaining how they were used",
                "Provides no challenge, approach, result, or learning",
            ],
        },
        {
            "category": "behavioral",
            "difficulty": "medium",
            "target_words": 130,
            "question": "Tell me about a time you faced a technical problem that you did not immediately know how to solve. How did you approach it?",
            "excellent": [
                "A specific technical problem",
                "A structured investigation",
                "Reproduction or isolation of the issue where relevant",
                "Use of errors, logs, documentation, or other evidence",
                "Breaking the problem into smaller parts",
                "Asking for help appropriately",
                "Identifying root cause rather than guessing",
                "Verifying the solution",
                "A clear result and lesson learned",
            ],
            "important": [
                "specific situation",
                "investigation",
                "evidence",
                "root cause",
                "verification",
                "result and learning",
            ],
            "red_flags": [
                "No concrete technical example",
                "Random changes without investigation",
                "No verification, result, or reflection",
            ],
        },
        {
            "category": "problem_solving",
            "difficulty": "medium",
            "target_words": 150,
            "question": "A backend service suddenly starts returning unexpected 500 errors in production. Walk me through how you would investigate the issue before making a code change.",
            "excellent": [
                "Determine the scope and affected requests or endpoints",
                "Inspect application logs, stack traces, and error evidence",
                "Review recent deployments or configuration changes where relevant",
                "Reproduce the problem safely when possible",
                "Trace the request and data flow",
                "Inspect relevant service or database dependencies",
                "Identify a root cause before editing",
                "Make a focused change only after understanding the problem",
                "Verify both failing and successful cases",
                "Monitor after deployment where appropriate",
            ],
            "important": [
                "scope",
                "logs and traces",
                "recent changes",
                "safe reproduction",
                "request and dependency flow",
                "root cause",
                "focused fix",
                "verification and monitoring",
            ],
            "red_flags": [
                "Makes an immediate unverified code change",
                "Ignores logs, scope, or dependencies",
                "Provides no root-cause or verification process",
            ],
        },
    ]

    public_questions = []
    private_rubrics = {}

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
        private_rubrics[str(question_id)] = {
            "excellent_answer_should_include": definition["excellent"],
            "important_points": definition["important"],
            "red_flags": definition["red_flags"],
        }

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
