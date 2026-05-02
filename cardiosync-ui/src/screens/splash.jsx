import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../css/splash.css'

function Splash() {
  const navigate = useNavigate()

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate('/onboarding')
    }, 3500)
    return () => clearTimeout(timer)
  }, [navigate])

  return (
    <div className="splash-screen">
      <div className="dna-bg">
        <img src="/assets/Images/dna-pattern.png" alt="DNA" className="dna-img"/>
      </div>
      <h1 className="logo">Cardiosync</h1>
    </div>
  )
}

export default Splash