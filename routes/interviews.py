"""Interview lifecycle, evaluation, review, and answer API routes."""

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from constants import WORKPLACE_SIMULATION_MODE
from services.career_service import POSITIONS_DATA, get_company_display_name
from services.backend_demo_interview_service import get_backend_demo_interview
from services.backend_demo_scenario_service import is_backend_demo
from services.interview_service import (
    InterviewEvaluationError,
    InterviewGenerationError,
    analyze_spoken_answer,
    generate_final_interview_evaluation,
    generate_interview_questions,
    normalize_interview_answers,
)
from services.simulation_storage import (
    complete_interview_attempt,
    create_interview_attempt,
    get_interview_attempt,
    get_simulation_attempt,
    save_interview_answer,
)

interviews_bp = Blueprint("interviews", __name__)

@interviews_bp.post("/simulation/attempts/<attempt_id>/interview/start")
def start_interview(attempt_id):
    """
    Start a fresh interview from a completed workplace simulation.
    """

    user_id = session.get("user_id")

    attempt = get_simulation_attempt(
        user_id=user_id,
        attempt_id=attempt_id,
    )

    if (
        not attempt
        or attempt.get("simulation_mode") != WORKPLACE_SIMULATION_MODE
    ):
        return redirect(url_for("careers.career"))

    evaluation = attempt.get("evaluation")

    if not isinstance(evaluation, dict):
        return redirect(
            url_for(
                "simulations.workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    try:
        score = float(
            evaluation.get("overall_score", 0)
        )
    except (TypeError, ValueError):
        score = 0

    if score < current_app.config["INTERVIEW_UNLOCK_SCORE"]:
        return redirect(
            url_for(
                "simulations.workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    career_id = attempt.get("career_id", "")
    position_id = attempt.get("position_id", "")
    company_id = attempt.get("company_id", "")

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    if not position:
        return redirect(url_for("careers.career"))

    position_title = position.get(
        "title",
        position_id.replace("-", " ").title(),
    )

    company_name = get_company_display_name(
        career_id,
        position_id,
        company_id,
    )

    career_title = (
        career_id
        .replace("-", " ")
        .title()
    )

    try:
        if is_backend_demo(career_id, position_id, company_id):
            generated = get_backend_demo_interview()
        else:
            generated = generate_interview_questions(
                workplace_attempt=attempt,
                career_title=career_title,
                position_title=position_title,
                company_name=company_name,
            )

        interview_id = create_interview_attempt(
            user_id=user_id,
            source_attempt_id=attempt_id,
            career_id=career_id,
            position_id=position_id,
            company_id=company_id,
            interview_data=generated,
        )

    except InterviewGenerationError as error:
        current_app.logger.exception(
            "Interview generation failed: %s",
            error,
        )

        return redirect(
            url_for(
                "simulations.workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    except Exception:
        current_app.logger.exception(
            "Could not create interview."
        )

        return redirect(
            url_for(
                "simulations.workplace_task_review",
                attempt_id=attempt_id,
            )
        )

    return redirect(
        url_for(
            "interviews.interview_workspace",
            interview_id=interview_id,
        )
    )

@interviews_bp.get("/interview/<interview_id>")
def interview_workspace(interview_id):
    """
    Display the active AI job interview.
    """

    user_id = session.get("user_id")

    interview = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )

    if not interview:
        return redirect(
            url_for("careers.career")
        )

    # If the interview is already complete,
    # send the user directly to the results.
    if interview.get("status") == "completed":
        return redirect(
            url_for(
                "interviews.interview_review",
                interview_id=interview_id,
            )
        )

    if interview.get("status") != "in_progress":
        return redirect(
            url_for("careers.career")
        )

    questions = interview.get(
        "public_questions",
        [],
    )

    if not isinstance(questions, list) or not questions:
        return redirect(
            url_for("careers.career")
        )

    career_id = interview.get(
        "career_id",
        "",
    )

    position_id = interview.get(
        "position_id",
        "",
    )

    company_id = interview.get(
        "company_id",
        "",
    )

    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )

    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " ",
        ).title(),
    )

    company_name = get_company_display_name(
        career_id,
        position_id,
        company_id,
    )


    # --------------------------------------------------------
    # RECOVER A FINISHED INTERVIEW
    # --------------------------------------------------------
    #
    # Firebase may already contain all 7 answers even when
    # final report generation previously failed.
    #
    # In that case current_question becomes 8. Instead of
    # trapping the candidate, automatically finish the report.

    try:
        current_question = int(
            interview.get(
                "current_question",
                1,
            )
        )
    except (TypeError, ValueError):
        current_question = 1

    if current_question > len(questions):

        answers = normalize_interview_answers(interview.get("answers", {}))

        if len(answers) >= len(questions):

            try:

                final_evaluation = (
                    generate_final_interview_evaluation(
                        answers=answers,
                        questions=questions,
                        company_name=company_name,
                        position_title=position_title,
                    )
                )

                overall_score = (
                    final_evaluation.get(
                        "overall_score",
                        0,
                    )
                )

                complete_interview_attempt(
                    user_id=user_id,
                    interview_id=interview_id,
                    overall_score=overall_score,
                    evaluation=final_evaluation,
                )

                return redirect(
                    url_for(
                        "interviews.interview_review",
                        interview_id=interview_id,
                    )
                )

            except InterviewEvaluationError as error:

                current_app.logger.warning(
                    "Interview recovery evaluation failed: %s",
                    error,
                )


    return render_template(
        "interview.html",

        interview_id=interview_id,

        interview_title=interview.get(
            "interview_title",
            f"{position_title} Interview",
        ),

        opening_message=interview.get(
            "opening_message",
            "Welcome to your CareerGrid interview.",
        ),

        questions=questions,

        career_id=career_id,
        position_id=position_id,
        company_id=company_id,

        position_title=position_title,
        company_name=company_name,

        user_name=session.get(
            "user_name",
            "User",
        ),
    )


def _parse_interview_form_number(field_name, converter, default):
    """Parse one numeric multipart field without propagating malformed input."""

    try:
        return converter(request.form.get(field_name, "0"))
    except (TypeError, ValueError):
        return default


def _resolve_interview_rubric(rubrics, question_id):
    """Read a private rubric from either Firebase's list or mapping shape."""

    if isinstance(rubrics, list):
        if (
            0 <= question_id < len(rubrics)
            and isinstance(rubrics[question_id], dict)
        ):
            return rubrics[question_id]
        return {}

    if isinstance(rubrics, dict):
        return rubrics.get(str(question_id), rubrics.get(question_id, {}))

    return {}


def _normalize_speech_measurements(
    *,
    duration_seconds,
    speaking_seconds,
    silence_seconds,
    silence_ratio,
    long_pause_count,
    longest_pause_seconds,
):
    """Clamp browser-measured speech metrics before saving them."""

    return {
        "duration_seconds": round(max(duration_seconds, 0), 2),
        "speaking_seconds": round(max(speaking_seconds, 0), 2),
        "silence_seconds": round(max(silence_seconds, 0), 2),
        "silence_ratio": round(max(0, min(silence_ratio, 1)), 4),
        "long_pause_count": max(long_pause_count, 0),
        "longest_pause_seconds": round(max(longest_pause_seconds, 0), 2),
    }


@interviews_bp.post("/api/interview/<interview_id>/answer")
def submit_interview_answer(interview_id):

    user_id = session.get("user_id")

    interview = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )

    if not interview:
        return jsonify(
            {
                "error":
                "Interview attempt not found."
            }
        ), 404


    if interview.get("status") != "in_progress":
        return jsonify(
            {
                "error":
                "This interview is already completed."
            }
        ), 400


    question_id = _parse_interview_form_number("question_id", int, None)
    if question_id is None:
        return jsonify(
            {
                "error":
                "Invalid question ID."
            }
        ), 400

    duration_seconds = _parse_interview_form_number(
        "duration_seconds", float, 0
    )
    speaking_seconds = _parse_interview_form_number(
        "speaking_seconds", float, 0
    )
    silence_seconds = _parse_interview_form_number(
        "silence_seconds", float, 0
    )
    silence_ratio = _parse_interview_form_number("silence_ratio", float, 0)
    measured_long_pause_count = _parse_interview_form_number(
        "long_pause_count", int, 0
    )
    longest_pause_seconds = _parse_interview_form_number(
        "longest_pause_seconds", float, 0
    )
    audio_file = request.files.get(
        "audio"
    )


    if not audio_file:
        return jsonify(
            {
                "error":
                "No microphone recording was received."
            }
        ), 400


    audio_bytes = audio_file.read()


    if not audio_bytes:
        return jsonify(
            {
                "error":
                "The microphone recording was empty."
            }
        ), 400


    # Keep uploads reasonably bounded.
    if len(audio_bytes) > current_app.config["MAX_INTERVIEW_AUDIO_BYTES"]:
        return jsonify(
            {
                "error":
                "The recording is too large."
            }
        ), 413


    questions = interview.get(
        "public_questions",
        [],
    )


    question = next(
        (
            item
            for item in questions
            if int(
                item.get(
                    "id",
                    0,
                )
            ) == question_id
        ),
        None,
    )


    if not question:
        return jsonify(
            {
                "error":
                "Interview question not found."
            }
        ), 404


    expected_question = int(
        interview.get(
            "current_question",
            1,
        )
    )


    if question_id != expected_question:
        return jsonify(
            {
                "error":
                "Please answer the current interview question."
            }
        ), 409


    rubrics = interview.get(
        "private_rubrics",
        {},
    )
    rubric = _resolve_interview_rubric(rubrics, question_id)

    career_id = interview.get(
        "career_id",
        "",
    )

    position_id = interview.get(
        "position_id",
        "",
    )

    company_id = interview.get(
        "company_id",
        "",
    )


    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )


    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " ",
        ).title(),
    )


    company_name = get_company_display_name(
        career_id,
        position_id,
        company_id,
    )


    mime_type = (
        audio_file.mimetype
        or "audio/webm"
    )


    try:

        analysis = analyze_spoken_answer(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            question=question,
            rubric=rubric,
            duration_seconds=duration_seconds,
            company_name=company_name,
            position_title=position_title,
        )

        analysis["speech_measurements"] = _normalize_speech_measurements(
            duration_seconds=duration_seconds,
            speaking_seconds=speaking_seconds,
            silence_seconds=silence_seconds,
            silence_ratio=silence_ratio,
            long_pause_count=measured_long_pause_count,
            longest_pause_seconds=longest_pause_seconds,
        )

        # Prefer actual browser-measured pauses over
        # the model's estimate from the recording.
        analysis["long_pause_count"] = max(
            measured_long_pause_count,
            0,
        )


        save_interview_answer(
            user_id=user_id,
            interview_id=interview_id,
            question_id=question_id,
            answer_data=analysis,
        )


    except InterviewEvaluationError as error:

        current_app.logger.warning(
            "Interview answer evaluation failed: %s",
            error,
        )

        return jsonify(
            {
                "error":
                "CareerGrid could not evaluate your recording. Please try again."
            }
        ), 503


    except Exception as error:

        current_app.logger.exception(
            "Could not save interview answer (type=%s).",
            type(error).__name__,
        )

        return jsonify(
            {
                "error": "Could not save your interview answer. Please try again."
            }
        ), 500


    # -----------------------------------------------------
    # If there are more questions, continue.
    # -----------------------------------------------------

    if question_id < len(questions):

        return jsonify(
            {
                "saved": True,
                "completed": False,
                "question_score":
                    analysis.get(
                        "question_score"
                    ),
            }
        )


    # -----------------------------------------------------
    # Final question completed.
    # Generate overall report.
    # -----------------------------------------------------

    refreshed = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )


    answers = (
        refreshed.get(
            "answers",
            {},
        )
        if refreshed
        else {}
    )


    try:

        final_evaluation = (
            generate_final_interview_evaluation(
                answers=answers,
                questions=questions,
                company_name=company_name,
                position_title=position_title,
            )
        )


        overall_score = (
            final_evaluation.get(
                "overall_score",
                0,
            )
        )


        complete_interview_attempt(
            user_id=user_id,
            interview_id=interview_id,
            overall_score=overall_score,
            evaluation=final_evaluation,
        )


    except InterviewEvaluationError as error:

        current_app.logger.warning(
            "Final interview evaluation failed: %s",
            error,
        )

        return jsonify(
            {
                "error":
                "Your answers were saved, but CareerGrid could not create the final report."
            }
        ), 503


    return jsonify(
        {
            "saved": True,
            "completed": True,

            "review_url": url_for(
                "interviews.interview_review",
                interview_id=interview_id,
            ),
        }
    )

