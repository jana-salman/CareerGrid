import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { evaluateWorkplaceSimulation, requestAdvisorGuidance } from '../../services/simulationApi.js'
import { buildEvaluationEvidence, markEvaluationFailed, markEvaluationPending, recordEvaluation } from '../state/evaluationEvidence.js'
import { createFinalReportMessage, ensureFinalReportMessage } from '../state/reportMail.js'
import { buildScenarioAttachments } from '../state/repositoryModel.js'
import { processCompletionReply, SUBMISSION_ACKNOWLEDGEMENT } from '../state/submissionWorkflow.js'

function createMessages(scenario) {
  const task = scenario.task || {}
  const advisor = scenario.advisor || {}
  const scenarioAttachments = buildScenarioAttachments(scenario)
  const main = task.id ? [{
    attachments: scenarioAttachments.length ? scenarioAttachments : task.attachments || scenario.attachments || [],
    body: task.body || task.summary || '',
    deadline: task.deadline || '',
    id: task.id,
    priority: task.priority || 'high',
    role: advisor.title || 'Advisor',
    sender: advisor.name || 'CareerGrid Advisor',
    subject: task.subject || 'Workplace task',
    task: true,
    unread: true,
  }] : []
  return [...main, ...(scenario.background_emails || []).map((email, index) => ({
    attachments: [],
    body: email.body,
    id: email.id || `background-${index}`,
    priority: email.priority || 'normal',
    role: email.sender_title,
    sender: email.sender_name,
    subject: email.subject,
    unread: true,
  }))]
}

