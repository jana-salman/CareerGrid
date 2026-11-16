import { Link } from 'react-router-dom'

import { finalReportPath } from './state/reportMail.js'
import { SUBMISSION_OPTIONS, submissionState } from './state/submissionWorkflow.js'

const DEFAULT_DELIVERABLES = [
  'Committed and pushed code changes that meet the requirements',
  'A reply to the task email summarising what you found, what you changed, and how you checked it',
]

function textList(value) {
  return Array.isArray(value) ? value.map((item) => String(item || '').trim()).filter(Boolean) : []
}

function WorkspaceBrief({ attempt, repository, onOpenApp, onClose }) {
  const scenario = attempt.public_scenario || {}
  const task = scenario.task || {}
  const project = scenario.project || {}
  const resources = (scenario.resources || []).map((item) => item?.name).filter(Boolean)
  const requirements = textList(task.requirements)
  const deliverables = textList(task.deliverables).length ? textList(task.deliverables) : DEFAULT_DELIVERABLES
  const criteria = textList(task.acceptance_criteria)
  const state = submissionState(repository, task.id)
  const extracted = Boolean(repository.workspace?.projectExtracted)
  const notice = scenario.simulation_notice || scenario.fictional_company_notice
    || 'Practice simulation: the company, people, and code are fictional. This is not a real employer assignment.'

  return (
    <aside className="workspace-brief" aria-labelledby="workspace-brief-title">
      <header className="workspace-brief-header">
        <div>
          <small>Task brief</small>
          <h2 id="workspace-brief-title">{task.subject || scenario.title || 'Workplace task'}</h2>
        </div>
        <button type="button" className="workspace-brief-close" aria-label="Hide task brief" onClick={onClose}>×</button>
      </header>
      <p className="workspace-brief-notice">{notice}</p>

      <section>
        <h3>1. The task</h3>
        <p>{task.summary || 'Read the task email in Mail for the full request.'}</p>
        {requirements.length > 0 && <ul>{requirements.map((item) => <li key={item}>{item}</li>)}</ul>}
        <button type="button" className="workspace-brief-link" onClick={() => onOpenApp('mail')}>Open the task email</button>
      </section>

      <section>
        <h3>2. Starter project and resources</h3>
        <p>
          Attached to the task email: <strong>{project.archive_name || 'project archive'}</strong>
          {resources.length > 0 && <> plus {resources.join(', ')}</>}.
        </p>
        <p>
          {extracted
            ? <>Extracted to <code>{repository.rootPath}</code>. Edit in VS Code; use the Terminal for Git.</>
            : <>Download it in Mail, then open Files → Downloads and choose <strong>Extract</strong>.</>}
        </p>
        <button type="button" className="workspace-brief-link" onClick={() => onOpenApp(extracted ? 'vscode' : 'files')}>{extracted ? 'Open VS Code' : 'Open Files'}</button>
      </section>

      <section>
        <h3>3. What to deliver</h3>
        <ul>{deliverables.map((item) => <li key={item}>{item}</li>)}</ul>
        {criteria.length > 0 && <><p className="workspace-brief-subhead">How it will be assessed</p><ul>{criteria.map((item) => <li key={item}>{item}</li>)}</ul></>}
      </section>

      <section>
        <h3>4. How to submit</h3>
        <details>
          <summary>Option A - pull request</summary>
          <ol>{SUBMISSION_OPTIONS.pullRequest.map((step) => <li key={step}>{step}</li>)}</ol>
        </details>
        <details>
          <summary>Option B - directly on main</summary>
          <ol>{SUBMISSION_OPTIONS.main.map((step) => <li key={step}>{step}</li>)}</ol>
        </details>
        <p>Only committed and pushed work is reviewed. You will be asked to confirm before the review starts, and the submitted version is then frozen.</p>
      </section>

      <section>
        <h3>5. Status and feedback</h3>
        <p role="status" aria-live="polite" className={`workspace-brief-status is-${state.stage}`}>{state.label}</p>
        {state.stage === 'evaluated'
          ? <Link className="workspace-brief-link" to={finalReportPath(attempt.attempt_id)}>Open feedback and personalized roadmap</Link>
          : <p>Your review and personalized roadmap arrive as a reply in the task email thread, with a link to the full report.</p>}
      </section>
    </aside>
  )
}

export default WorkspaceBrief
