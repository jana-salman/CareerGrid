import { useRef, useState } from 'react'

import {
  changedFiles,
  commit,
  createBranch,
  diff,
  push,
  stage,
  switchBranch,
} from '../state/repositoryModel.js'

const commandCompletions = [
  'cat', 'cd', 'clear', 'git add', 'git branch', 'git checkout -b',
  'git commit -m', 'git diff', 'git log', 'git log --oneline', 'git push',
  'git status', 'git switch', 'git switch -c', 'help', 'ls', 'pwd',
]

function normalizePath(path) {
  const resolved = []
  String(path || '/').replaceAll('\\', '/').split('/').forEach((part) => {
    if (!part || part === '.') return
    if (part === '..') resolved.pop()
    else resolved.push(part)
  })
  return `/${resolved.join('/')}`
}

function resolvePath(cwd, value = '.') {
  const raw = String(value || '.').trim()
  if (raw === '~') return '/Projects'
  return normalizePath(raw.startsWith('/') ? raw : `${cwd}/${raw}`)
}

function repositoryParent(repository) {
  const parts = repository.rootPath.split('/').filter(Boolean)
  return `/${parts.slice(0, -1).join('/')}` || '/'
}

function absoluteFilePath(repository, file) {
  return normalizePath(`${repository.rootPath}/${file.path}`)
}

function repositoryDirectories(repository, files) {
  const directories = new Set([repositoryParent(repository)])
  if (!repository.workspace?.projectExtracted) return directories
  directories.add(repository.rootPath)
  files.forEach((file) => {
    const parts = absoluteFilePath(repository, file).split('/').filter(Boolean)
    for (let index = 1; index < parts.length; index += 1) {
      directories.add(`/${parts.slice(0, index).join('/')}`)
    }
  })
  return directories
}

function fileAtPath(repository, files, path) {
  const target = normalizePath(path)
  return files.find((file) => absoluteFilePath(repository, file) === target)
}

function listOutput(repository, files, target) {
  const projectParent = repositoryParent(repository)
  if (target === projectParent) {
    return repository.workspace?.projectExtracted ? `${repository.repositoryName}/` : ''
  }

  const file = fileAtPath(repository, files, target)
  if (file) return file.path.split('/').pop()
  if (!repositoryDirectories(repository, files).has(target)) return null

  const prefix = target === '/' ? '/' : `${target}/`
  const entries = new Map()
  files.forEach((item) => {
    const absolute = absoluteFilePath(repository, item)
    if (!absolute.startsWith(prefix)) return
    const remaining = absolute.slice(prefix.length)
    if (!remaining) return
    const [name, ...rest] = remaining.split('/')
    entries.set(name, rest.length > 0)
  })
  return [...entries]
    .sort(([leftName, leftFolder], [rightName, rightFolder]) => {
      if (leftFolder !== rightFolder) return leftFolder ? -1 : 1
      return leftName.localeCompare(rightName)
    })
    .map(([name, folder]) => folder ? `${name}/` : name)
    .join('    ')
}

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

function logOutput(repository, oneline) {
  const commits = [...repository.branches[repository.currentBranch].commits].reverse()
  if (oneline) return commits.map((item) => `${item.id} ${item.message}`).join('\n')
  return commits.map((item) => `commit ${item.id}\nAuthor: ${item.author}\nDate:   ${new Date(item.createdAt).toLocaleString()}\n\n    ${item.message}`).join('\n\n')
}

function commonPrefix(values) {
  if (!values.length) return ''
  return values.reduce((prefix, value) => {
    let index = 0
    while (index < prefix.length && prefix[index] === value[index]) index += 1
    return prefix.slice(0, index)
  })
}

function autocomplete(value, cwd, repository, files) {
  const pathCommand = value.match(/^(cd|cat|git add)\s+([^\s]*)$/)
  if (pathCommand) {
    const [, command, partial] = pathCommand
    const candidates = []
    if (cwd === repositoryParent(repository) && repository.workspace?.projectExtracted) {
      candidates.push(repository.repositoryName)
    } else if (cwd === repository.rootPath || cwd.startsWith(`${repository.rootPath}/`)) {
      const prefix = cwd === repository.rootPath ? '' : `${cwd.slice(repository.rootPath.length + 1)}/`
      files.forEach((file) => {
        if (file.path.startsWith(prefix)) candidates.push(file.path.slice(prefix.length))
      })
    }
    const matches = [...new Set(candidates)].filter((candidate) => candidate.startsWith(partial))
    if (!matches.length) return value
    return `${command} ${matches.length === 1 ? matches[0] : commonPrefix(matches)}`
  }

  const matches = commandCompletions.filter((command) => command.startsWith(value))
  if (!matches.length) return value
  return matches.length === 1 ? `${matches[0]} ` : commonPrefix(matches)
}

