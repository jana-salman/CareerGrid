import { BrowserRouter, Route, Routes } from 'react-router-dom'

import FoundationPage from './pages/FoundationPage.jsx'
import CareerPage from './pages/CareerPage.jsx'
import CompanyPage from './pages/CompanyPage.jsx'
import HomePage from './pages/HomePage.jsx'
import PositionPage from './pages/PositionPage.jsx'
import routeDefinitions from './routeDefinitions.js'

function CareerGridRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/career" element={<CareerPage />} />
      <Route path="/positions/:careerId" element={<PositionPage />} />
      <Route path="/positions/:careerId/:positionId" element={<CompanyPage />} />
      {routeDefinitions.filter(({ path }) => ![
        '/',
        '/career',
        '/positions/:careerId',
        '/positions/:careerId/:positionId',
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
