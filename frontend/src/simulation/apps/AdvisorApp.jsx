const guideSteps = [
  ['1. Check Mail', 'Tasks and advisor messages arrive through your inbox.'],
  ['2. Use your tools', 'Investigate files, code, browser behavior and logs.'],
  ['3. Ask naturally', "If you get stuck, message your advisor and explain what you've tried."],
  ['4. Deliver your work', 'Submit your work and communicate your findings through the appropriate tools.'],
]

function AdvisorApp() {
  return <div className="guide-content">
    <span className="welcome-label">How CareerGrid works</span>
    <h2>Treat this workspace like a real workday.</h2>
    {guideSteps.map(([title, body]) => <div className="guide-step" key={title}><strong>{title}</strong><p>{body}</p></div>)}
  </div>
}

export default AdvisorApp