function TerminalApp({ files, repository, onRepositoryChange }) {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const [commandHistory, setCommandHistory] = useState([])
  const [historyIndex, setHistoryIndex] = useState(null)
  const [cwd, setCwd] = useState(() => repositoryParent(repository))
  const inputRef = useRef(null)

  const apply = (result, successMessage) => {
    if (!result.error) onRepositoryChange(result.repository)
    return result.error || successMessage(result)
  }

  const isInsideRepository = cwd === repository.rootPath || cwd.startsWith(`${repository.rootPath}/`)

  const execute = (command) => {
    if (command === 'pwd') return cwd
    if (command === 'ls' || command.startsWith('ls ')) {
      const rawTarget = command === 'ls' ? '.' : command.slice(3).trim()
      const output = listOutput(repository, files, resolvePath(cwd, rawTarget))
      return output === null ? `ls: cannot access '${rawTarget}': No such file or directory` : output
    }
    if (command === 'cd' || command.startsWith('cd ')) {
      const rawTarget = command === 'cd' ? '/Projects' : command.slice(3).trim()
      const target = resolvePath(cwd, rawTarget)
      if (!repositoryDirectories(repository, files).has(target)) return `cd: ${rawTarget}: No such file or directory`
      setCwd(target)
      return ''
    }
    if (command.startsWith('cat ')) {
      const rawTarget = command.slice(4).trim()
      const file = fileAtPath(repository, files, resolvePath(cwd, rawTarget))
      return file?.content ?? `cat: ${rawTarget}: No such file`
    }
    if (command.startsWith('git ') && !isInsideRepository) return 'fatal: not a git repository (or any of the parent directories): .git'
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
      const rawPath = command.slice(8).trim()
      const absolutePath = resolvePath(cwd, rawPath)
      const path = absolutePath.startsWith(`${repository.rootPath}/`) ? absolutePath.slice(repository.rootPath.length + 1) : rawPath
      return apply(stage(repository, [path]), (result) => result.count ? `${path} staged` : `pathspec '${rawPath}' did not match changed files`)
    }
    if (command.startsWith('git commit -m ')) {
      const message = command.match(/^git commit -m\s+["'](.+)["']$/)?.[1] || ''
      return apply(commit(repository, message), (result) => `[${repository.currentBranch} ${result.commit.id}] ${result.commit.message}\n${result.filesChanged} file(s) changed`)
    }
    if (command === 'git push' || command.startsWith('git push ')) {
      return apply(push(repository), (result) => `Branch '${result.branch}' pushed to origin`)
    }
    if (command === 'git log') return logOutput(repository, false)
    if (command === 'git log --oneline') return logOutput(repository, true)
    if (command === 'help') return `Available commands:

Navigation
  pwd
  ls [path]
  cd <path>
  cat <file>
  clear

Git
  git status
  git branch
  git switch -c <branch>
  git switch <branch>
  git checkout -b <branch>
  git add <file>
  git add .
  git commit -m "message"
  git log
  git log --oneline
  git push

Terminal
  help`
    if (command === 'clear') return '__CLEAR__'
    return `${command}: command not found`
  }

  const runCommand = () => {
    const command = input.trim()
    if (!command) return
    const output = execute(command)
    setHistory((items) => output === '__CLEAR__' ? [] : [...items, { command, cwd, output }])
    if (output !== '__CLEAR__') setCommandHistory((items) => [...items, command])
    setHistoryIndex(null)
    setInput('')
  }

  const run = (event) => {
    event.preventDefault()
    runCommand()
  }

  const moveCursor = (position) => {
    window.requestAnimationFrame(() => inputRef.current?.setSelectionRange(position, position))
  }

  const handleKeyDown = (event) => {
    const key = event.key.toLowerCase()
    if (event.ctrlKey && event.shiftKey && (key === 'c' || key === 'v')) return
    if (event.ctrlKey && key === 'l') {
      event.preventDefault()
      setHistory([])
      return
    }
    if (event.ctrlKey && key === 'c') {
      event.preventDefault()
      if (input) setHistory((items) => [...items, { command: input, cwd, output: '^C' }])
      setInput('')
      setHistoryIndex(null)
      return
    }
    if (event.ctrlKey && key === 'a') {
      event.preventDefault()
      moveCursor(0)
      return
    }
    if (event.ctrlKey && key === 'e') {
      event.preventDefault()
      moveCursor(input.length)
      return
    }
    if (event.ctrlKey && key === 'u') {
      event.preventDefault()
      setInput('')
      setHistoryIndex(null)
      return
    }
    if (event.ctrlKey && key === 'r') {
      event.preventDefault()
      const query = input.toLowerCase()
      const match = [...commandHistory].reverse().find((command) => command.toLowerCase().includes(query))
      if (match) {
        setInput(match)
        moveCursor(match.length)
      }
      return
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      if (!commandHistory.length) return
      const nextIndex = historyIndex === null ? commandHistory.length - 1 : Math.max(0, historyIndex - 1)
      setHistoryIndex(nextIndex)
      setInput(commandHistory[nextIndex])
      moveCursor(commandHistory[nextIndex].length)
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (historyIndex === null) return
      const nextIndex = historyIndex + 1
      if (nextIndex >= commandHistory.length) {
        setHistoryIndex(null)
        setInput('')
      } else {
        setHistoryIndex(nextIndex)
        setInput(commandHistory[nextIndex])
        moveCursor(commandHistory[nextIndex].length)
      }
      return
    }
    if (event.key === 'Tab') {
      event.preventDefault()
      const completed = autocomplete(input, cwd, repository, files)
      setInput(completed)
      moveCursor(completed.length)
    }
  }

  return <>
    <div className="terminal-tab-bar">
      <div className="terminal-tab is-active"><span>&gt;_</span><span>bash</span></div>
      <div className="terminal-working-directory">{cwd}</div>
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
              <span className="terminal-command-prompt">careergrid:{entry.cwd}$</span>
              <span className="terminal-command-text">{entry.command}</span>
            </div>
            <pre className={`terminal-output${outputClass}`}>{entry.output}</pre>
          </div>
        })}
      </div>
    </div>
    <form className="terminal-command-bar" onSubmit={run}>
      <span className="terminal-prompt">careergrid:{cwd}$</span>
      <input ref={inputRef} className="terminal-input" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} autoFocus spellCheck="false" />
    </form>
  </>
}

export default TerminalApp
