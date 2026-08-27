import { BrowserRouter, Route, Routes } from 'react-router-dom'

import FoundationPage from './pages/FoundationPage.jsx'
import CareerPage from './pages/CareerPage.jsx'
import CompanyPage from './pages/CompanyPage.jsx'
import HomePage from './pages/HomePage.jsx'
import PositionPage from './pages/PositionPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import WorkplaceReportPage from './pages/WorkplaceReportPage.jsx'
import SimulationDesktop from './simulation/SimulationDesktop.jsx'
import routeDefinitions from './routeDefinitions.js'

function CareerGridRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/career" element={<CareerPage />} />
      <Route path="/positions/:careerId" element={<PositionPage />} />
      <Route path="/positions/:careerId/:positionId" element={<CompanyPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/simulation/attempts/:attemptId/report" element={<WorkplaceReportPage />} />
      <Route path="/workspace/attempt/:attemptId" element={<SimulationDesktop />} />
      {routeDefinitions.filter(({ path }) => ![
        '/',
        '/career',
        '/positions/:careerId',
        '/positions/:careerId/:positionId',
        '/dashboard',
        '/simulation/attempts/:attemptId/report',
        '/workspace/attempt/:attemptId',
      ].includes(path)).map(({ path, title }) => (
        <Route
          key={path}
          path={path}
          element={<FoundationPage title={title} />}
        />
      ))}
      <Route path="*" element={<FoundationPage title="Page not found" />} />
    </Routes>
  )
}

function AppRouter() {
  return (
    <BrowserRouter>
      <CareerGridRoutes />
    </BrowserRouter>
  )
}

export { CareerGridRoutes }
export default AppRouter
