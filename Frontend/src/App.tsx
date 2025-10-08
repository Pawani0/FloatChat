import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage, DashboardPage, ChatBotPage } from './pages';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatBotPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;