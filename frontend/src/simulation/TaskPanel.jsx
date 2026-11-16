import { useState } from 'react'
import { Link } from 'react-router-dom'
import { saveFrontendSimulationProgress } from '../services/simulationApi.js'
import { branchSyncStatus, diffSnapshots, pushedCommit } from './state/repositoryModel.js'

const defaultLabels = ['Triage the production report', 'Investigate across viewports', 'Implement the fix', 'Verify behavior and regressions', 'Deliver for review (pull request or main)']
const fields = [[['selected_email_id', 'Critical email ID'], ['selected_priority', 'Priority'], ['selected_action', 'First action'], ['written_response', 'Reply to the frontend lead', true]], [['viewports_tested', 'Viewports'], ['evidence_opened', 'Evidence inspected'], ['selected_root_cause', 'Root cause'], ['proposed_next_action', 'Proposed next action', true], ['investigation_summary', 'Investigation summary', true]], [['files_opened', 'Files opened'], ['fix_explanation', 'What you changed and why it is safe', true]], [['commands_run', 'Commands you ran (self-reported)'], ['tests_performed', 'Behavior checks you did (self-reported)'], ['viewport_checks', 'Viewports'], ['accessibility_checks', 'Accessibility checks'], ['release_decision', 'Release decision']], [['reviewed_files', 'Reviewed changed files'], ['commit_message', 'Commit message'], ['pr_title', 'Pull request title', false, 'pull_request'], ['pr_description', 'Pull request description', true, 'pull_request'], ['testing_checklist', 'Testing checklist'], ['release_recommendation', 'Release recommendation'], ['final_team_message', 'Final team update', true]]]

// Files the participant changed and saved in VS Code, compared with the
// original project. Their final contents are what CareerGrid checks.
function workspaceChanges(repository) {
  if (!repository?.baseline?.snapshot) return {}
  const branch = repository.branches[repository.currentBranch]
  return Object.fromEntries(
    diffSnapshots(repository.baseline.snapshot, branch.workingTree)
      .filter((change) => change.status !== 'deleted')
      .map((change) => [change.path, change.after]),
  )
}

function deliveryEvidence(repository, mode) {
  if (!repository) return { pushed: false }
  const pullRequest = [...repository.pullRequests].reverse().find((item) => item.status === 'open')
  const branch = mode === 'pull_request' && pullRequest ? pullRequest.compareBranch : repository.defaultBranch
  const pushed = pushedCommit(repository, branch)
  const status = branchSyncStatus(repository, branch)
  return {
    branch,
    commit_id: pushed?.id || '',
    pull_request_url: mode === 'pull_request' ? pullRequest?.url || '' : '',
    pushed: Boolean(pushed) && !status?.unpushedCommits.length,
    uncommitted_files: status?.uncommittedPaths || [],
  }
}

const list = (value) =>
  String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

function buildStepPayload(step, value, repository) {
  if (step === 1) {
    return {
      opened_email_ids: [value('selected_email_id')],
      selected_email_id: value('selected_email_id'),
      selected_priority: value('selected_priority'),
      selected_action: value('selected_action'),
      written_response: value('written_response'),
    }
  }

  if (step === 2) {
    return {
      pages_inspected: ['product'],
      viewports_tested: list(value('viewports_tested')),
      evidence_opened: list(value('evidence_opened')),
      selected_root_cause: value('selected_root_cause'),
      proposed_next_action: value('proposed_next_action'),
      investigation_summary: value('investigation_summary'),
    }
  }

  if (step === 3) {
    return {
      files_opened: list(value('files_opened')),
      changed_files: workspaceChanges(repository),
      fix_explanation: value('fix_explanation'),
    }
  }

  if (step === 4) {
    return {
      commands_run: list(value('commands_run')),
      tests_performed: list(value('tests_performed')),
      viewport_checks: list(value('viewport_checks')),
      accessibility_checks: list(value('accessibility_checks')),
      release_decision: value('release_decision'),
    }
  }

  const mode = value('delivery_mode') || 'pull_request'
  return {
    delivery_mode: mode,
    delivery_evidence: deliveryEvidence(repository, mode),
    reviewed_files: list(value('reviewed_files')),
    commit_message: value('commit_message'),
    pr_title: value('pr_title'),
    pr_description: value('pr_description'),
    testing_checklist: list(value('testing_checklist')),
    release_recommendation: value('release_recommendation'),
    final_team_message: value('final_team_message'),
  }
}

