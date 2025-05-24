import { Routes, Route, Navigate } from 'react-router-dom'; // Removed AuthProvider
// Removed AuthProvider import
import Header from "./components/Header";
import Home from "./pages/Home";
import SpeechTestPage from "./pages/SpeechTestPage";
import ChatBot from './components/ChatBot'; // Import ChatBot
import LoginPage from './pages/LoginPage'; // Import LoginPage
import SummaryPage from './pages/SummaryPage'; // Import SummaryPage
import LaunchPage from './pages/LaunchPage'; // Import the new LaunchPage
import PrivateRoute from './components/PrivateRoute'; // Import PrivateRoute

function App() {
  return (
    // <AuthProvider>  Removed AuthProvider wrapper
    <>
        <Header />
        <div className="pt-16 sm:pt-20"> {/* Add padding to prevent content from being hidden behind fixed header */}
          <Routes>
            <Route path="/launch" element={<LaunchPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<LaunchPage />} /> {/* Default route is LaunchPage */}
            
            {/* Protected Routes */}
            <Route element={<PrivateRoute />}>
              <Route path="/home" element={<Home />} />
              <Route path="/chatbot" element={<ChatBot />} />
              <Route path="/summary" element={<SummaryPage />} />
            </Route>
            
            <Route path="/speech-test" element={<SpeechTestPage />} />
            {/* Redirect to /launch if no other route matches */}
            <Route path="*" element={<Navigate to="/launch" replace />} />
          </Routes>
        </div>
    </>
    // </AuthProvider> Removed AuthProvider wrapper
  );
}

export default App
