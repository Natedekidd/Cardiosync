import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../css/onboarding.css'

const cards = [
  {
    title: <>Understand <br/><strong>Your Heart</strong><br/>and Own <strong>Your Future.</strong></>,
    text: 'CardioSync analyzes your vitals, genetics, and lifestyle to give you a clear picture of your cardiovascular health, starting today.',
  },
  {
    title: <>Track Your <br/><strong>Vitals</strong><br/>Every <strong>Single Day.</strong></>,
    text: 'Monitor your heart rate, blood pressure, and activity in real time all in one place.',
  },
  {
    title: <>Live <br/><strong>Healthier</strong><br/>Starting <strong>Right Now.</strong></>,
    text: 'Get personalized recommendations based on your unique cardiovascular profile.',
  },
]

function Onboarding() {
  const [current, setCurrent] = useState(0)
  const navigate = useNavigate()

  const handleNext = () => {
    if (current < cards.length - 1) {
      setCurrent(current + 1)
    } else {
      navigate('/auth')
    }
  }

  return (
    <div className="onboarding-screen">
      <div className="carousel-wrapper">
        <div
          className="carousel-track"
          style={{ transform: `translateX(-${current * 100}%)` }}
        >
          {cards.map((card, index) => (
            <div className="card" key={index}>
              <div className="card-top">
                <h2 className="card-title">{card.title}</h2>
                <p className="card-text">{card.text}</p>
              </div>
              <div className="card-bottom">
                <img
                  src="/assets/Images/onboarding-illustration.png"
                  alt="People exercising"
                  className="illustration"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bottom-controls">
        <div className="dots">
          {cards.map((_, index) => (
            <span
              key={index}
              className={`dot ${index === current ? 'active' : ''}`}
            />
          ))}
        </div>
        <button className="btn-next" onClick={handleNext}>
          {current === cards.length - 1 ? 'Get Started' : 'Next'}
        </button>
      </div>
    </div>
  )
}

export default Onboarding