function TaskPanel({ attempt, progress, repository, onProgress = () => {} }) {
  const scenario = attempt.public_scenario || {}
  const labels = defaultLabels.map((label, index) => scenario.frontend_tasks?.[index]?.title || label)
  const notice = scenario.simulation_notice || scenario.fictional_company_notice
  const [liveProgress, setLiveProgress] = useState(progress)
  const current = liveProgress || progress
  const step = Number(current?.current_step || 1)
  const complete = current?.status === 'completed' || Boolean(current?.evaluation)
  const [values, setValues] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const prior = current?.responses?.[`step_${step}`] || {}
  const value = (name) => values[name] ?? prior[name] ?? ''

  const submit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = buildStepPayload(step, value, repository)
      if (step === 3 && !Object.keys(payload.changed_files).length) {
        throw new Error('No saved changes found. Edit the project files in VS Code and save them first.')
      }
      const result = await saveFrontendSimulationProgress(attempt.attempt_id, step, payload)
      const next = result.evaluation
        ? {
            ...current,
            status: 'completed',
            evaluation: result.evaluation,
            responses: { ...current.responses, [`step_${step}`]: result.response },
          }
        : {
            ...current,
            current_step: step + 1,
            responses: { ...current.responses, [`step_${step}`]: result.response },
          }
      setLiveProgress(next)
      onProgress(next)
      setValues({})
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <aside className="frontend-task-panel">
      <small>FRONTEND WORKPLACE - TASK {Math.min(step, 5)} OF 5</small>
      <h2>{complete ? 'Frontend simulation complete' : labels[step - 1]}</h2>
      {notice && <p className="frontend-task-note">{notice}</p>}
      <div className="frontend-task-progress">
        {Array.from({ length: 5 }, (_, index) => (
          <span className={index + 1 <= step ? 'done' : ''} key={index} />
        ))}
      </div>
      {complete ? (
        <Link className="frontend-task-submit" to={`/simulation/attempts/${encodeURIComponent(attempt.attempt_id)}/report`}>
          Open feedback and personalized roadmap
        </Link>
      ) : (
        <form onSubmit={submit}>
          {step === 3 && (
            <div>
              <small>Saved changes CareerGrid will check:</small>
              <ul className="frontend-task-changes">
                {Object.keys(workspaceChanges(repository)).map((path) => <li key={path}>{path}</li>)}
                {!Object.keys(workspaceChanges(repository)).length && <li>None yet - edit and save files in VS Code.</li>}
              </ul>
            </div>
          )}
          {step === 5 && (
            <label>
              Delivery method
              <select value={value('delivery_mode') || 'pull_request'} onChange={(e) => setValues({ ...values, delivery_mode: e.target.value })}>
                <option value="pull_request">Pull request (branch, push, open PR)</option>
                <option value="main">Directly on main (commit and push main)</option>
              </select>
              <small className="frontend-task-note">
                {(value('delivery_mode') || 'pull_request') === 'main'
                  ? 'Commit and push on main in the Terminal first. Only pushed work counts.'
                  : 'Push your branch and open the pull request in GitHub first.'}
              </small>
            </label>
          )}
          {fields[step - 1]
            .filter(([, , , onlyFor]) => !onlyFor || onlyFor === (value('delivery_mode') || 'pull_request'))
            .map(([name, label, area]) => (
            <label key={name}>
              {label}
              {area ? (
                <textarea required value={value(name)} onChange={(e) => setValues({ ...values, [name]: e.target.value })} />
              ) : (
                <input required value={value(name)} onChange={(e) => setValues({ ...values, [name]: e.target.value })} />
              )}
            </label>
          ))}
          {step === 4 && <p className="frontend-task-note">The workspace cannot run commands. What you list here is recorded as your own report; CareerGrid separately checks your saved files.</p>}
          <p className="frontend-task-error">{error}</p>
          <button className="frontend-task-submit" disabled={saving} type="submit">
            {saving ? 'Saving...' : 'Save and continue'}
          </button>
        </form>
      )}
    </aside>
  )
}

export default TaskPanel
