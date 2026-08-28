import { useEffect } from 'react'
import { Link } from 'react-router-dom'

import { prefetchDashboard } from '../services/dashboardApi.js'

function CareerNav({ backTo, backLabel, showDashboard = false }) {
  const warmDashboard = () => {
    prefetchDashboard().catch(() => {})
  }

  useEffect(() => {
    if (showDashboard) {
      warmDashboard()
    }
  }, [showDashboard])

  return (
    <nav className="navbar">
      <h2 className="logo">CareerGrid</h2>
      {backTo ? (
        <Link to={backTo}>{backLabel}</Link>
      ) : (
        <div>
          <Link to="/">Home</Link>
          {showDashboard && (
            <Link to="/dashboard" onFocus={warmDashboard} onMouseEnter={warmDashboard}>
              Dashboard
            </Link>
          )}
        </div>
      )}
    </nav>
  )
}

export default CareerNav
