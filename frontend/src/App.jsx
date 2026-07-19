import { Routes, Route, Navigate } from "react-router-dom";
import Marketing from "./pages/Marketing";
import DemoHub from "./pages/DemoHub";

export default function App() {
  return (
    <Routes>
      {/* Marketing landing */}
      <Route path="/" element={<Marketing />} />

      {/* Unified demo — Bank View + Client View */}
      <Route path="/demo" element={<DemoHub />} />

      {/* Legacy routes now live as Bank View sections — keep old links working */}
      <Route path="/portfolio"    element={<Navigate to="/demo?view=bank&section=portfolio" replace />} />
      <Route path="/how-it-works" element={<Navigate to="/demo?view=bank&section=how" replace />} />
      <Route path="/benefits"     element={<Navigate to="/demo?view=bank&section=benefits" replace />} />
      <Route path="/ai-engine"    element={<Navigate to="/demo?view=bank&section=ai" replace />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
