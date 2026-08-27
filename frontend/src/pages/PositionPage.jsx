import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import CareerNav from '../components/CareerNav.jsx'
import { getPositions } from '../services/careerApi.js'

function PositionPage() {
  const { careerId } = useParams()
  const [catalog, setCatalog] = useState(null)
  useEffect(() => {
    getPositions(careerId)
      .then(setCatalog)
      .catch((error) => {
        if (error.status === 401) window.location.assign('/login')
        else setCatalog({ positions: [], career_name: 'Career' })
      })
  }, [careerId])
  return <div className="career-page"><CareerNav backTo="/career" backLabel="Back to Careers" /><div className="simulation-header"><span className="selection-kicker">Career path</span><h1>{catalog?.career_name || 'Career'}</h1><p>Choose your position to see available companies.</p></div><div className="career-grid">{catalog?.positions.map((position) => <div className={`career-card${position.available ? '' : ' career-card--unavailable'}`} key={position.id}><h3>{position.title}</h3><p>Explore companies offering this role</p>{position.available ? <Link to={`/positions/${careerId}/${position.id}`}>View Companies</Link> : <button className="coming-soon-control" type="button" disabled>Coming Soon</button>}</div>)}</div></div>
}

export default PositionPage
