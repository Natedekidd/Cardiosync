import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { getToken } from './api'
import Splash from './screens/splash'
import Onboarding from './screens/onboarding'
import Auth from './screens/Auth'
import Dashboard from './screens/Dashboard'
import PatientData from './screens/PatientData'
import Simulation from './screens/Simulation'
import Medications from './screens/Medications'
import RiskAnalysis from './screens/RiskAnalysis'
import ActionPlan from './screens/ActionPlan'
import Profile from './screens/Profile'

// Protect routes - redirect to /auth if not logged in
function PrivateRoute({ children }) {
  return getToken() ? children : <Navigate to="/auth" replace />
}

function App() {
  return (
    <BrowserRouter>
      <div className="phone-frame">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Splash />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/auth" element={<Auth />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/patient" element={<PrivateRoute><PatientData /></PrivateRoute>} />
          <Route path="/risk" element={<PrivateRoute><RiskAnalysis /></PrivateRoute>} />
          <Route path="/simulation" element={<PrivateRoute><Simulation /></PrivateRoute>} />
          <Route path="/medications" element={<PrivateRoute><Medications /></PrivateRoute>} />
          <Route path="/action" element={<PrivateRoute><ActionPlan /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App