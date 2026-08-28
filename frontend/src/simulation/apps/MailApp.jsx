import { useMemo, useState } from 'react'
import { requestAdvisorGuidance } from '../../services/simulationApi.js'
import {
  assessCompletionEmail,
  cancelSubmissionCandidate,
  confirmSubmission,
  createSubmissionCandidate,
  isAffirmativeSubmissionConfirmation,
  isSubmissionCancellation,
} from '../state/submissionWorkflow.js'

function createMessages(scenario) {
  const task = scenario.task || {}
  const advisor = scenario.advisor || {}
  const main = task.id ? [{ id: task.id, sender: advisor.name || 'CareerGrid Advisor', role: advisor.title || 'Advisor', subject: task.subject || 'Workplace task', body: task.body || task.summary || '', unread: true, task: true, attachments: task.attachments || scenario.attachments || [] }] : []
  return [...main, ...(scenario.background_emails || []).map((email, index) => ({ id: email.id || `background-${index}`, sender: email.sender_name, role: email.sender_title, subject: email.subject, body: email.body, unread: true, attachments: [] }))]
}

function completionGuidance(errors) {
  if (errors.includes('missing_pull_request')) return 'Please include the simulated pull request link in your completion update.'
  if (errors.includes('invalid_pull_request')) return "I couldn't find that pull request in the current project. Please double-check the link and send it again."
  if (errors.includes('branch_not_pushed')) return 'Push the pull request branch before submitting it for review.'
  if (errors.includes('no_compare_commits')) return 'Commit your changes on the feature branch before submitting the pull request.'
  if (errors.includes('branch_mismatch')) return 'The branch named in your update does not match the pull request branch.'
  if (errors.includes('insufficient_summary')) return 'Please add a meaningful summary of what you investigated or changed.'
  if (errors.includes('missing_verification')) return 'Please state how you tested, checked, or verified the work.'
  return 'Please complete the simulated Git and pull request workflow before submitting.'
}

