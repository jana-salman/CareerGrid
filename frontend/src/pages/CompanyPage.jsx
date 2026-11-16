import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import CareerNav from '../components/CareerNav.jsx'
import { getCompanies, getPositions } from '../services/careerApi.js'
import { startWorkplaceSimulation } from '../services/simulationApi.js'

const SEARCH_MESSAGES = {
  no_results: 'No live listings matched right now.',
  not_configured: 'Live listings are not configured on this server.',
  provider_error: 'The job provider could not be reached.',
  unsupported_location: 'Live listings are not available for this location.',
}

// The server bounds generation (time budget, then a built-in fallback), so the
// browser waits a little longer than that before offering a retry.
const LAUNCH_TIMEOUT_MS = 6 * 60 * 1000

function newRequestId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

function CompanyPage() {
  const { careerId, positionId } = useParams()
  const navigate = useNavigate()
  // The role title comes from the local catalogue, so it never waits on the
  // external job provider that the listings depend on.
  const [role, setRole] = useState({ status: 'loading', title: '' })
  const [catalog, setCatalog] = useState(null)
  const [catalogState, setCatalogState] = useState({ status: 'loading', error: '' })
  const [launch, setLaunch] = useState({ status: 'idle', company: null, error: '' })
  // One request id per listing: a retry reuses it, so the server resumes the
  // same attempt instead of creating a duplicate.
  const requestIds = useRef(new Map())
  const pending = launch.status === 'pending'

  const handleAuthError = (error) => {
    if (error.status === 401) {
      window.location.assign('/login')
      return true
    }
    return false
  }

  useEffect(() => {
    let active = true
    setRole({ status: 'loading', title: '' })
    getPositions(careerId)
      .then((data) => {
        if (!active) return
        const position = data.positions?.find((item) => item.id === positionId)
        setRole(position ? { status: 'ready', title: position.title } : { status: 'missing', title: '' })
      })
      .catch((error) => { if (active && !handleAuthError(error)) setRole({ status: 'error', title: '' }) })
    return () => { active = false }
  }, [careerId, positionId])

  const loadCompanies = useCallback(() => {
    let active = true
    setCatalog(null)
    setCatalogState({ status: 'loading', error: '' })
    getCompanies(careerId, positionId)
      .then((data) => {
        if (!active) return
        setCatalog(data)
        setCatalogState({ status: 'ready', error: '' })
      })
      .catch((error) => {
        if (active && !handleAuthError(error)) {
          setCatalogState({ status: 'error', error: error.message || 'Companies could not be loaded.' })
        }
      })
    return () => { active = false }
  }, [careerId, positionId])

  useEffect(() => loadCompanies(), [loadCompanies])

  const title = role.title || catalog?.position_title || ''

  const start = async (company) => {
    if (pending) return
    const key = `${company.job_source}:${company.company_id}`
    if (!requestIds.current.has(key)) requestIds.current.set(key, newRequestId())
    setLaunch({ status: 'pending', company, error: '' })
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), LAUNCH_TIMEOUT_MS)
    try {
      const result = await startWorkplaceSimulation({
        signal: controller.signal,
        careerId,
        positionId,
        companyId: company.company_id,
        jobSource: company.job_source,
        jobContext: company.listing_kind === 'live'
          ? {
              title: company.title,
              company: company.company_name,
              location: company.location,
              description: company.full_description || company.description,
              url: company.url,
            }
          : null,
        clientRequestId: requestIds.current.get(key),
      })
      navigate(result.workspace_url || `/workspace/attempt/${encodeURIComponent(result.attempt_id)}`)
    } catch (error) {
      if (handleAuthError(error)) return
      setLaunch({
        status: 'error',
        company,
        error: controller.signal.aborted
          ? 'Preparing your task is taking longer than expected. Try again to pick up the same workspace.'
          : error.message || 'CareerGrid could not prepare your workspace.',
        retryable: controller.signal.aborted || error.data?.retryable !== false,
      })
    } finally {
      window.clearTimeout(timer)
    }
  }

  const search = catalog?.job_search
  const searchMessage = search ? SEARCH_MESSAGES[search.status] : null

  return <div className="career-page" aria-busy={pending || catalogState.status === 'loading'}>
    <CareerNav backTo={`/positions/${careerId}`} backLabel="Back to Positions" />
    <div className="simulation-header">
      <span className="selection-kicker">CareerGrid workspace</span>
      <h1>{title || (role.status === 'loading' ? 'Loading role…' : 'Role unavailable')}</h1>
      <p>
        {role.status === 'missing'
          ? 'This role could not be found. Go back to choose another position.'
          : 'Choose your company workspace and begin your workplace simulation.'}
      </p>
    </div>

    {pending && (
      <div className="workspace-launch-overlay" role="status" aria-live="polite">
        <div className="workspace-launch-card">
          <span className="workspace-launch-spinner" aria-hidden="true" />
          <h2>Preparing your workspace…</h2>
          <p>We're generating a {title || 'workplace'} task for {launch.company?.company_name || 'your chosen company'}. We check each task for depth and consistency, which usually takes one to three minutes. Please keep this page open.</p>
        </div>
      </div>
    )}

    {launch.status === 'error' && (
      <div className="workspace-launch-error" role="alert">
        <strong>We couldn't prepare your workspace.</strong>
        <p>{launch.error}</p>
        <div className="workspace-launch-actions">
          {launch.retryable && <button type="button" className="main-btn" onClick={() => start(launch.company)}>Try again</button>}
          <button type="button" className="secondary-btn" onClick={() => setLaunch({ status: 'idle', company: null, error: '' })}>Choose another company</button>
        </div>
      </div>
    )}

    {catalogState.status === 'loading' && (
      <p className="job-search-status" role="status">Loading companies and live listings…</p>
    )}
    {catalogState.status === 'error' && (
      <div className="workspace-launch-error" role="alert">
        <strong>Companies could not be loaded.</strong>
        <p>{catalogState.error}</p>
        <div className="workspace-launch-actions">
          <button type="button" className="main-btn" onClick={loadCompanies}>Try again</button>
        </div>
      </div>
    )}
    {searchMessage && (
      <p className="job-search-status" role="status">
        {searchMessage} {search.message} The companies below are practice simulations, not live vacancies.
      </p>
    )}

    <div className="job-list">{catalog?.companies.map((company) => <div className="job-card" key={`${company.job_source}-${company.company_id}`}>
      <div className="job-card-main">
        <h3>{company.title}</h3>
        <p className="job-company">{company.company_name}</p>
        <p className="job-location">{company.location}</p>
        <p className="job-description">{company.description}</p>
        {company.listing_kind === 'live' && (
          <p className="job-source">
            Source: {company.source_label}
            {company.url && <> · <a href={company.url} target="_blank" rel="noreferrer">View original listing</a></>}
          </p>
        )}
      </div>
      <div className="job-card-side">
        <span className="job-status">{company.status}</span>
        <button type="button" className="main-btn" disabled={pending} onClick={() => start(company)}>Enter Workspace</button>
      </div>
    </div>)}</div>

    {search?.status === 'ok' && search.attribution && (
      <p className="job-search-attribution">
        Live listings: <a href={search.attribution.url} target="_blank" rel="noreferrer">{search.attribution.label}</a>
      </p>
    )}
  </div>
}

export default CompanyPage
