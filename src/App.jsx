import { Routes, Route } from 'react-router-dom'; // Import Routes and Route
import Header from "./components/Header";
import Home from "./pages/Home";
import SpeechTestPage from "./pages/SpeechTestPage";
import ChatBot from './components/ChatBot'; // Import ChatBot

function App() {

  return (
    <>
      <Header />
      <div className="pt-16 sm:pt-20"> {/* Add padding to prevent content from being hidden behind fixed header */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/speech-test" element={<SpeechTestPage />} />
          <Route path="/chatbot" element={<ChatBot />} /> {/* Add route for ChatBot */}
        </Routes>
      </div>
    </>
  )
}

export default App
