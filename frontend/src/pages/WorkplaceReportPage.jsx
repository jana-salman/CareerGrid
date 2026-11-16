import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getWorkplaceReport } from '../services/dashboardApi.js'
import { readableList, roadmapForDisplay } from './reportRoadmap.js'

function scoreCopy(score) {
  if (score >= 80) return ['score-label--strong', 'Strong Performance', "You're showing strong readiness for this role."]
  if (score >= 60) return ['score-label--developing', 'Developing', 'Good progress — keep strengthening the areas below.']
  return ['score-label--practice', 'Needs More Practice', 'Review the feedback and try the workplace task again.']
}

function formatDimensionName(name) {
  return name
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function Section({ children, className = '', kicker, title }) {
  return (
    <section className={`review-section${className ? ` ${className}` : ''}`}>
      <div className="section-heading">
        <span>{kicker}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  )
}

function ListSection({ kicker, title, items }) {
  return (
    <Section className="feedback-card" kicker={kicker} title={title}>
      <ul className="feedback-list">
        {items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
      </ul>
    </Section>
  )
}

function WorkplaceReportPage() {
  const { attemptId } = useParams()
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const stylesheet = [...document.querySelectorAll('link[rel="stylesheet"]')].find(
      (link) => link.getAttribute('href') === '/static/css/task_review.css',
    )
    const originalPosition = stylesheet?.parentNode
      ? document.createComment('task-review-stylesheet-position')
      : null

    document.body.classList.add('workplace-report-route')
    if (stylesheet?.parentNode && originalPosition) {
      stylesheet.parentNode.insertBefore(originalPosition, stylesheet)
      document.head.appendChild(stylesheet)
    }

    return () => {
      document.body.classList.remove('workplace-report-route')
      if (stylesheet && originalPosition?.parentNode) {
        originalPosition.parentNode.replaceChild(stylesheet, originalPosition)
      }
    }
  }, [])

  useEffect(() => {
    let active = true
    getWorkplaceReport(attemptId)
      .then((data) => active && setReport(data))
      .catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [attemptId])

  if (error) return <main className="review-page"><p>{error}</p></main>
  if (!report) return <main className="review-page"><p>Loading your task review...</p></main>

  const evaluation = report.evaluation
  const score = Number(evaluation.overall_score) || 0
  const [labelClass, label, heading] = scoreCopy(score)
  const roadmap = roadmapForDisplay(evaluation)
  const strengths = readableList(report.strengths)
  const improvements = readableList(report.areas_for_improvement)
  const nextSteps = readableList(report.recommended_next_steps)

  return (
    <main className="review-page">
      <nav className="review-nav">
        <Link className="review-brand" to="/career">
          <span className="review-brand-icon">CG</span>
          <span>CareerGrid</span>
        </Link>
        <Link className="back-workspace-link" to={`/workspace/attempt/${encodeURIComponent(attemptId)}`}>
          ← Back to workspace
        </Link>
      </nav>

      <section className="review-container">
        <header className="review-header">
          <span className="review-kicker">CareerGrid · Task Review Report</span>
          <h1>{report.task_title}</h1>
          <p className="review-context">
            {report.position_title} <span>·</span> {report.company_name}
          </p>

          <div className="score-section">
            <div className="score-circle">
              <strong>{score}</strong>
              <span>/ 100</span>
            </div>
            <div className="score-copy">
              <span className={`score-label ${labelClass}`}>{label}</span>
              <h2>{heading}</h2>
            </div>
          </div>
        </header>

        {evaluation.summary && (
          <Section kicker="Overview" title="Overall Assessment">
            <p className="assessment-copy">{evaluation.summary}</p>
          </Section>
        )}

        {evaluation.dimensions && (
          <Section kicker="Detailed Evaluation" title="Performance Breakdown">
            <div className="performance-grid">
              {Object.entries(evaluation.dimensions).map(([name, dimension]) => (
                <article className="performance-card" key={name}>
                  <div className="performance-card-header">
                    <h3>{formatDimensionName(name)}</h3>
                    <strong>{dimension.score ?? '—'} / {dimension.max_score ?? 10}</strong>
                  </div>
                  {dimension.feedback && <p>{dimension.feedback}</p>}
                </article>
              ))}
            </div>
          </Section>
        )}

        {evaluation.submission_overview && (
          <Section kicker="What Was Reviewed" title="Submitted Work">
            <ul className="feedback-list">
              <li>Delivery: {evaluation.submission_overview.mode === 'main' ? 'Committed and pushed directly to main' : 'Pull request from a feature branch'}</li>
              {evaluation.submission_overview.branch && <li>Branch: {evaluation.submission_overview.branch}{evaluation.submission_overview.commit_id ? ` · commit ${evaluation.submission_overview.commit_id}` : ''}</li>}
              {evaluation.submission_overview.pull_request_url && <li>Pull request: {evaluation.submission_overview.pull_request_url}</li>}
              {evaluation.submission_overview.changed_files?.length > 0 && <li>Files changed from the original project: {evaluation.submission_overview.changed_files.join(', ')}</li>}
            </ul>
          </Section>
        )}

        {evaluation.git_workflow_feedback && (
          <Section kicker="Assessed Separately" title="Git Workflow Feedback">
            <p className="assessment-copy">{evaluation.git_workflow_feedback}</p>
          </Section>
        )}

        {evaluation.verification_note && <p className="assessment-copy report-verification-note">{evaluation.verification_note}</p>}

        <div className="feedback-columns">
          {strengths.length > 0 && (
            <ListSection kicker="What Went Well" title="Strengths" items={strengths} />
          )}
          {improvements.length > 0 && (
            <ListSection
              kicker="Your Next Focus"
              title="Areas for Improvement"
              items={improvements}
            />
          )}
        </div>

        {evaluation.advisor_feedback && (
          <Section className="advisor-section" kicker="CareerGrid Advisor" title="Advisor Feedback">
            <p>{evaluation.advisor_feedback}</p>
          </Section>
        )}

        {roadmap.status === 'available' && (
          <Section kicker="Your Personalized Roadmap" title="Skill Gaps and Next Learning Steps">
            <div className="performance-grid">
              {roadmap.items.map((item, index) => (
                <article className="performance-card roadmap-card" key={`${index}-${item.skill}`}>
                  <div className="performance-card-header"><h3>{item.skill}</h3></div>
                  {item.evidence && <p><strong>Evidence from your submission:</strong> {item.evidence}</p>}
                  {item.gap && <p><strong>Gap:</strong> {item.gap}</p>}
                  <h4 className="roadmap-subheading">Next steps</h4>
                  <ol className="roadmap-steps">
                    {item.steps.map((step, stepIndex) => <li key={`${stepIndex}-${step}`}>{step}</li>)}
                  </ol>
                  <h4 className="roadmap-subheading">Free learning resources</h4>
                  {item.resources.length > 0 ? (
                    <ul className="roadmap-resources">
                      {item.resources.map((resource) => (
                        <li key={resource.url}>
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`${resource.title}${resource.provider ? ` by ${resource.provider}` : ''} (opens in a new tab)`}
                          >
                            {resource.title} <span aria-hidden="true">↗</span>
                          </a>
                          {resource.provider && <span className="roadmap-resource-provider">{resource.provider}</span>}
                          {resource.relevance && <p>{resource.relevance}</p>}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="roadmap-empty">No suitable free learning resource is listed for this skill yet.</p>
                  )}
                </article>
              ))}
            </div>
          </Section>
        )}

        {roadmap.status === 'unavailable' && (
          <Section kicker="Your Personalized Roadmap" title="Roadmap Unavailable">
            <p className="assessment-copy roadmap-empty">
              The learning roadmap saved with this report could not be read, so it is not shown.
              Your score, performance breakdown, and feedback above are unaffected.
            </p>
          </Section>
        )}

        {nextSteps.length > 0 && (
          <Section kicker="Keep Growing" title="Recommended Next Steps">
            <ul className="next-step-list">
              {nextSteps.map((step, index) => (
                <li key={`${index}-${step}`}>
                  <span>{index + 1}</span>
                  <p>{step}</p>
                </li>
              ))}
            </ul>
          </Section>
        )}

        <section className="next-actions">
          <span className="next-actions-kicker">What's next?</span>
          <h2>Keep building your career skills.</h2>
          <p>Practice this role again, explore another career, or review your simulation history.</p>

          {report.interview_unlocked && (
            <form
              action={`/simulation/attempts/${encodeURIComponent(attemptId)}/interview/start`}
              method="post"
              className="interview-launch-form"
            >
              <button type="submit" className="interview-launch-btn">
                <span className="interview-launch-icon">🎙</span>
                <span className="interview-launch-content">
                  <strong>Start Job Interview</strong>
                  <small>Continue to your AI-powered interview simulation</small>
                </span>
                <span className="interview-launch-arrow">→</span>
              </button>
            </form>
          )}

          <div className="next-actions-buttons">
            <form action="/simulation/workplace/start" method="post">
              <input type="hidden" name="career_id" value={report.career_id} />
              <input type="hidden" name="position_id" value={report.position_id} />
              <input type="hidden" name="company_id" value={report.company_id} />
              <input type="hidden" name="job_source" value={report.job_source} />
              <input type="hidden" name="retry_attempt_id" value={attemptId} />
              <button className="review-button review-button--primary" type="submit">
                <span>↻</span>
                Try Again
              </button>
            </form>
            <Link className="review-button review-button--secondary" to="/career">
              Explore Careers
            </Link>
          </div>

          <Link className="dashboard-link" to="/dashboard">View Dashboard →</Link>
        </section>
      </section>
    </main>
  )
}

export default WorkplaceReportPage
