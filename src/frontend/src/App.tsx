import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import TopologyViewer from './components/TopologyViewer'
// import TimelinePlayer from './components/TimelinePlayer'
import './App.css'

function App() {
  const [scenarioId, setScenarioId] = useState<string | null>(null)

  // Animation state (Disabled for Real-time)
  // const [time, setTime] = useState(0)
  // const [maxTime, setMaxTime] = useState(1000)
  // const [isPlaying, setIsPlaying] = useState(false)

  const handleScenarioGenerated = (id: string) => {
    setScenarioId(id);
    // setTime(0);
    // setIsPlaying(false);
    // setMaxTime(2000); 
  };

  return (
    <div className="app-container">
      <div className="left-panel">
        <ChatInterface onScenarioGenerated={handleScenarioGenerated} />
      </div>
      <div className="right-panel">
        {scenarioId ? (
          <>
            <TopologyViewer
              scenarioId={scenarioId}
            />
            {/* TimelinePlayer disabled for Real-time mode
            <TimelinePlayer
              time={time}
              setTime={setTime}
              maxTime={maxTime}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
            />
            */}
          </>
        ) : (
          <div className="placeholder">
            <p>Start a conversation to visualize Kubernetes behavior</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
