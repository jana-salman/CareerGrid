import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getWorkplaceReport } from '../services/dashboardApi.js'

function scoreCopy(score) {
  if (score >= 80) return ['score-label--strong', 'Strong Performance', "You're showing strong readiness for this role."]
  if (score >= 60) return ['score-label--developing', 'Developing', 'Good progress - keep strengthening the areas below.']
  return ['score-label--practice', 'Needs More Practice', 'Review the feedback and try the workplace task again.']
}

function Section({ children, className = '', kicker, title }) {
  return <section className={`review-section ${className}`}><div className="section-heading"><span>{kicker}</span><h2>{title}</h2></div>{children}</section>
}

function ListSection({ kicker, title, items }) {
  return <Section className="feedback-card" kicker={kicker} title={title}><ul className="feedback-list">{items.map((item) => <li key={item}>{item}</li>)}</ul></Section>
}

function WorkplaceReportPage() {
  const { attemptId } = useParams()
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    getWorkplaceReport(attemptId).then((data) => active && setReport(data)).catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [attemptId])
  if (error) return <main className="review-page"><p>{error}</p></main>
  if (!report) return <main className="review-page"><p>Loading your task review...</p></main>
  const evaluation = report.evaluation
  const score = Number(evaluation.overall_score) || 0
  const [labelClass, label, heading] = scoreCopy(score)
  return <main className="review-page"><nav className="review-nav"><Link className="review-brand" to="/career"><span className="review-brand-icon">CG</span><span>CareerGrid</span></Link><a className="back-workspace-link" href={`/workspace/attempt/${encodeURIComponent(attemptId)}`}>Back to workspace</a></nav><section className="review-container"><header className="review-header"><span className="review-kicker">CareerGrid - Task Review Report</span><h1>{report.task_title}</h1><p className="review-context">{report.position_title} <span>-</span> {report.company_name}</p><div className="score-section"><div className="score-circle"><strong>{score}</strong><span>/ 100</span></div><div className="score-copy"><span className={`score-label ${labelClass}`}>{label}</span><h2>{heading}</h2></div></div></header>{evaluation.summary && <Section kicker="Overview" title="Overall Assessment"><p className="assessment-copy">{evaluation.summary}</p></Section>}{evaluation.dimensions && <Section kicker="Detailed Evaluation" title="Performance Breakdown"><div className="performance-grid">{Object.entries(evaluation.dimensions).map(([name, dimension]) => <article className="performance-card" key={name}><div className="performance-card-header"><h3>{name.replaceAll('_', ' ')}</h3><strong>{dimension.score ?? '-'} / {dimension.max_score ?? 10}</strong></div>{dimension.feedback && <p>{dimension.feedback}</p>}</article>)}</div></Section>}<div className="feedback-columns">{report.strengths.length > 0 && <ListSection kicker="What Went Well" title="Strengths" items={report.strengths} />}{report.areas_for_improvement.length > 0 && <ListSection kicker="Your Next Focus" title="Areas for Improvement" items={report.areas_for_improvement} />}</div>{evaluation.advisor_feedback && <Section className="advisor-section" kicker="CareerGrid Advisor" title="Advisor Feedback"><p>{evaluation.advisor_feedback}</p></Section>}{report.recommended_next_steps.length > 0 && <Section kicker="Keep Growing" title="Recommended Next Steps"><ol className="next-step-list">{report.recommended_next_steps.map((step, index) => <li key={step}><span>{index + 1}</span><p>{step}</p></li>)}</ol></Section>}<section className="next-actions"><span className="next-actions-kicker">What's next?</span><h2>Keep building your career skills.</h2><p>Practice this role again, explore another career, or review your simulation history.</p>{report.interview_unlocked && <form action={`/simulation/attempts/${encodeURIComponent(attemptId)}/interview/start`} method="post" className="interview-launch-form"><button type="submit" className="interview-launch-btn"><span className="interview-launch-icon">Interview</span><span className="interview-launch-content"><strong>Start Job Interview</strong><small>Continue to your AI-powered interview simulation</small></span><span className="interview-launch-arrow">&rarr;</span></button></form>}<div className="next-actions-buttons"><form action="/simulation/workplace/start" method="post"><input type="hidden" name="career_id" value={report.career_id} /><input type="hidden" name="position_id" value={report.position_id} /><input type="hidden" name="company_id" value={report.company_id} /><button className="review-button review-button--primary" type="submit"><span>Retry</span>Try Again</button></form><Link className="review-button review-button--secondary" to="/career">Explore Careers</Link></div><Link className="dashboard-link" to="/dashboard">View Dashboard</Link></section></section></main>
}

export default WorkplaceReportPage
