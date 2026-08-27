import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import CareerNav from '../components/CareerNav.jsx'
import { getCompanies } from '../services/careerApi.js'

function CompanyPage() {
  const { careerId, positionId } = useParams()
  const [catalog, setCatalog] = useState(null)
  useEffect(() => {
    getCompanies(careerId, positionId)
      .then(setCatalog)
      .catch((error) => {
        if (error.status === 401) window.location.assign('/login')
        else setCatalog({ companies: [], position_title: 'Position' })
      })
  }, [careerId, positionId])
  return <div className="career-page"><CareerNav backTo={`/positions/${careerId}`} backLabel="Back to Positions" /><div className="simulation-header"><span className="selection-kicker">CareerGrid workspace</span><h1>{catalog?.position_title || 'Position'}</h1><p>Choose your company workspace and begin your workplace simulation.</p></div><div className="job-list">{catalog?.companies.map((company) => <div className="job-card" key={`${company.job_source}-${company.company_id}`}><div className="job-card-main"><h3>{company.title}</h3><p className="job-company">{company.company_name}</p><p className="job-location">{company.location}</p><p className="job-description">{company.description}</p></div><div className="job-card-side"><span className="job-status">{company.status}</span><form method="post" action="/simulation/workplace/start"><input type="hidden" name="career_id" value={careerId} /><input type="hidden" name="position_id" value={positionId} /><input type="hidden" name="company_id" value={company.company_id} /><input type="hidden" name="job_source" value={company.job_source} /><button type="submit" className="main-btn">Enter Workspace</button></form></div></div>)}</div></div>
}

export default CompanyPage
