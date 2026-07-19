import { Routes, Route, Navigate } from "react-router-dom";
import Marketing from "./pages/Marketing";
import DemoHub from "./pages/DemoHub";
import Guide from "./pages/Guide";

export default function App() {
  return (
    <Routes>
      {/* Marketing landing */}
      <Route path="/" element={<Marketing />} />

      {/* Unified demo — Bank View (Lending + Portfolio) + Client View */}
      <Route path="/demo" element={<DemoHub />} />

      {/* Learn destination — How It Works + Benefits + AI Engine */}
      <Route path="/how-it-works" element={<Guide />} />

      {/* Legacy routes — keep old links working */}
      <Route path="/portfolio" element={<Navigate to="/demo?view=bank&section=portfolio" replace />} />
      <Route path="/benefits"  element={<Navigate to="/how-it-works?section=benefits" replace />} />
      <Route path="/ai-engine" element={<Navigate to="/how-it-works?section=ai" replace />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
