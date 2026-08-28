"""Version 1 interview-generation and evaluation prompts."""

import json
from typing import Any


INTERVIEW_PROMPT_VERSION = "interview_v1"


def build_interview_generation_prompt(
    *,
    previous_context: str,
    career_title: str,
    position_title: str,
    company_name: str,
    question_count: int,
) -> str:
    """Build the interview question-generation prompt."""

    return f"""
You are the AI interview engine for CareerGrid.

Create a realistic professional job interview.

CAREER:
{career_title}

POSITION:
{position_title}

COMPANY:
{company_name}


The candidate already completed a workplace simulation.

Here is the completed workplace simulation context:

{previous_context}


CRITICAL EXCLUSION RULE:

DO NOT repeat anything the candidate already had to do
in the workplace simulation.

Do not:
- repeat the same task
- paraphrase the same task
- reuse the same workplace problem
- ask for the same deliverable
- ask a technical question that directly repeats a skill already
  demonstrated by the previous task
- ask something whose answer was already explicitly produced
  in the workplace simulation

The interview must feel like a completely separate real interview.


Generate exactly {question_count} questions.

Use this structure:

1. Professional introduction / tell me about yourself
2. Motivation for this company or position
3. Behavioral interview question
4. Situational problem-solving question
5. Workplace judgment / teamwork / communication question
6. Technical or role-knowledge question that was NOT already
   covered by the workplace simulation
7. Final hiring-manager style question


The interview should be realistic.

Do not make every question highly technical.

The technical question should test useful role knowledge rather than
obscure trivia.


Each interview attempt should vary in wording, scenarios and focus.


For every question provide:

difficulty:
- easy
- medium
- hard

target_words:
Estimate how many spoken words a strong candidate would normally
need to answer properly.

Suggested ranges:

easy:
70-100 words

medium:
100-160 words

hard:
140-220 words


Also create a PRIVATE evaluation rubric for every question.

Return ONLY valid JSON.

Exact structure:

{{
    "interview_title": "string",
    "opening_message": "string",

    "questions": [
        {{
            "id": 1,

            "category": "introduction",

            "question": "string",

            "difficulty": "easy",

            "target_words": 90,

            "rubric": {{
                "excellent_answer_should_include": [
                    "string"
                ],

                "important_points": [
                    "string"
                ],

                "red_flags": [
                    "string"
                ]
            }}
        }}
    ]
}}

Do not include markdown.
"""


def build_spoken_answer_evaluation_prompt(
    *,
    question: dict[str, Any],
    rubric: dict[str, Any],
    company_name: str,
    position_title: str,
) -> str:
    """Build the private prompt for one recorded interview answer."""

    return f"""
You are evaluating ONE spoken answer from a CareerGrid job interview.

COMPANY:
{company_name}

POSITION:
{position_title}

INTERVIEW QUESTION:
{question.get("question", "")}

QUESTION DIFFICULTY:
{question.get("difficulty", "medium")}

EXPECTED STRONG ANSWER LENGTH:
{question.get("target_words", 100)} words


PRIVATE QUESTION RUBRIC:

{json.dumps(rubric, ensure_ascii=False)}


Listen carefully to the candidate's attached microphone recording.


Your first job is to create an accurate transcript of what the
candidate actually said.

Do NOT improve or rewrite their answer.

Keep filler words if they are actually spoken.


Then evaluate the candidate.


CONTENT:

Evaluate:
- whether they actually answered the question
- relevance
- specificity
- completeness
- reasoning
- examples when appropriate
- professional understanding
- quality compared with the private rubric


SPEAKING DELIVERY:

Evaluate:
- clarity
- fluency
- hesitation
- awkward pauses
- excessive filler words
- speaking pace
- professionalism
- confidence communicated through organization and decisiveness


Do NOT score or judge:
- accent
- nationality
- ethnicity
- gender
- age
- voice pitch
- vocal depth
- any protected or personal characteristic


Confidence means:
- decisive phrasing
- organized answer
- limited unnecessary hesitation
- ability to communicate the idea clearly

It does NOT mean having a specific accent or voice type.


Return ONLY valid JSON:

{{
    "transcript": "exact transcript",

    "content_score": 0,

    "relevance_score": 0,

    "structure_score": 0,

    "clarity_score": 0,

    "confidence_score": 0,

    "professionalism_score": 0,

    "delivery_score": 0,

    "long_pause_count": 0,

    "hesitation_level": "low",

    "feedback": "specific concise feedback",

    "strong_points": [
        "specific strength"
    ],

    "improvements": [
        "specific improvement"
    ]
}}

Every score must be between 0 and 100.

Do not invent words the candidate did not say.
"""


def build_final_interview_evaluation_prompt(
    *,
    deterministic_score: float,
    answer_list: list[dict[str, Any]],
    company_name: str,
    position_title: str,
) -> str:
    """Build the final interview-report prompt."""

    return f"""
You are preparing the FINAL CareerGrid job interview report.

COMPANY:
{company_name}

POSITION:
{position_title}


The candidate completed the entire interview.


CALCULATED INTERVIEW SCORE:
{deterministic_score}/100


QUESTION-BY-QUESTION EVIDENCE:

{json.dumps(answer_list, ensure_ascii=False)}


Create concise and useful interview feedback.

Do NOT change the calculated score.

The feedback should help the user prepare for a real interview.

Mention repeated speaking issues if they appear across answers,
such as:

- excessive filler words
- answers that are too short
- answers that are too long
- weak structure
- unclear examples
- excessive hesitation
- poor speaking pace
- strong professionalism
- strong clarity
- strong reasoning


Return ONLY valid JSON:

{{
    "overall_score": {deterministic_score},

    "summary":
        "overall interview assessment",

    "strengths": [
        "specific strength"
    ],

    "areas_for_improvement": [
        "specific improvement"
    ],

    "communication_feedback":
        "specific feedback about speaking performance",

    "content_feedback":
        "specific feedback about answer quality",

    "next_steps": [
        "specific interview preparation recommendation"
    ],

    "readiness":
        "one concise statement describing interview readiness"
}}

Do not mention hidden rubrics.

Do not mention internal scoring formulas.
"""
