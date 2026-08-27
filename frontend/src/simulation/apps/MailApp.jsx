import { useMemo, useState } from 'react'
import { requestAdvisorGuidance } from '../../services/simulationApi.js'

function createMessages(scenario) {
  const task = scenario.task || {}
  const advisor = scenario.advisor || {}
  const main = task.id ? [{ id: task.id, sender: advisor.name || 'CareerGrid Advisor', role: advisor.title || 'Advisor', subject: task.subject || 'Workplace task', body: task.body || task.summary || '', unread: true, task: true, attachments: task.attachments || scenario.attachments || [] }] : []
  return [...main, ...(scenario.background_emails || []).map((email, index) => ({ id: email.id || `background-${index}`, sender: email.sender_name, role: email.sender_title, subject: email.subject, body: email.body, unread: true, attachments: [] }))]
}

function MailApp({ attempt, downloadedAttachments, onDownload }) {
  const scenario = attempt.public_scenario || {}
  const [messages, setMessages] = useState(() => createMessages(scenario))
  const [folder, setFolder] = useState('inbox')
  const [selectedId, setSelectedId] = useState(null)
  const [query, setQuery] = useState('')
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const visible = useMemo(() => messages.filter((message) => (folder === 'sent' ? message.sent : !message.sent) && `${message.sender} ${message.subject}`.toLowerCase().includes(query.toLowerCase())), [folder, messages, query])
  const selected = messages.find((message) => message.id === selectedId)
  const open = (id) => { setSelectedId(id); setMessages((items) => items.map((item) => item.id === id ? { ...item, unread: false } : item)) }
  const send = async () => {
    if (!draft.trim() || !selected) return
    setSending(true); setError('')
    const userMessage = { id: `sent-${Date.now()}`, sender: 'You', role: 'You', body: draft.trim(), sent: true }
    setMessages((items) => items.map((item) => item.id === selected.id ? { ...item, replies: [...(item.replies || []), userMessage] } : item))
    try {
      const result = await requestAdvisorGuidance({ attemptId: attempt.attempt_id, advisorContext: { message: draft.trim(), task: { subject: selected.subject } } })
      const reply = result.advisor_reply || result.reply || 'Thanks - I have received your update.'
      setMessages((items) => items.map((item) => item.id === selected.id ? { ...item, replies: [...(item.replies || []), userMessage, { id: `advisor-${Date.now()}`, sender: selected.sender, role: selected.role, body: reply }] } : item))
      setDraft('')
    } catch (requestError) { setError(requestError.message) }
    finally { setSending(false) }
  }
  return <div className="mail-layout"><aside className="mail-sidebar"><div className="mail-sidebar-title">Mail</div><nav className="mail-folders"><button className={`mail-folder${folder === 'inbox' ? ' is-active' : ''}`} type="button" onClick={() => setFolder('inbox')}><span>Inbox</span><span>Inbox</span><span className="folder-count">{messages.filter((item) => !item.sent && item.unread).length}</span></button><button className={`mail-folder${folder === 'sent' ? ' is-active' : ''}`} type="button" onClick={() => setFolder('sent')}><span>Sent</span><span>Sent</span><span className="folder-count">{messages.filter((item) => item.sent).length}</span></button></nav></aside><section className="mail-list-column"><div className="mail-list-toolbar"><div><h2>{folder === 'inbox' ? 'Inbox' : 'Sent'}</h2><span>Your workplace messages</span></div><input type="search" placeholder="Search mail" value={query} onChange={(event) => setQuery(event.target.value)} /></div><div className="mail-message-list">{visible.map((message) => <button className={`mail-list-item${selectedId === message.id ? ' is-selected' : ''}${message.unread ? ' is-unread' : ''}`} type="button" key={message.id} onClick={() => open(message.id)}><strong>{message.sender}</strong><span>{message.subject}</span><p>{message.body?.slice(0, 120)}</p></button>)}</div></section><section className="mail-reading-pane">{!selected ? <div className="mail-empty-state"><div className="mail-empty-icon">Mail</div><h2>Select a message</h2><p>Open an email from your inbox to read it here.</p></div> : <div className="mail-message-view"><header className="mail-message-header"><h1>{selected.subject}</h1><p>{selected.sender} · {selected.role}</p></header><div className="mail-thread"><article className="mail-thread-message"><strong>{selected.sender}</strong><p>{selected.body}</p></article>{selected.replies?.map((reply) => <article className="mail-thread-message" key={reply.id}><strong>{reply.sender}</strong><p>{reply.body}</p></article>)}</div>{selected.attachments?.length > 0 && <section className="mail-attachments"><h3>Attachments</h3><div className="mail-attachment-list">{selected.attachments.map((attachment) => <button className="mail-attachment-card" type="button" key={attachment.id || attachment.name} onClick={() => onDownload(attachment)}><span className="mail-attachment-icon">FILE</span><span className="mail-attachment-info"><strong>{attachment.name}</strong><small>{downloadedAttachments.some((item) => item.name === attachment.name) ? 'Saved to Downloads' : attachment.size || 'Attachment'}</small></span></button>)}</div></section>}<section className="mail-composer"><div className="mail-composer-header"><span>To:</span><strong>{selected.sender}</strong></div><textarea rows="6" placeholder="Write your reply..." value={draft} onChange={(event) => setDraft(event.target.value)} /><p className="mail-draft-status">{error}</p><div className="mail-compose-actions"><button className="mail-send-button" type="button" disabled={sending || !draft.trim()} onClick={send}>{sending ? 'Sending...' : 'Send'}</button></div></section></div>}</section></div>
}

export default MailApp
