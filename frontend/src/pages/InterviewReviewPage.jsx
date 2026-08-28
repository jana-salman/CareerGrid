import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { getInterviewReview } from '../services/interviewApi.js'

const INTERVIEW_STYLESHEET = '/static/css/interview.css'

function useInterviewReviewStyles() {
  useEffect(() => {
    const existing = [...document.querySelectorAll('link[rel="stylesheet"]')].find(
      (link) => link.getAttribute('href') === INTERVIEW_STYLESHEET,
    )
    const stylesheet = existing || document.createElement('link')
    if (!existing) {
      stylesheet.rel = 'stylesheet'
      stylesheet.href = INTERVIEW_STYLESHEET
      document.head.appendChild(stylesheet)
    }

    document.body.classList.add('interview-route')

    return () => {
      document.body.classList.remove('interview-route')
      if (!existing) stylesheet.remove()
    }
  }, [])
}

function roundedScore(value) {
  const score = Number(value)
  return Number.isFinite(score) ? Math.round(score) : 0
}

function ReviewList({ items }) {
  return (
    <ul>
      {items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
    </ul>
  )
}

function InterviewReview({ review }) {
  return (
    <div className="interview-app">
      <header className="interview-header">
        <div className="brand">CareerGrid</div>
        <div className="interview-meta">
          <span>{review.company_name}</span>
          <span className="meta-dot" aria-hidden="true" />
          <span>{review.position_title}</span>
        </div>
      </header>

      <main className="interview-stage" aria-labelledby="interviewReviewHeading">
        <section className="question-card">
          <span className="question-category">INTERVIEW COMPLETE</span>
          <h2 id="interviewReviewHeading">Your interview performance</h2>
          <div
            className="final-score"
            aria-label={`Overall interview score: ${roundedScore(review.overall_score)} out of 100`}
          >
            {roundedScore(review.overall_score)}
            <span aria-hidden="true"> / 100</span>
          </div>
          <p>{review.summary}</p>
        </section>

        <section className="review-grid" aria-label="Interview feedback highlights">
          <article className="review-card">
            <span className="question-category">Strengths</span>
            <ReviewList items={review.strengths} />
          </article>

          <article className="review-card">
            <span className="question-category">Improve</span>
            <ReviewList items={review.areas_for_improvement} />
          </article>
        </section>

        <section className="review-card review-wide">
          <span className="question-category">Speaking performance</span>
          <p>{review.communication_feedback}</p>
        </section>

        <section className="review-card review-wide">
          <span className="question-category">Answer quality</span>
          <p>{review.content_feedback}</p>
        </section>

        <section className="question-review-list" aria-labelledby="questionAnalysisHeading">
          <div className="section-heading">
            <span className="question-category">QUESTION ANALYSIS</span>
            <h2 id="questionAnalysisHeading">Your answers</h2>
          </div>

          {review.question_results.map((item, index) => {
            const headingId = `interviewQuestionResult-${index}`
            return (
              <article className="answer-review-card" aria-labelledby={headingId} key={headingId}>
                <div className="answer-review-top">
                  <div>
                    <span className="question-category">{item.category}</span>
                    <h3 id={headingId}>{item.question}</h3>
                  </div>
                  <div
                    className="answer-score"
                    aria-label={`Question score: ${roundedScore(item.score)} out of 100`}
                  >
                    {roundedScore(item.score)} <small aria-hidden="true">/100</small>
                  </div>
                </div>

                <div className="speech-stats" aria-label="Speaking statistics">
                  <span>{item.word_count} words</span>
                  <span>{item.words_per_minute} WPM</span>
                  <span>{item.filler_count} fillers</span>
                  <span>{item.long_pause_count} long pauses</span>
                </div>

                <div className="answer-transcript">
                  <strong>What you said</strong>
                  <p>{item.transcript}</p>
                </div>

                <div className="answer-feedback">
                  <strong>CareerGrid feedback</strong>
                  <p>{item.feedback}</p>
                </div>
              </article>
            )
          })}
        </section>

        <section className="review-card review-wide">
          <span className="question-category">Recommended next steps</span>
          <ReviewList items={review.next_steps} />
        </section>

        <div className="interview-actions">
          <a
            href={review.explore_url}
            className="finish-answer-button"
            style={{ textDecoration: 'none', textAlign: 'center' }}
          >
            Explore More Careers
          </a>
        </div>
      </main>
    </div>
  )
}

function InterviewReviewPage() {
  const { interviewId } = useParams()
  const [review, setReview] = useState(null)
  const [error, setError] = useState('')

  useInterviewReviewStyles()

  useEffect(() => {
    let active = true
    getInterviewReview(interviewId)
      .then((data) => {
        if (!active) return
        if (data.status !== 'completed' && data.redirect_url) {
          window.location.replace(data.redirect_url)
          return
        }
        setReview(data)
      })
      .catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [interviewId])

  useEffect(() => {
    const previousTitle = document.title
    document.title = 'Interview Review | CareerGrid'
    return () => { document.title = previousTitle }
  }, [])

  if (error) {
    return <main className="interview-stage" role="alert"><p>{error}</p></main>
  }
  if (!review) {
    return (
      <main className="interview-stage" aria-busy="true" aria-live="polite">
        <p>Loading your interview review...</p>
      </main>
    )
  }

  return <InterviewReview review={review} />
}

export default InterviewReviewPage
