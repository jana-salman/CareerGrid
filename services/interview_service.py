"""Generate, time, analyze, and evaluate CareerGrid interview responses."""

import json
import math
import os
import re
from typing import Any

from google.genai import types

from services.gemini_service import get_gemini_client


class InterviewGenerationError(RuntimeError):
    """Raised when CareerGrid cannot generate a valid interview."""


class InterviewEvaluationError(RuntimeError):
    """Raised when CareerGrid cannot evaluate an interview answer."""


# ============================================================
# INTERVIEW CONFIGURATION
# ============================================================

INTERVIEW_QUESTION_COUNT = 7

MIN_ANSWER_SECONDS = 45
MAX_ANSWER_SECONDS = 150

PROFESSIONAL_SPEAKING_WPM = 130

TARGET_ANSWER_COVERAGE = 0.90


# ============================================================
# HELPERS
# ============================================================

def _gemini_model() -> str:
    return os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )


def _extract_json(text: str) -> dict[str, Any]:
    """
    Convert Gemini output into a JSON object even when the model
    wraps it in markdown code fences.
    """

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace(
            "```json",
            "",
            1,
        )

        cleaned = cleaned.replace(
            "```",
            "",
        )

        cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Gemini response did not contain valid JSON."
        )

    return json.loads(
        cleaned[start:end + 1]
    )


def _safe_float(
    value: Any,
    default: float = 0,
) -> float:

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def calculate_answer_time(
    target_words: int,
    difficulty: str,
) -> int:
    """
    Calculate the time available for a spoken interview answer.

    The candidate receives enough time to cover approximately
    90% of a strong answer at a professional speaking pace,
    plus thinking time.
    """

    try:
        target_words = int(target_words)

    except (TypeError, ValueError):
        target_words = 100

    target_words = max(
        50,
        min(
            target_words,
            260,
        ),
    )

    covered_words = (
        target_words
        * TARGET_ANSWER_COVERAGE
    )

    speaking_seconds = (
        covered_words
        / PROFESSIONAL_SPEAKING_WPM
    ) * 60

    difficulty = str(
        difficulty or "medium"
    ).lower()

    thinking_time = {
        "easy": 10,
        "medium": 18,
        "hard": 25,
    }.get(
        difficulty,
        18,
    )

    total_seconds = math.ceil(
        speaking_seconds
        + thinking_time
    )

    return max(
        MIN_ANSWER_SECONDS,
        min(
            total_seconds,
            MAX_ANSWER_SECONDS,
        ),
    )


def _previous_task_context(
    workplace_attempt: dict[str, Any],
) -> str:
    """
    Build context that tells Gemini what the candidate already did
    so the interview does not repeat those same tasks.
    """

    context = {
        "previous_workplace_scenario":
            workplace_attempt.get(
                "public_scenario",
                {},
            ),

        "previous_candidate_responses":
            workplace_attempt.get(
                "responses",
                {},
            ),
    }

    return json.dumps(
        context,
        ensure_ascii=False,
        default=str,
    )


# ============================================================
# QUESTION GENERATION
# ============================================================

