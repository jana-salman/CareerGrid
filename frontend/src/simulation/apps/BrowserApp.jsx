import { useState } from 'react'

const titles = {
  'careergrid://api-status': 'API Status',
  'careergrid://documentation': 'Documentation',
  'careergrid://home': 'Home',
  'careergrid://logs': 'Logs',
  'careergrid://product': 'Product Page',
  'careergrid://snake': 'Snake',
}

function BrowserApp({ attempt }) {
  const [address, setAddress] = useState('careergrid://home')
  const [draftAddress, setDraftAddress] = useState(address)
  const [devtoolsTab, setDevtoolsTab] = useState('network')
  const [collapsed, setCollapsed] = useState(false)
  const scenario = attempt.public_scenario || {}

  const navigate = (nextAddress) => {
    const normalized = String(nextAddress || '').trim().toLowerCase()
    const target = normalized.startsWith('careergrid://') ? normalized : `careergrid://${normalized || 'home'}`
    setAddress(target)
    setDraftAddress(target)
  }
  const go = (event) => {
    event.preventDefault()
    navigate(draftAddress)
  }

  return (
    <div className="browser-layout">
      <div className="browser-tab-strip" role="tablist" aria-label="Browser tabs">
        <div className="browser-page-tab is-active">
          <button className="browser-tab-select" type="button" role="tab" aria-selected="true"><span>{titles[address] || 'Not found'}</span></button>
          <button className="browser-tab-close" type="button" aria-label="Close tab" onClick={() => navigate('careergrid://home')}>×</button>
        </div>
      </div>

      <div className="browser-toolbar">
        <div className="browser-navigation" aria-label="Browser navigation">
          <button type="button" title="Back" aria-label="Back" disabled>←</button>
          <button type="button" title="Forward" aria-label="Forward" disabled>→</button>
          <button type="button" title="Reload" aria-label="Reload" onClick={() => navigate(address)}>↻</button>
          <button type="button" title="Home" aria-label="Home" onClick={() => navigate('careergrid://home')}>⌂</button>
        </div>
        <form className="browser-address-form" onSubmit={go}>
          <span className="browser-scheme-icon" aria-hidden="true">◇</span>
          <input className="browser-address" aria-label="Address" value={draftAddress} onChange={(event) => setDraftAddress(event.target.value)} spellCheck="false" />
        </form>
        <button className="browser-new-tab" type="button" title="New tab" aria-label="New tab" onClick={() => navigate('careergrid://home')}>＋</button>
      </div>

      <div className="browser-loading" aria-hidden="true" />
      <div className={`browser-viewport${collapsed ? ' is-devtools-collapsed' : ''}`}>
        <main className="browser-page" tabIndex="-1">
          <BrowserPage address={address} navigate={navigate} scenario={scenario} />
        </main>
        <aside className="browser-devtools" aria-label="Developer tools">
          <div className="browser-devtools-tabs" role="tablist">
            {['network', 'console', 'elements'].map((tab) => (
              <button className={`browser-devtools-tab${devtoolsTab === tab ? ' is-active' : ''}`} type="button" key={tab} onClick={() => setDevtoolsTab(tab)}>
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
            <button className="browser-devtools-toggle" type="button" aria-expanded={!collapsed} title={`${collapsed ? 'Expand' : 'Collapse'} DevTools`} onClick={() => setCollapsed((value) => !value)}>{collapsed ? '⌃' : '⌄'}</button>
          </div>
          <div className="browser-devtools-content"><DevtoolsContent scenario={scenario} tab={devtoolsTab} /></div>
        </aside>
      </div>
    </div>
  )
}

function BrowserPage({ address, navigate, scenario }) {
  if (address === 'careergrid://snake') return <Snake />
  if (address === 'careergrid://product') return (
    <section className="product-demo">
      <div className="viewport-buttons"><button type="button">Desktop</button><button type="button">Tablet</button><button type="button">Mobile</button></div>
      <div><small>Task preview</small><h1>{scenario.task?.subject || 'Workplace task'}</h1><p>{scenario.task?.summary || scenario.task?.body || 'Task-related product evidence.'}</p><button type="button">Open task</button></div>
    </section>
  )
  if (address === 'careergrid://api-status') return (
    <section className="internal-page"><div className="internal-page-heading"><span>LIVE SIMULATION</span><h1>API status</h1><p>{scenario.task?.subject || 'Generated workplace services'}</p></div><div className="status-grid"><article><small>API health</small><strong className="status-warning">Investigate</strong></article><article><small>Database</small><strong className="status-good">Connected</strong></article><article><small>Authentication</small><strong className="status-good">Operational</strong></article><article><small>Environment</small><strong>Simulated</strong></article></div><div className="incident-card"><h2>Recent incidents</h2><p>Review the current task and public evidence in Developer Tools.</p></div></section>
  )
  if (address === 'careergrid://documentation') return (
    <section className="internal-page"><div className="internal-page-heading"><span>REFERENCE</span><h1>API documentation</h1><p>Endpoints relevant to this simulated workplace task.</p></div><div className="endpoint-list"><article className="endpoint-doc"><b className="method-get">GET</b><code>/api/health</code><span>Simulated endpoint</span></article><article className="endpoint-doc"><b className="method-post">POST</b><code>/api/workplace</code><span>Task-related endpoint</span></article></div></section>
  )
  if (address === 'careergrid://logs') return (
    <section className="internal-page"><div className="internal-page-heading"><span>OBSERVABILITY</span><h1>Application logs</h1><p>Public evidence from the current simulation scenario.</p></div><div className="internal-logs">{(scenario.resources || []).slice(0, 8).map((resource) => <div className="log-info" key={resource.id || resource.name}><b>INFO</b><span>{resource.name}: {String(resource.content || '').split('\n')[0]}</span></div>)}</div></section>
  )
  if (address !== 'careergrid://home') return (
    <section className="internal-page internal-error"><strong>404</strong><h1>Internal page not found</h1><p><code>{address}</code> is not an available CareerGrid page.</p><button type="button" onClick={() => navigate('careergrid://home')}>Return home</button></section>
  )
  return (
    <section className="internal-page internal-home">
      <div className="internal-hero"><span>CAREERGRID INTERNAL</span><h1>Developer workspace</h1><p>Inspect the simulated services, review task evidence, or take a debug break.</p></div>
      <div className="internal-card-grid">
        {attemptCard('careergrid://api-status', '◉', 'API Status', 'Health and incident information', navigate)}
        {attemptCard('careergrid://documentation', '⌘', 'API Documentation', 'Endpoints relevant to this task', navigate)}
        {attemptCard('careergrid://logs', '≡', 'Logs', 'Scenario-derived application events', navigate)}
        {attemptCard('careergrid://snake', '◇', 'Snake Debug Break', 'Take a short break while the deployment finishes.', navigate)}
      </div>
    </section>
  )
}

function attemptCard(url, icon, title, description, navigate) {
  return <button className="internal-card" type="button" key={url} onClick={() => navigate(url)}><span>{icon}</span><strong>{title}</strong><small>{description}</small></button>
}

function DevtoolsContent({ scenario, tab }) {
  if (tab === 'console') return <div className="console-output"><div className="console-info"><b>INFO</b> DevTools connected to the CareerGrid simulated API.</div><div className="console-success"><b>SUCCESS</b> Public scenario evidence loaded safely.</div></div>
  if (tab === 'elements') return <div className="devtools-empty">Select an internal page element to inspect its simulated structure.</div>
  return <><div className="network-tools"><button className="is-active" type="button">All</button><button type="button">Fetch/XHR</button></div><div className="network-table"><div className="network-columns"><span>Method</span><span>Name</span><span>Status</span><span>Type</span><span>Time</span><span>Duration</span></div><button className="network-row" type="button"><span>GET</span><span>/api/health</span><span className="status-good">200</span><span>fetch</span><span>Now</span><span>42 ms</span></button>{scenario.task && <button className="network-row" type="button"><span>GET</span><span>/api/task-evidence</span><span className="status-good">200</span><span>fetch</span><span>Now</span><span>73 ms</span></button>}</div></>
}

function Snake() {
  const [score, setScore] = useState(0)
  return <section className="snake-game"><h2>Snake</h2><p>Score: {score}</p><button type="button" onClick={() => setScore((value) => value + 1)}>Move snake</button></section>
}

export default BrowserApp