function MailApp({ attempt, downloadedAttachments, repository, onDownload, onRepositoryChange, onSubmissionConfirmed = () => {} }) {
  const scenario = attempt.public_scenario || {}
  const [messages, setMessages] = useState(() => createMessages(scenario))
  const [folder, setFolder] = useState('inbox')
  const [selectedId, setSelectedId] = useState(null)
  const [query, setQuery] = useState('')
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const completionEnabled = attempt.position_id !== 'frontend-developer'
  const visible = useMemo(() => messages.filter((message) => (folder === 'sent' ? message.sent : !message.sent) && `${message.sender} ${message.subject}`.toLowerCase().includes(query.toLowerCase())), [folder, messages, query])
  const selected = messages.find((message) => message.id === selectedId)
  const open = (id) => { setSelectedId(id); setMessages((items) => items.map((item) => item.id === id ? { ...item, unread: false } : item)) }
  const send = async () => {
    if (!draft.trim() || !selected || sending) return
    setSending(true); setError('')
    const body = draft.trim()
    const userMessage = { id: `sent-${Date.now()}`, sender: 'You', role: 'You', body, sent: true }
    let advisorReply = ''
    let nextRepository = repository
    try {
      if (completionEnabled && selected.task) {
        const candidate = repository.submissionCandidates[selected.id]
        const existing = repository.submissions[selected.id]
        if (existing) advisorReply = 'This task has already been submitted for final review.'
        else if (candidate && isSubmissionCancellation(body)) {
          const result = cancelSubmissionCandidate(repository, selected.id); nextRepository = result.repository
          advisorReply = 'No problem. The pending submission was cancelled so you can correct it.'
        } else if (candidate && isAffirmativeSubmissionConfirmation(body)) {
          const result = confirmSubmission(repository, selected.id, body, userMessage.id)
          if (result.error) advisorReply = result.error
          else { nextRepository = result.repository; advisorReply = 'Thanks, I will treat this pull request as your final submission and begin the review.'; onSubmissionConfirmed(result.submission, result.repository, selected) }
        } else if (candidate) advisorReply = 'I have the pull request queued for final review. Reply yes to submit it, or cancel to make a correction.'
        else {
          const assessment = assessCompletionEmail(repository, body)
          if (assessment.validCandidate) {
            const result = createSubmissionCandidate(repository, selected.id, body, assessment); nextRepository = result.repository
            advisorReply = 'Just to confirm, is this the pull request you want me to review as your final submission?'
          } else if (assessment.looksLikeSubmission) advisorReply = completionGuidance(assessment.errors)
        }
      }
      if (!advisorReply) {
        const result = await requestAdvisorGuidance({ attemptId: attempt.attempt_id, advisorContext: { message: body, task: { subject: selected.subject } } })
        advisorReply = result.advisor_reply || result.reply || 'Thanks - I have received your update.'
      }
      if (nextRepository !== repository) onRepositoryChange(nextRepository)
      setMessages((items) => items.map((item) => item.id === selected.id ? { ...item, replies: [...(item.replies || []), userMessage, { id: `advisor-${Date.now()}`, sender: selected.sender, role: selected.role, body: advisorReply }] } : item))
      setDraft('')
    } catch (requestError) { setError(requestError.message) }
    finally { setSending(false) }
  }
  return <div className="mail-layout"><aside className="mail-sidebar"><div className="mail-sidebar-title">Mail</div><nav className="mail-folders"><button className={`mail-folder${folder === 'inbox' ? ' is-active' : ''}`} type="button" onClick={() => setFolder('inbox')}><span>Inbox</span><span>Inbox</span><span className="folder-count">{messages.filter((item) => !item.sent && item.unread).length}</span></button><button className={`mail-folder${folder === 'sent' ? ' is-active' : ''}`} type="button" onClick={() => setFolder('sent')}><span>Sent</span><span>Sent</span><span className="folder-count">{messages.filter((item) => item.sent).length}</span></button></nav></aside><section className="mail-list-column"><div className="mail-list-toolbar"><div><h2>{folder === 'inbox' ? 'Inbox' : 'Sent'}</h2><span>Your workplace messages</span></div><input type="search" placeholder="Search mail" value={query} onChange={(event) => setQuery(event.target.value)} /></div><div className="mail-message-list">{visible.map((message) => <button className={`mail-list-item${selectedId === message.id ? ' is-selected' : ''}${message.unread ? ' is-unread' : ''}`} type="button" key={message.id} onClick={() => open(message.id)}><strong>{message.sender}</strong><span>{message.subject}</span><p>{message.body?.slice(0, 120)}</p></button>)}</div></section><section className="mail-reading-pane">{!selected ? <div className="mail-empty-state"><div className="mail-empty-icon">Mail</div><h2>Select a message</h2><p>Open an email from your inbox to read it here.</p></div> : <div className="mail-message-view"><header className="mail-message-header"><h1>{selected.subject}</h1><p>{selected.sender} · {selected.role}</p></header><div className="mail-thread"><article className="mail-thread-message"><strong>{selected.sender}</strong><p>{selected.body}</p></article>{selected.replies?.map((reply) => <article className="mail-thread-message" key={reply.id}><strong>{reply.sender}</strong><p>{reply.body}</p></article>)}</div>{selected.attachments?.length > 0 && <section className="mail-attachments"><h3>Attachments</h3><div className="mail-attachment-list">{selected.attachments.map((attachment) => <button className="mail-attachment-card" type="button" key={attachment.id || attachment.name} onClick={() => onDownload(attachment)}><span className="mail-attachment-icon">FILE</span><span className="mail-attachment-info"><strong>{attachment.name}</strong><small>{downloadedAttachments.some((item) => item.name === attachment.name) ? 'Saved to Downloads' : attachment.size || 'Attachment'}</small></span></button>)}</div></section>}<section className="mail-composer"><div className="mail-composer-header"><span>To:</span><strong>{selected.sender}</strong></div><textarea rows="6" placeholder="Write your reply..." value={draft} onChange={(event) => setDraft(event.target.value)} /><p className="mail-draft-status">{error}</p><div className="mail-compose-actions"><button className="mail-send-button" type="button" disabled={sending || !draft.trim()} onClick={send}>{sending ? 'Sending...' : 'Send'}</button></div></section></div>}</section></div>
}

export default MailApp