function MailApp({ attempt, downloadedAttachments, repository, userIdentity, onDownload, onRepositoryChange, onUnreadChange }) {
  const navigate = useNavigate()
  const scenario = attempt.public_scenario || {}
  const [messages, setMessages] = useState(() => createMessages(scenario))
  const [folder, setFolder] = useState('inbox')
  const [selectedId, setSelectedId] = useState(null)
  const [query, setQuery] = useState('')
  const [draft, setDraft] = useState('')
  const [replying, setReplying] = useState(false)
  const [sending, setSending] = useState(false)
  const [, setEvaluationStatus] = useState('')
  const submissionLock = useRef(false)
  const [error, setError] = useState('')
  const completionEnabled = attempt.position_id !== 'frontend-developer'
  const userName = userIdentity.name?.trim() || userIdentity.email?.split('@')[0] || 'CareerGrid User'
  const userInitial = userName.charAt(0).toUpperCase()
  const positionTitle = attempt.position_id
    ?.replaceAll('-', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase()) || 'CareerGrid User'
  const visible = useMemo(() => messages.filter((message) => (
    (folder === 'sent' ? message.sent : !message.sent)
    && `${message.sender} ${message.subject}`.toLowerCase().includes(query.toLowerCase())
  )), [folder, messages, query])
  const selected = messages.find((message) => message.id === selectedId)

  useEffect(() => {
    onUnreadChange(messages.filter((message) => !message.sent && message.unread).length)
  }, [messages, onUnreadChange])

  useEffect(() => {
    const completedTask = messages.find((message) => message.task && repository.evaluations[message.id]?.status === 'completed')
    if (!completedTask) return
    const evaluation = repository.evaluations[completedTask.id].data || {}
    setMessages((items) => items.map((message) => (
      message.id === completedTask.id
        ? ensureFinalReportMessage(message, { attemptId: attempt.attempt_id, evaluation })
        : message
    )))
    setFolder('inbox')
    setSelectedId((current) => current || completedTask.id)
  }, [attempt.attempt_id, repository.evaluations])

  const open = (id) => {
    setSelectedId(id)
    setReplying(false)
    setDraft('')
    setError('')
    setMessages((items) => items.map((item) => (
      item.id === id ? { ...item, unread: false } : item
    )))
  }

  const runEvaluation = async (sourceRepository, submission, taskMessage) => {
    const pending = markEvaluationPending(sourceRepository, taskMessage.id)
    if (pending.error) return { advisorReply: pending.error, failed: true, repository: sourceRepository }
    let evaluationRepository = pending.repository
    onRepositoryChange(evaluationRepository)
    setEvaluationStatus('evaluating')
    setError('Evaluating your submitted workplace evidence...')
    try {
      const evidence = buildEvaluationEvidence({ attempt, repository: evaluationRepository, submission, taskMessage })
      const evaluation = await evaluateWorkplaceSimulation({ attemptId: attempt.attempt_id, evidence })
      evaluationRepository = recordEvaluation(evaluationRepository, taskMessage.id, evaluation).repository
      onRepositoryChange(evaluationRepository)
      setEvaluationStatus('success')
      setError('')
      return {
        advisorReply: 'Your workplace review is ready.',
        failed: false,
        reportMessage: createFinalReportMessage({ attemptId: attempt.attempt_id, evaluation, taskMessage }),
        repository: evaluationRepository,
      }
    } catch (requestError) {
      evaluationRepository = markEvaluationFailed(evaluationRepository, taskMessage.id, requestError.message).repository
      onRepositoryChange(evaluationRepository)
      setEvaluationStatus('failed')
      setError(requestError.message)
      return {
        advisorReply: 'Your submission was recorded, but the review could not be completed. Reply retry to try again.',
        failed: true,
        repository: evaluationRepository,
      }
    }
  }

  const send = async () => {
    if (!draft.trim() || !selected || sending || submissionLock.current) return
    submissionLock.current = true
    setSending(true)
    setError('')
    const body = draft.trim()
    const userMessage = { body, id: `sent-${Date.now()}`, role: positionTitle, sender: userName, sent: true }
    let advisorReply = ''
    let reportMessage = null
    let nextRepository = repository
    let confirmationRendered = false
    let completionFailed = false
    try {
      if (completionEnabled && selected.task) {
        const completion = await processCompletionReply({
          body,
          evaluate: async (sourceRepository, submission) => {
            confirmationRendered = true
            setMessages((items) => items.map((item) => {
              if (item.id !== selected.id) return item
              if (item.replies?.some((reply) => reply.id === userMessage.id)) return item
              return {
                ...item,
                replies: [
                  ...(item.replies || []),
                  userMessage,
                  {
                    body: SUBMISSION_ACKNOWLEDGEMENT,
                    id: `advisor-confirm-${userMessage.id}`,
                    role: selected.role,
                    sender: selected.sender,
                  },
                ],
              }
            }))
            setDraft('')
            setReplying(false)
            return runEvaluation(
              sourceRepository,
              submission,
              { ...selected, replies: [...(selected.replies || []), userMessage] },
            )
          },
          messageId: userMessage.id,
          repository,
          threadId: selected.id,
        })
        nextRepository = completion.repository
        advisorReply = completion.advisorReply
        reportMessage = completion.reportMessage || null
        completionFailed = Boolean(completion.failed)
      }
      if (!advisorReply) {
        const result = await requestAdvisorGuidance({
          advisorContext: { message: body, task: { subject: selected.subject } },
          attemptId: attempt.attempt_id,
        })
        advisorReply = result.advisor_reply || result.reply || 'Thanks - I have received your update.'
      }
      if (nextRepository !== repository) onRepositoryChange(nextRepository)
      setMessages((items) => items.map((item) => {
        if (item.id !== selected.id) return item
        const replies = [...(item.replies || [])]
        if (!confirmationRendered) {
          replies.push(
            userMessage,
            { body: advisorReply, id: `advisor-${Date.now()}`, role: selected.role, sender: selected.sender },
          )
        } else if (completionFailed && advisorReply !== SUBMISSION_ACKNOWLEDGEMENT) {
          replies.push({
            body: advisorReply,
            id: `advisor-evaluation-${userMessage.id}`,
            role: selected.role,
            sender: selected.sender,
          })
        }
        if (reportMessage && !replies.some((reply) => reply.type === 'evaluation-review')) {
          replies.push(reportMessage)
        }
        return { ...item, replies }
      }))
      setDraft('')
      setReplying(false)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      submissionLock.current = false
      setSending(false)
    }
  }

  return (
    <div className="mail-layout">
      <aside className="mail-sidebar">
        <div className="mail-sidebar-title">Mail</div>
        <nav className="mail-folders">
          <button className={`mail-folder${folder === 'inbox' ? ' is-active' : ''}`} type="button" onClick={() => setFolder('inbox')}>
            <span aria-hidden="true">📥</span><span>Inbox</span>
            <span className="folder-count">{messages.filter((item) => !item.sent && item.unread).length}</span>
          </button>
          <button className={`mail-folder${folder === 'sent' ? ' is-active' : ''}`} type="button" onClick={() => setFolder('sent')}>
            <span aria-hidden="true">📤</span><span>Sent</span>
            <span className="folder-count">{messages.filter((item) => item.sent).length}</span>
          </button>
        </nav>
        <div className="mail-sidebar-footer">
          <span className="mail-account-avatar">{userInitial}</span>
          <div><strong>{userName}</strong><small>{positionTitle}</small></div>
        </div>
      </aside>

      <section className="mail-list-column">
        <div className="mail-list-toolbar">
          <div><h2>{folder === 'inbox' ? 'Inbox' : 'Sent'}</h2><span>Your workplace messages</span></div>
          <input id="mail-search" type="search" placeholder="Search mail" value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <div className="mail-message-list">
          {visible.map((message) => (
            <button
              className={`mail-list-item${selectedId === message.id ? ' is-selected' : ''}${message.unread ? ' is-unread' : ''}`}
              type="button"
              key={message.id}
              onClick={() => open(message.id)}
            >
              <span className="mail-list-topline"><strong className="mail-list-sender">{message.sender}</strong><span className="mail-list-time">Now</span></span>
              <div className="mail-list-subject">{message.subject}</div>
              <div className="mail-list-preview">{message.body?.slice(0, 120)}</div>
              {message.deadline && <div className="mail-list-deadline">Due {message.deadline}</div>}
            </button>
          ))}
        </div>
      </section>

      <section className="mail-reading-pane">
        {!selected ? (
          <div className="mail-empty-state"><div className="mail-empty-icon">✉</div><h2>Select a message</h2><p>Open an email from your inbox to read it here.</p></div>
        ) : (
          <div className="mail-message-view">
            <header className="mail-message-header">
              <div>
                <div className="mail-message-label-row">
                  <span className={`mail-priority priority-${selected.priority || 'normal'}`}>{selected.priority === 'high' ? 'High priority' : 'Normal priority'}</span>
                  {selected.deadline && <span className="mail-deadline">Due {selected.deadline}</span>}
                  {selected.task && <span className="mail-task-status">Workplace task</span>}
                </div>
                <h1>{selected.subject}</h1>
              </div>
            </header>

            <div className="mail-thread">
              <ThreadMessage message={selected} onOpenReport={(path) => navigate(path)} />
              {selected.replies?.map((reply) => <ThreadMessage message={reply} onOpenReport={(path) => navigate(path)} key={reply.id} />)}
            </div>

            {selected.attachments?.length > 0 && (
              <section className="mail-attachments">
                <h3>Attachments</h3>
                <div className="mail-attachment-list">
                  {selected.attachments.map((attachment) => {
                    const downloaded = downloadedAttachments.some((item) => item.name === attachment.name)
                    return (
                      <div className="mail-attachment-card" key={attachment.id || attachment.name}>
                        <span className="mail-attachment-icon">FILE</span>
                        <span className="mail-attachment-info"><strong>{attachment.name}</strong><span>{attachment.size || 'Attachment'}</span></span>
                        <button className={`mail-download-button${downloaded ? ' is-downloaded' : ''}`} type="button" onClick={() => onDownload(attachment)}>
                          {downloaded ? 'Saved' : 'Download'}
                        </button>
                      </div>
                    )
                  })}
                </div>
              </section>
            )}

            {!replying && <div className="mail-message-actions"><button className="mail-primary-action" type="button" onClick={() => setReplying(true)}>↩ Reply</button></div>}
            {replying && (
              <section className="mail-composer">
                <div className="mail-composer-header"><span>To:</span><strong>{selected.sender}</strong></div>
                <textarea id="mail-reply-text" rows="8" placeholder="Write your reply..." value={draft} onChange={(event) => setDraft(event.target.value)} />
                <div className="mail-composer-footer">
                  <span className="mail-draft-status">{error || 'Your reply will stay in this email thread.'}</span>
                  <div className="mail-compose-actions">
                    <button className="mail-cancel-button" type="button" onClick={() => { setReplying(false); setDraft(''); setError('') }}>Cancel</button>
                    <button className="mail-send-button" type="button" disabled={sending || !draft.trim()} onClick={send}>{sending ? 'Sending...' : 'Send'}</button>
                  </div>
                </div>
              </section>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

function ThreadMessage({ message, onOpenReport }) {
  const isUser = message.sent
  return (
    <article className={`mail-thread-message${isUser ? ' is-user' : ''}`}>
      <header className="mail-thread-message-header">
        <div className="mail-sender-block">
          <span className="mail-sender-avatar">{String(message.sender || 'U').charAt(0).toUpperCase()}</span>
          <div><strong>{message.sender}</strong><small>{message.role || ''}</small></div>
        </div>
        <span className="mail-thread-time">Now</span>
      </header>
      <div className="mail-thread-body">{message.body}</div>
      {message.attachments?.filter((attachment) => attachment.type === 'evaluation-report').map((attachment) => (
        <button className="mail-download-button" type="button" key={attachment.id} onClick={() => onOpenReport(attachment.reportPath)}>{attachment.name}</button>
      ))}
    </article>
  )
}

export default MailApp