def generate_interview_questions(
    *,
    workplace_attempt: dict[str, Any],
    career_title: str,
    position_title: str,
    company_name: str,
) -> dict[str, Any]:
    """
    Generate a fresh seven-question job interview.

    The questions are tailored to:
    - the role
    - the company
    - the user's completed workplace simulation

    Previously tested workplace tasks are explicitly excluded.
    """

    if not isinstance(
        workplace_attempt,
        dict,
    ):
        raise InterviewGenerationError(
            "A valid workplace attempt is required."
        )

    previous_context = (
        _previous_task_context(
            workplace_attempt
        )
    )

    prompt = f"""
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


Generate exactly {INTERVIEW_QUESTION_COUNT} questions.

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

    client = get_gemini_client()

    try:

        response = (
            client.models.generate_content(
                model=_gemini_model(),

                contents=prompt,

                config=types.GenerateContentConfig(
                    temperature=0.9,
                    response_mime_type="application/json",
                ),
            )
        )

        data = _extract_json(
            response.text or ""
        )

    except Exception as error:

        raise InterviewGenerationError(
            f"Interview generation failed: {error}"
        ) from error

    finally:
        client.close()

    questions = data.get(
        "questions"
    )

    if (
        not isinstance(
            questions,
            list,
        )
        or len(questions)
        != INTERVIEW_QUESTION_COUNT
    ):
        raise InterviewGenerationError(
            "Gemini did not generate exactly "
            f"{INTERVIEW_QUESTION_COUNT} interview questions."
        )

    public_questions = []
    private_rubrics = {}

    for index, question in enumerate(
        questions,
        start=1,
    ):

        if not isinstance(
            question,
            dict,
        ):
            raise InterviewGenerationError(
                "Gemini generated an invalid interview question."
            )

        question_text = str(
            question.get(
                "question",
                "",
            )
        ).strip()

        if not question_text:
            raise InterviewGenerationError(
                "Gemini generated an empty interview question."
            )

        difficulty = str(
            question.get(
                "difficulty",
                "medium",
            )
        ).lower()

        if difficulty not in {
            "easy",
            "medium",
            "hard",
        }:
            difficulty = "medium"

        try:
            target_words = int(
                question.get(
                    "target_words",
                    110,
                )
            )

        except (TypeError, ValueError):
            target_words = 110

        target_words = max(
            50,
            min(
                target_words,
                260,
            ),
        )

        question_id = index

        public_questions.append(
            {
                "id":
                    question_id,

                "category":
                    str(
                        question.get(
                            "category",
                            "general",
                        )
                    ),

                "question":
                    question_text,

                "difficulty":
                    difficulty,

                "target_words":
                    target_words,

                "time_limit_seconds":
                    calculate_answer_time(
                        target_words,
                        difficulty,
                    ),
            }
        )

        private_rubrics[
            str(question_id)
        ] = question.get(
            "rubric",
            {},
        )

    return {
        "interview_title":
            str(
                data.get(
                    "interview_title",
                    f"{position_title} Interview",
                )
            ),

        "opening_message":
            str(
                data.get(
                    "opening_message",
                    "Welcome to your CareerGrid interview simulation.",
                )
            ),

        "public_questions":
            public_questions,

        "private_rubrics":
            private_rubrics,
    }


# ============================================================
# FILLER WORD ANALYSIS
# ============================================================

def _count_fillers(
    transcript: str,
) -> dict[str, Any]:

    lowered = transcript.lower()

    patterns = {
        "uh":
            r"\buh+\b",

        "um":
            r"\bum+\b",

        "erm":
            r"\berm+\b",

        "hmm":
            r"\bhmm+\b",

        "like":
            r"\blike\b",

        "you know":
            r"\byou know\b",

        "basically":
            r"\bbasically\b",

        "actually":
            r"\bactually\b",
    }

    counts = {}
    total = 0

    for filler, pattern in patterns.items():

        count = len(
            re.findall(
                pattern,
                lowered,
                flags=re.IGNORECASE,
            )
        )

        if count:
            counts[
                filler
            ] = count

            total += count

    words = re.findall(
        r"\b[\w'-]+\b",
        transcript,
    )

    word_count = len(
        words
    )

    filler_rate = (
        (total / word_count) * 100
        if word_count
        else 0
    )

    return {
        "counts":
            counts,

        "total":
            total,

        "rate_percent":
            round(
                filler_rate,
                2,
            ),

        "word_count":
            word_count,
    }


# ============================================================
# SPOKEN ANSWER EVALUATION
# ============================================================

def analyze_spoken_answer(
    *,
    audio_bytes: bytes,
    mime_type: str,
    question: dict[str, Any],
    rubric: dict[str, Any],
    duration_seconds: float,
    company_name: str,
    position_title: str,
) -> dict[str, Any]:
    """
    Analyze the candidate's real microphone recording.

    Gemini transcribes the answer and evaluates both content
    and speaking delivery.
    """

    if not audio_bytes:
        raise InterviewEvaluationError(
            "No interview audio was received."
        )

    duration_seconds = max(
        _safe_float(
            duration_seconds,
            0,
        ),
        1,
    )

    prompt = f"""
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

    client = get_gemini_client()

    try:

        response = (
            client.models.generate_content(
                model=_gemini_model(),

                contents=[
                    prompt,

                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type,
                    ),
                ],

                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.15,
                ),
            )
        )

        result = _extract_json(
            response.text or ""
        )

    except Exception as error:

        raise InterviewEvaluationError(
            f"Could not evaluate interview audio: {error}"
        ) from error

    finally:
        client.close()

    transcript = str(
        result.get(
            "transcript",
            "",
        )
    ).strip()

    filler_data = _count_fillers(
        transcript
    )

    word_count = filler_data[
        "word_count"
    ]

    words_per_minute = (
        round(
            (
                word_count
                / duration_seconds
            )
            * 60,
            1,
        )
        if duration_seconds
        else 0
    )

    content_score = _safe_float(
        result.get(
            "content_score"
        )
    )

    relevance_score = _safe_float(
        result.get(
            "relevance_score"
        )
    )

    structure_score = _safe_float(
        result.get(
            "structure_score"
        )
    )

    clarity_score = _safe_float(
        result.get(
            "clarity_score"
        )
    )

    confidence_score = _safe_float(
        result.get(
            "confidence_score"
        )
    )

    professionalism_score = _safe_float(
        result.get(
            "professionalism_score"
        )
    )

    delivery_score = _safe_float(
        result.get(
            "delivery_score"
        )
    )


    # ========================================================
    # FILLER CONTROL SCORE
    # ========================================================

    filler_rate = filler_data[
        "rate_percent"
    ]

    if filler_rate <= 2:
        filler_score = 100

    elif filler_rate <= 4:
        filler_score = 90

    elif filler_rate <= 7:
        filler_score = 75

    elif filler_rate <= 10:
        filler_score = 60

    elif filler_rate <= 15:
        filler_score = 40

    else:
        filler_score = 20


    # ========================================================
    # SPEAKING PACE SCORE
    # ========================================================

    if (
        110
        <= words_per_minute
        <= 165
    ):
        pace_score = 100

    elif (
        95
        <= words_per_minute
        < 110
        or
        165
        < words_per_minute
        <= 180
    ):
        pace_score = 85

    elif (
        80
        <= words_per_minute
        < 95
        or
        180
        < words_per_minute
        <= 195
    ):
        pace_score = 70

    else:
        pace_score = 50


    # ========================================================
    # QUESTION SCORE
    #
    # 45% answer substance
    # 25% relevance + structure
    # 30% speaking delivery
    # ========================================================

    substance_component = (
        content_score
    )

    reasoning_component = (
        relevance_score
        + structure_score
    ) / 2

    spoken_component = (
        clarity_score
        + confidence_score
        + professionalism_score
        + delivery_score
        + filler_score
        + pace_score
    ) / 6

    question_score = round(
        (
            substance_component
            * 0.45

            + reasoning_component
            * 0.25

            + spoken_component
            * 0.30
        ),
        1,
    )

    return {
        "question_id":
            question.get(
                "id"
            ),

        "transcript":
            transcript,

        "duration_seconds":
            round(
                duration_seconds,
                1,
            ),

        "word_count":
            word_count,

        "words_per_minute":
            words_per_minute,

        "filler_words":
            filler_data[
                "counts"
            ],

        "filler_count":
            filler_data[
                "total"
            ],

        "filler_rate_percent":
            filler_rate,

        "long_pause_count":
            int(
                _safe_float(
                    result.get(
                        "long_pause_count"
                    )
                )
            ),

        "hesitation_level":
            str(
                result.get(
                    "hesitation_level",
                    "unknown",
                )
            ),

        "scores": {
            "content":
                round(
                    content_score,
                    1,
                ),

            "relevance":
                round(
                    relevance_score,
                    1,
                ),

            "structure":
                round(
                    structure_score,
                    1,
                ),

            "clarity":
                round(
                    clarity_score,
                    1,
                ),

            "confidence":
                round(
                    confidence_score,
                    1,
                ),

            "professionalism":
                round(
                    professionalism_score,
                    1,
                ),

            "delivery":
                round(
                    delivery_score,
                    1,
                ),

            "filler_control":
                filler_score,

            "speaking_pace":
                pace_score,
        },

        "question_score":
            question_score,

        "feedback":
            str(
                result.get(
                    "feedback",
                    "",
                )
            ),

        "strong_points":
            result.get(
                "strong_points",
                [],
            ),

        "improvements":
            result.get(
                "improvements",
                [],
            ),
    }

