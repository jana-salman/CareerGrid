import { BrowserRouter, Route, Routes } from 'react-router-dom'

import FoundationPage from './pages/FoundationPage.jsx'
import routeDefinitions from './routeDefinitions.js'

function CareerGridRoutes() {
  return (
    <Routes>
      {routeDefinitions.map(({ path, title }) => (
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
