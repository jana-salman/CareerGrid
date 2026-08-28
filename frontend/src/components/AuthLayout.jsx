import { useEffect } from 'react'
import { Link } from 'react-router-dom'

const puzzlePieces = [
  ['education', 'education-piece.png'],
  ['career', 'career-piece.png'],
  ['science', 'science-piece.png'],
  ['center', 'center-piece.png'],
  ['coding', 'coding-piece.png'],
  ['calculator', 'calculator-piece.png'],
  ['travel', 'travel-piece.png'],
]

function AuthLayout({ children, headingId }) {
  useEffect(() => {
    const stylesheet = document.createElement('link')
    stylesheet.rel = 'stylesheet'
    stylesheet.href = '/static/css/auth/login.css'
    stylesheet.dataset.careergridAuth = 'true'
    document.head.appendChild(stylesheet)
    document.body.classList.add('careergrid-login')

    return () => {
      document.body.classList.remove('careergrid-login')
      stylesheet.remove()
    }
  }, [])

  return (
    <main className="login-shell">
      <section className="login-intro" aria-labelledby="careergrid-heading">
        <Link className="careergrid-brand" to="/" aria-label="CareerGrid home">
          <span className="brand-mark" aria-hidden="true"><span /><span /><span /></span>
          <span><strong>CareerGrid</strong><small>Explore. Practice. Grow.</small></span>
        </Link>
        <div className="career-puzzle" aria-label="CareerGrid puzzle pieces connecting learning, skills, and careers" role="img">
          {puzzlePieces.map(([name, filename]) => (
            <img className={`puzzle-image puzzle-image--${name}`} src={`/static/images/login-puzzle/${filename}`} alt="" key={name} />
          ))}
          <div className="puzzle-shine" aria-hidden="true" />
        </div>
        <div className="intro-copy">
          <h1 id="careergrid-heading"><span>The missing piece</span> between education <em>and your career.</em></h1>
          <p>Step into realistic workplace simulations, solve practical challenges, and build the skills you need for your career.</p>
        </div>
        <ul className="login-benefits" aria-label="CareerGrid benefits">
          <li><span className="benefit-icon">◈</span><span><strong>Real-World Simulations</strong><small>Experience authentic workplace scenarios.</small></span></li>
          <li><span className="benefit-icon">◎</span><span><strong>Skill Development</strong><small>Build and apply skills employers value.</small></span></li>
          <li><span className="benefit-icon">↗</span><span><strong>Career Clarity</strong><small>Explore roles and discover what fits you.</small></span></li>
        </ul>
      </section>
      <section className="login-panel" aria-labelledby={headingId}>
        <div className="login-card">{children}</div>
      </section>
    </main>
  )
}

export default AuthLayout
