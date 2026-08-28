import { useState } from 'react'

import { createPullRequest } from '../state/repositoryModel.js'

function GitHubApp({ repository, onRepositoryChange }) {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const current = repository.branches[repository.currentBranch]
  const pushed = repository.remote.pushedBranches.includes(repository.currentBranch)
  const pullRequest = repository.pullRequests.at(-1) || null

  const create = (event) => {
    event.preventDefault()
    const result = createPullRequest(repository, {
      baseBranch: repository.defaultBranch,
      compareBranch: repository.currentBranch,
      title,
      description: body,
    })
    if (result.error) { setError(result.error); return }
    setError('')
    onRepositoryChange(result.repository)
  }

  return <div className="github-layout"><header className="github-repository-header"><h2>CareerGrid workspace repository</h2><span>{repository.currentBranch}</span></header><section className="github-content"><h3>Branches</h3><p>{pushed ? `${repository.currentBranch} pushed` : 'Push a branch from Terminal to create a pull request.'}</p><h3>Commits</h3><ul>{current.commits.map((item) => <li key={item.id}>{item.message}</li>)}</ul>{pushed && !pullRequest && <form className="github-pr-form" onSubmit={create}><input placeholder="Pull request title" value={title} onChange={(event) => setTitle(event.target.value)} /><textarea placeholder="Describe your changes" value={body} onChange={(event) => setBody(event.target.value)} /><p>{error}</p><button type="submit">Create pull request</button></form>}{pullRequest && <article className="github-pull-request"><h3>#{pullRequest.id} {pullRequest.title}</h3><p>{pullRequest.description}</p><a href={pullRequest.url} target="_blank" rel="noreferrer">{pullRequest.url}</a><strong>Pull request created</strong></article>}</section></div>
}

export default GitHubApp
