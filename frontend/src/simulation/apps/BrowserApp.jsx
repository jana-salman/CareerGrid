import { useState } from 'react'

function BrowserApp({ attempt }) {
  const [address, setAddress] = useState('careergrid://home')
  const scenario = attempt.public_scenario || {}
  const pages = { 'careergrid://home': <><h2>CareerGrid Browser</h2><p>Use this simulated browser to inspect workspace evidence.</p></>, 'careergrid://product': <><h2>Product preview</h2><p>{scenario.task?.summary || 'Task-related product evidence.'}</p></>, 'careergrid://snake': <Snake /> }
  const go = (event) => { event.preventDefault(); if (!pages[address]) setAddress('careergrid://home') }
  return <div className="browser-layout"><div className="browser-toolbar"><button type="button" onClick={() => setAddress('careergrid://home')}>Home</button><form onSubmit={go}><input className="browser-address" value={address} onChange={(event) => setAddress(event.target.value)} /></form><button type="button" onClick={go}>Refresh</button></div><main className="browser-page">{pages[address] || pages['careergrid://home']}<p><button onClick={() => setAddress('careergrid://product')} type="button">Open task page</button> <button onClick={() => setAddress('careergrid://snake')} type="button">Open Snake</button></p></main></div>
}
function Snake() { const [score, setScore] = useState(0); return <section className="snake-game"><h2>Snake</h2><p>Score: {score}</p><button type="button" onClick={() => setScore((value) => value + 1)}>Move snake</button></section> }
export default BrowserApp
