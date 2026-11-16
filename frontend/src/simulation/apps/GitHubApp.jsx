import { useEffect, useState } from 'react'

import { branchSyncStatus, createPullRequest } from '../state/repositoryModel.js'
import { copyPullRequestLink } from '../state/pullRequestClipboard.js'
import { SUBMISSION_OPTIONS, submissionState } from '../state/submissionWorkflow.js'

function SyncStatus({ repository }) {
  const status = branchSyncStatus(repository, repository.currentBranch)
  if (!status) return null
  const items = []
  if (status.uncommittedPaths.length) items.push(`${status.uncommittedPaths.length} uncommitted file(s) - not visible on GitHub until committed and pushed`)
  if (status.unpushedCommits.length) items.push(`${status.unpushedCommits.length} local commit(s) not pushed yet - run git push`)
  if (!items.length) items.push(status.pushed ? `Branch ${status.branch} is up to date with GitHub` : `Branch ${status.branch} has not been pushed`)
  return <ul className="github-sync-status" aria-label="Branch status">{items.map((item) => <li key={item}>{item}</li>)}</ul>
}

function DeliveryGuide({ repository, taskId }) {
  const state = taskId ? submissionState(repository, taskId) : null
  return (
    <aside className="github-section github-delivery-guide" style={{ marginTop: 16 }}>
      <h3 className="github-section-title">Submitting your work</h3>
      <div className="github-section-body">
        {state && <p className="github-muted" role="status">Status: {state.label}</p>}
        <p><strong>Pull request:</strong> push a feature branch, click Create Pull Request, then email the link from Mail.</p>
        <p><strong>Directly on main:</strong> commit and push on main, then reply to the task email that the work is ready on main. No link is needed.</p>
        <details><summary>Step-by-step</summary>
          <p>Pull request</p><ol>{SUBMISSION_OPTIONS.pullRequest.map((step) => <li key={step}>{step}</li>)}</ol>
          <p>Main</p><ol>{SUBMISSION_OPTIONS.main.map((step) => <li key={step}>{step}</li>)}</ol>
        </details>
      </div>
    </aside>
  )
}

function GitHubApp({ repository, taskId, onRepositoryChange }) {
  const [activeTab, setActiveTab] = useState('code')
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const current = repository.branches[repository.currentBranch]
  const pushed = repository.remote.pushedBranches.includes(repository.currentBranch)
  const pullRequest = repository.pullRequests.at(-1) || null

  useEffect(() => {
    if (!toast) return undefined
    const timer = window.setTimeout(() => setToast(''), 2300)
    return () => window.clearTimeout(timer)
  }, [toast])

  const create = (event) => {
    event.preventDefault()
    const result = createPullRequest(repository, {
      baseBranch: repository.defaultBranch,
      compareBranch: repository.currentBranch,
      description: body,
      title,
    })
    if (result.error) {
      setError(result.error)
      return
    }
    setError('')
    setShowForm(false)
    setActiveTab('pulls')
    onRepositoryChange(result.repository)
  }

  return <>
    <div className="github-toolbar">
      <label className="github-repository-picker"><span>Repository</span><select aria-label="Repository" value={repository.rootPath} onChange={() => {}}><option value={repository.rootPath}>{repository.repositoryName}</option></select></label>
    </div>
    <div className="github-content">
      <div className="github-repository-page">
        <header className="github-repository-header">
          <h2 className="github-repository-name">careergrid-sim / {repository.repositoryName}</h2>
          <p className="github-repository-path">{repository.rootPath}</p>
        </header>
        <nav className="github-tabs" aria-label="Repository navigation">
          <button className={`github-tab${activeTab === 'code' ? ' is-active' : ''}`} type="button" onClick={() => { setActiveTab('code'); setShowForm(false) }}>Code</button>
          <button className={`github-tab${activeTab === 'pulls' ? ' is-active' : ''}`} type="button" onClick={() => { setActiveTab('pulls'); setShowForm(false) }}>Pull Requests</button>
        </nav>

        {showForm ? (
          <form className="github-pr-form" onSubmit={create}>
            <div className="github-actions"><h3>Create pull request</h3><button className="github-secondary-button" type="button" onClick={() => setShowForm(false)}>Cancel</button></div>
            <div className="github-form-grid">
              <label className="github-form-field">Base branch<select className="github-form-control" value={repository.defaultBranch} onChange={() => {}}><option>{repository.defaultBranch}</option></select></label>
              <label className="github-form-field">Compare branch<select className="github-form-control" value={repository.currentBranch} onChange={() => {}}><option>{repository.currentBranch}</option></select></label>
              <label className="github-form-field is-full">Title<input className="github-form-control" required maxLength="140" value={title} onChange={(event) => setTitle(event.target.value)} /></label>
              <label className="github-form-field is-full">Description<textarea className="github-form-control" rows="7" placeholder="Describe the change and any relevant context." value={body} onChange={(event) => setBody(event.target.value)} /></label>
            </div>
            <p className="github-form-error">{error}</p>
            <div className="github-form-actions"><button className="github-primary-button" type="submit">Create Pull Request</button></div>
          </form>
        ) : activeTab === 'pulls' ? (
          pullRequest
            ? <PullRequestDetail pullRequest={pullRequest} repository={repository} onCopySuccess={() => setToast('Pull request link copied')} />
            : <PullRequestsView pullRequests={repository.pullRequests} onCreate={() => setShowForm(true)} />
        ) : (
          <CodeView current={current} pushed={pushed} repository={repository} taskId={taskId} onCreate={() => setShowForm(true)} />
        )}
      </div>
    </div>
    {toast && <div className="github-toast" role="status">{toast}</div>}
  </>
}

