import { useState } from 'react'

import {
  changedFiles,
  commit,
  createBranch,
  diff,
  push,
  stage,
  switchBranch,
} from '../state/repositoryModel.js'

function statusOutput(repository) {
  const branch = repository.branches[repository.currentBranch]
  const changed = changedFiles(repository).filter((path) => !branch.stagedPaths.includes(path))
  const lines = [`On branch ${repository.currentBranch}`]
  if (branch.stagedPaths.length) lines.push('Changes to be committed:', ...branch.stagedPaths.map((path) => `  modified: ${path}`))
  if (changed.length) lines.push('Changes not staged for commit:', ...changed.map((path) => `  modified: ${path}`))
  if (!branch.stagedPaths.length && !changed.length) lines.push('nothing to commit, working tree clean')
  return lines.join('\n')
}

function diffOutput(repository) {
  const changes = diff(repository)
  if (!changes.length) return ''
  return changes.map((change) => `diff -- ${change.path}\n--- before\n${change.before}\n+++ after\n${change.after}`).join('\n\n')
}

function TerminalApp({ files, repository, onRepositoryChange }) {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])

  const apply = (result, successMessage) => {
    if (!result.error) onRepositoryChange(result.repository)
    return result.error || successMessage(result)
  }

  const execute = (command) => {
    const target = command.slice(4)
    if (command === 'pwd') return repository.rootPath
    if (command === 'ls') return files.map((file) => file.path.split('/').pop()).join('  ')
    if (command.startsWith('cd ')) return target === '..' || target === '/Projects' || target === repository.rootPath ? '' : `cd: ${target}: No such file or directory`
    if (command.startsWith('cat ')) return files.find((file) => file.path === target || file.path.endsWith(`/${target}`))?.content || `cat: ${target}: No such file`
    if (command === 'git status') return statusOutput(repository)
    if (command === 'git diff') return diffOutput(repository)
    if (command === 'git branch') return Object.keys(repository.branches).map((name) => `${name === repository.currentBranch ? '*' : ' '} ${name}`).join('\n')
    if (command.startsWith('git switch -c ') || command.startsWith('git checkout -b ')) {
      const name = command.split(' ').at(-1)
      return apply(createBranch(repository, name), () => `Switched to a new branch '${name}'`)
    }
    if (command.startsWith('git switch ') || command.startsWith('git checkout ')) {
      const name = command.split(' ').at(-1)
      return apply(switchBranch(repository, name), () => `Switched to branch '${name}'`)
    }
    if (command === 'git add .' || command === 'git add -A' || command === 'git add --all') {
      return apply(stage(repository, '.'), (result) => `${result.count} file(s) staged`)
    }
    if (command.startsWith('git add ')) {
      const path = command.slice(8).trim()
      return apply(stage(repository, [path]), (result) => result.count ? `${path} staged` : `pathspec '${path}' did not match changed files`)
    }
    if (command.startsWith('git commit -m ')) {
      const message = command.match(/^git commit -m\s+["'](.+)["']$/)?.[1] || ''
      return apply(commit(repository, message), (result) => `[${repository.currentBranch} ${result.commit.id}] ${result.commit.message}\n${result.filesChanged} file(s) changed`)
    }
    if (command === 'git push' || command.startsWith('git push ')) {
      return apply(push(repository), (result) => `Branch '${result.branch}' pushed to origin`)
    }
    if (command === 'git log' || command === 'git log --oneline') {
      return [...repository.branches[repository.currentBranch].commits].reverse().map((item) => `${item.id} ${item.message}`).join('\n')
    }
    if (command === 'help') return 'Available commands: pwd, ls, cd, cat, git status, git diff, git branch, git switch, git add, git commit, git push, git log, clear'
    if (command === 'clear') return '__CLEAR__'
    return `${command}: command not found`
  }

  const run = (event) => {
    event.preventDefault()
    const command = input.trim()
    if (!command) return
    const output = execute(command)
    setHistory((items) => output === '__CLEAR__' ? [] : [...items, { command, output }])
    setInput('')
  }

  return <>
    <div className="terminal-tab-bar">
      <div className="terminal-tab is-active"><span>&gt;_</span><span>bash</span></div>
      <div className="terminal-working-directory">{repository.rootPath}</div>
    </div>
    <div className="terminal-screen">
      <div className="terminal-welcome">CareerGrid Workspace Terminal{`\n\n`}Type <strong>help</strong> to see available commands.</div>
      <div className="terminal-history">
        {history.map((entry, index) => {
          const outputClass = /fatal|error|not found/i.test(entry.output)
            ? ' is-error'
            : /switched|pushed|staged|file\(s\) changed/i.test(entry.output)
              ? ' is-success'
              : ''
          return <div className="terminal-command-block" key={index}>
            <div className="terminal-command-line">
              <span className="terminal-command-prompt">careergrid:{repository.rootPath}$</span>
              <span className="terminal-command-text">{entry.command}</span>
            </div>
            <pre className={`terminal-output${outputClass}`}>{entry.output}</pre>
          </div>
        })}
      </div>
    </div>
    <form className="terminal-command-bar" onSubmit={run}>
      <span className="terminal-prompt">careergrid:{repository.rootPath}$</span>
      <input className="terminal-input" value={input} onChange={(event) => setInput(event.target.value)} autoFocus spellCheck="false" />
    </form>
  </>
}

export default TerminalApp