@interviews_bp.get("/interview/<interview_id>/review")
def interview_review(interview_id):

    user_id = session.get("user_id")

    interview = get_interview_attempt(
        user_id=user_id,
        interview_id=interview_id,
    )

    if not interview:
        return redirect(
            url_for("careers.career")
        )


    if interview.get("status") != "completed":

        return redirect(
            url_for(
                "interviews.interview_workspace",
                interview_id=interview_id,
            )
        )


    evaluation = interview.get(
        "evaluation",
        {},
    )


    questions = interview.get(
        "public_questions",
        [],
    )


    answers = normalize_interview_answers(interview.get("answers", {}))


    career_id = interview.get(
        "career_id",
        "",
    )

    position_id = interview.get(
        "position_id",
        "",
    )

    company_id = interview.get(
        "company_id",
        "",
    )


    position = (
        POSITIONS_DATA
        .get(career_id, {})
        .get(position_id, {})
    )


    position_title = position.get(
        "title",
        position_id.replace(
            "-",
            " ",
        ).title(),
    )


    company_name = get_company_display_name(
        career_id,
        position_id,
        company_id,
    )


    question_results = []

    for question in questions:

        question_id = str(
            question.get("id")
        )

        answer = answers.get(
            question_id,
            {},
        )

        question_results.append(
            {
                "question":
                    question.get(
                        "question"
                    ),

                "category":
                    question.get(
                        "category"
                    ),

                "score":
                    answer.get(
                        "question_score",
                        0,
                    ),

                "transcript":
                    answer.get(
                        "transcript",
                        "",
                    ),

                "feedback":
                    answer.get(
                        "feedback",
                        "",
                    ),

                "word_count":
                    answer.get(
                        "word_count",
                        0,
                    ),

                "words_per_minute":
                    answer.get(
                        "words_per_minute",
                        0,
                    ),

                "filler_count":
                    answer.get(
                        "filler_count",
                        0,
                    ),

                "filler_rate_percent":
                    answer.get(
                        "filler_rate_percent",
                        0,
                    ),

                "long_pause_count":
                    answer.get(
                        "long_pause_count",
                        0,
                    ),
            }
        )


    return render_template(
        "interview_review.html",

        interview_id=interview_id,

        evaluation=evaluation,

        overall_score=evaluation.get(
            "overall_score",
            0,
        ),

        company_name=company_name,

        position_title=position_title,

        question_results=question_results,

        strengths=evaluation.get(
            "strengths",
            [],
        ),

        areas_for_improvement=evaluation.get(
            "areas_for_improvement",
            [],
        ),

        next_steps=evaluation.get(
            "next_steps",
            [],
        ),
    )
