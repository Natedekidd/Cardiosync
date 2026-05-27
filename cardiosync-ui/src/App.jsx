import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { createContext, useContext, useState } from 'react'
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
import Help from './screens/Help'

// inside Routes:
<Route path="/help" element={<PrivateRoute><Help /></PrivateRoute>} />

// Theme context
export const ThemeContext = createContext()
export const useTheme = () => useContext(ThemeContext)

function PrivateRoute({ children }) {
  return getToken() ? children : <Navigate to="/auth" replace />
}

function App() {
  const [darkMode, setDarkMode] = useState(false)
  const toggleTheme = () => setDarkMode(prev => !prev)

  return (
    <ThemeContext.Provider value={{ darkMode, toggleTheme }}>
      <BrowserRouter>
        <div className={`phone-frame ${darkMode ? 'dark' : ''}`}>
          <Routes>
            <Route path="/" element={<Splash />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/auth" element={<Auth />} />

            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/patient" element={<PrivateRoute><PatientData /></PrivateRoute>} />
            <Route path="/risk" element={<PrivateRoute><RiskAnalysis /></PrivateRoute>} />
            <Route path="/simulation" element={<PrivateRoute><Simulation /></PrivateRoute>} />
            <Route path="/medications" element={<PrivateRoute><Medications /></PrivateRoute>} />
            <Route path="/action" element={<PrivateRoute><ActionPlan /></PrivateRoute>} />
            <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
            <Route path="/help" element={<PrivateRoute><Help /></PrivateRoute>} />
          </Routes>
        </div>
      </BrowserRouter>
    </ThemeContext.Provider>
  )
}

export default App