const routeDefinitions = [
  { path: '/', title: 'CareerGrid' },
  { path: '/login', title: 'Login' },
  { path: '/register', title: 'Register' },
  { path: '/dashboard', title: 'Dashboard' },
  { path: '/career', title: 'Career selection' },
  { path: '/positions/:careerId', title: 'Position selection' },
  {
    path: '/positions/:careerId/:positionId',
    title: 'Company selection',
  },
  {
    path: '/workspace/:careerId/:positionId/:companyId',
    title: 'Workplace simulation',
  },
  {
    path: '/workspace/attempt/:attemptId',
    title: 'Workplace simulation attempt',
  },
  {
    path: '/simulation/attempts/:attemptId/report',
    title: 'Simulation report',
  },
  { path: '/interview/:interviewId', title: 'Interview' },
  {
    path: '/interview/:interviewId/review',
    title: 'Interview review',
  },
]

export default routeDefinitions
