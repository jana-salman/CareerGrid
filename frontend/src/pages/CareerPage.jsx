import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import CareerNav from '../components/CareerNav.jsx'
import { getCareers } from '../services/careerApi.js'

function CareerPage() {
  const [careers, setCareers] = useState([])
  useEffect(() => {
    getCareers()
      .then(({ careers: data }) => setCareers(data))
      .catch((error) => {
        if (error.status === 401) window.location.assign('/login')
      })
  }, [])
  return <div className="career-page"><CareerNav showDashboard /><div className="career-header"><h1>Choose a Career Path</h1><p>Select a career you want to explore through an interactive simulation.</p></div><div className="career-grid">{careers.map((career) => <div className={`career-card${career.available ? '' : ' career-card--unavailable'}`} key={career.id}><div className="career-icon">{career.icon}</div><h3>{career.title}</h3><p>{career.description}</p>{career.available ? <Link to={`/positions/${career.id}`}>View Positions</Link> : <button className="coming-soon-control" type="button" disabled>Coming Soon</button>}</div>)}</div></div>
}

export default CareerPage
