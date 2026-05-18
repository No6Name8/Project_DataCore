import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Incubator from "./pages/Incubator";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Landing />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="incubator" element={<Incubator />} />
      </Route>
    </Routes>
  );
}
