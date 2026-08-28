import { useState } from 'react'

import { requestAdvisorGuidance } from '../../services/simulationApi.js'

const guideSteps = [
  ['1. Check Mail', 'Tasks and advisor messages arrive through your inbox.'],
  ['2. Use your tools', 'Investigate files, code, browser behavior and logs.'],
  ['3. Ask naturally', "If you get stuck, message your advisor and explain what you've tried."],
  ['4. Deliver your work', 'Submit your work and communicate your findings through the appropriate tools.'],
]

function AdvisorApp({ attempt }) {
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const send = async (event) => {
    event.preventDefault()
    if (!text.trim()) return
    const question = text.trim()
    setMessages((items) => [...items, { body: question, from: 'You' }])
    setText('')
    setLoading(true)
    setError('')
    try {
      const result = await requestAdvisorGuidance({
        advisorContext: { question, task: { subject: attempt.public_scenario?.task?.subject } },
        attemptId: attempt.attempt_id,
      })
      setMessages((items) => [...items, {
        body: result.advisor_reply || result.reply || 'Guidance is currently unavailable.',
        from: 'Advisor',
      }])
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return <div className="guide-content">
    <span className="welcome-label">How CareerGrid works</span>
    <h2>Treat this workspace like a real workday.</h2>
    {guideSteps.map(([title, body]) => <div className="guide-step" key={title}><strong>{title}</strong><p>{body}</p></div>)}
    {messages.map((message, index) => <article className="guide-step" key={`${message.from}-${index}`}><strong>{message.from}</strong><p>{message.body}</p></article>)}
    <form className="github-pr-form" onSubmit={send}>
      <label className="github-form-field">Ask your advisor<textarea className="github-form-control" rows="4" value={text} onChange={(event) => setText(event.target.value)} placeholder="Describe what you tried or ask a question." /></label>
      <p className="github-form-error">{error}</p>
      <div className="github-form-actions"><button className="open-mail-btn" disabled={loading} type="submit">{loading ? 'Thinking...' : 'Ask advisor'}</button></div>
    </form>
  </div>
}

export default AdvisorApp
