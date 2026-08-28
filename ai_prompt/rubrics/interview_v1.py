"""Version 1 private interview evaluation rubrics."""


INTERVIEW_RUBRIC_VERSION = "interview_v1"


def build_backend_demo_interview_rubrics() -> dict[str, dict[str, list[str]]]:
    """Return server-only rubrics for the deterministic Backend demo."""

    return {
        "1": {
            "excellent_answer_should_include": [
                "A concise professional introduction",
                "Relevant technical background or experience",
                "Genuine interest in backend development",
                "Interest in problem solving, APIs, data, or backend systems",
                "A desire to learn and grow",
            ],
            "important_points": [
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
        "2": {
            "excellent_answer_should_include": [
                "Clearly identifies a real project and its purpose or problem",
                "Explains the candidate's personal role and contribution",
                "Mentions relevant technologies without requiring a fixed stack",
                "Describes at least one meaningful challenge",
                "Explains how the challenge was approached",
                "Reflects on the result or what was learned",
                "Communicates the experience clearly",
            ],
            "important_points": [
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
        "3": {
            "excellent_answer_should_include": [
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
            "important_points": [
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
        "4": {
            "excellent_answer_should_include": [
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
            "important_points": [
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
    }