function CodeView({ current, pushed, repository, taskId, onCreate }) {
  const onMain = repository.currentBranch === repository.defaultBranch
  const prHint = onMain
    ? 'Pull requests compare a feature branch with main. Create one with git switch -c <name>, or submit directly on main.'
    : !pushed ? 'Push this branch (git push) to open a pull request.' : ''
  return <>
    <div className="github-actions">
      <label>Branch <select className="github-branch-select" value={repository.currentBranch} onChange={() => {}}><option>{repository.currentBranch}</option></select></label>
      <button className="github-primary-button" type="button" disabled={!pushed || onMain} onClick={onCreate}>Create Pull Request</button>
    </div>
    {prHint && <p className="github-muted">{prHint}</p>}
    <SyncStatus repository={repository} />
    <div className="github-layout">
      <div>
        {current.commits.at(-1) && <section className="github-section"><div className="github-section-body"><div className="github-commit-title">{current.commits.at(-1).message}</div><div className="github-commit-meta">{current.commits.at(-1).author} committed · {current.commits.at(-1).id}</div></div></section>}
        <section className="github-section github-file-preview">
          <h3 className="github-section-title">Repository files</h3>
          <div className="github-section-body">
            {Object.values(current.workingTree).map((file) => <div className="github-file-row" key={file.path}><span className="github-file-icon">FILE</span><button className="github-file-button" type="button">{file.path}</button><span className="github-file-meta">Project file</span></div>)}
          </div>
        </section>
      </div>
      <div>
        <aside className="github-section"><h3 className="github-section-title">Branches</h3><div className="github-section-body github-branch-list">{Object.keys(repository.branches).map((branch) => <div className={`github-branch-row${branch === repository.currentBranch ? ' is-current' : ''}`} key={branch}><span className="github-branch-name">{branch === repository.currentBranch ? '● ' : ''}{branch}</span><span className={`github-status-badge ${repository.remote.pushedBranches.includes(branch) ? 'is-pushed' : 'is-local'}`}>{repository.remote.pushedBranches.includes(branch) ? 'Pushed' : 'Local only'}</span></div>)}</div></aside>
        <DeliveryGuide repository={repository} taskId={taskId} />
        <aside className="github-section" style={{ marginTop: 16 }}><h3 className="github-section-title">Commits</h3><div className="github-section-body">{current.commits.slice().reverse().map((item) => <CommitRow commit={item} key={item.id} />)}</div></aside>
      </div>
    </div>
  </>
}

function PullRequestsView({ pullRequests, onCreate }) {
  return <>
    <div className="github-actions"><span className="github-muted">{pullRequests.length} pull request{pullRequests.length === 1 ? '' : 's'}</span><button className="github-primary-button" type="button" onClick={onCreate}>Create Pull Request</button></div>
    <section className="github-section" style={{ marginTop: 16 }}><div className="github-section-body">{pullRequests.length ? pullRequests.map((pullRequest) => <div className="github-pr-row" key={pullRequest.id}><div><span className="github-link-button github-pr-title">#{pullRequest.id} {pullRequest.title}</span><div className="github-pr-meta">{pullRequest.compareBranch} → {pullRequest.baseBranch} · opened by {pullRequest.author}</div></div><span className="github-status-badge is-open">Open</span></div>) : <p className="github-muted">No pull requests yet. Push a branch, then open a pull request here.</p>}</div></section>
  </>
}

function PullRequestDetail({ onCopySuccess, pullRequest, repository }) {
  const commits = repository.branches[pullRequest.compareBranch]?.commits || []
  const copyLink = async () => {
    const result = await copyPullRequestLink(pullRequest.url)
    if (result.copied) onCopySuccess()
  }
  return <section className="github-pr-detail" style={{ marginTop: 16 }}>
    <div className="github-actions"><div><h3>#{pullRequest.id} {pullRequest.title}</h3><div className="github-detail-meta"><span className="github-status-badge is-open">Open</span><span>{pullRequest.compareBranch} → {pullRequest.baseBranch}</span><span>opened by {pullRequest.author}</span></div></div></div>
    <p className="github-pr-description">{pullRequest.description || 'No description provided.'}</p>
    <a className="github-pr-url" href={pullRequest.url} target="_blank" rel="noreferrer">{pullRequest.url}</a>
    <div className="github-form-actions"><button className="github-secondary-button" type="button" onClick={copyLink}>Copy PR Link</button></div>
    <section className="github-section" style={{ marginTop: 16 }}><h4 className="github-section-title">Compare branch commits</h4><div className="github-section-body">{commits.map((commit) => <CommitRow commit={commit} key={commit.id} />)}</div></section>
  </section>
}

function CommitRow({ commit }) {
  return <div className="github-commit-row"><div><div className="github-commit-title">{commit.message}</div><div className="github-commit-meta">{commit.author} committed</div></div><span className="github-commit-id">{commit.id}</span></div>
}

export default GitHubApp