def _normalize_indexed_data(
    value: Any,
) -> dict[str, Any]:
    """
    Firebase Realtime Database may return numeric-keyed
    objects as Python lists.

    Convert either representation into:
        {"1": {...}, "2": {...}}
    """

    if isinstance(value, dict):
        return {
            str(key): item
            for key, item in value.items()
            if isinstance(item, dict)
        }

    if isinstance(value, list):
        return {
            str(index): item
            for index, item in enumerate(value)
            if (
                index > 0
                and isinstance(item, dict)
            )
        }

    return {}

# ============================================================
# FINAL INTERVIEW REPORT
# ============================================================

def generate_final_interview_evaluation(
    *,
    answers: dict[str, Any],
    questions: list[dict[str, Any]],
    company_name: str,
    position_title: str,
) -> dict[str, Any]:
    """
    Produce the final interview report after all seven
    questions have been completed.
    """
    answers = _normalize_indexed_data(
        answers
    )
    answer_list = []

    for question in questions:

        question_id = str(
            question.get(
                "id"
            )
        )

        answer = answers.get(
            question_id,
            {},
        )

        answer_list.append(
            {
                "question":
                    question.get(
                        "question"
                    ),

                "question_score":
                    answer.get(
                        "question_score"
                    ),

                "transcript":
                    answer.get(
                        "transcript"
                    ),

                "feedback":
                    answer.get(
                        "feedback"
                    ),

                "delivery_statistics": {
                    "word_count":
                        answer.get(
                            "word_count"
                        ),

                    "words_per_minute":
                        answer.get(
                            "words_per_minute"
                        ),

                    "filler_count":
                        answer.get(
                            "filler_count"
                        ),

                    "filler_rate_percent":
                        answer.get(
                            "filler_rate_percent"
                        ),

                    "long_pause_count":
                        answer.get(
                            "long_pause_count"
                        ),
                },
            }
        )

    valid_scores = [
        _safe_float(
            answer.get(
                "question_score"
            )
        )

        for answer in answers.values()

        if isinstance(
            answer,
            dict,
        )
    ]

    deterministic_score = (
        round(
            sum(valid_scores)
            / len(valid_scores),
            1,
        )

        if valid_scores

        else 0
    )

    prompt = f"""
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

    client = get_gemini_client()

    try:

        response = (
            client.models.generate_content(
                model=_gemini_model(),

                contents=prompt,

                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.25,
                ),
            )
        )

        result = _extract_json(
            response.text or ""
        )

    except Exception as error:

        raise InterviewEvaluationError(
            f"Could not create final interview evaluation: {error}"
        ) from error

    finally:
        client.close()

    # Gemini is NOT allowed to change this score.
    result[
        "overall_score"
    ] = deterministic_score

    result[
        "question_results"
    ] = answer_list

    return result
