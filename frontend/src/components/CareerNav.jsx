import { Link } from 'react-router-dom'

function CareerNav({ backTo, backLabel, showDashboard = false }) {
  return (
    <nav className="navbar">
      <h2 className="logo">CareerGrid</h2>
      {backTo ? (
        <Link to={backTo}>{backLabel}</Link>
      ) : (
        <div>
          <Link to="/">Home</Link>
          {showDashboard && <a href="/dashboard">Dashboard</a>}
        </div>
      )}
    </nav>
  )
}

export default CareerNav
