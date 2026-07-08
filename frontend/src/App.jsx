import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Demo from "./pages/Demo";
import HowItWorks from "./pages/HowItWorks";
import Benefits from "./pages/Benefits";
import AIEngine from "./pages/AIEngine";
import Portfolio from "./pages/Portfolio";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/demo" replace />} />
        <Route path="demo" element={<Demo />} />
        <Route path="how-it-works" element={<HowItWorks />} />
        <Route path="benefits" element={<Benefits />} />
        <Route path="ai-engine" element={<AIEngine />} />
        <Route path="portfolio" element={<Portfolio />} />
      </Route>
    </Routes>
  );
}
