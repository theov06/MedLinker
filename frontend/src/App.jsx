import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { HomePage } from './sections/HomePage/HomePage';
import { Finder } from './sections/Finder/Finder';
import { Chatbot } from './sections/Chatbot/Chatbot';
import { Profile } from './sections/Profile/Profile';

export default function App() {
  return (
    <BrowserRouter>
      <div className="h-screen flex bg-bg-main">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/finder" element={<Finder />} />
            <Route path="/chatbot" element={<Chatbot />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}