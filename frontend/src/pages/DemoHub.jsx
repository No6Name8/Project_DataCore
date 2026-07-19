import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useLang } from "../i18n/LanguageContext";
import TopNav from "../components/TopNav";
import SidebarShell from "../components/SidebarShell";
import { LayoutDashboard, Briefcase, Building2, User } from "lucide-react";

import Demo from "./Demo";
import Portfolio from "./Portfolio";
import ClientView from "./ClientView";

/* Bank View sidebar — the working lending dashboard only */
const SECTIONS = [
  { id: "lending",   icon: LayoutDashboard, en: "Lending Engine", ar: "محرك الإقراض", Comp: Demo },
  { id: "portfolio", icon: Briefcase,       en: "Portfolio",      ar: "المحفظة",       Comp: Portfolio },
];

export default function DemoHub() {
  const { lang, isRTL } = useLang();
  const [params, setParams] = useSearchParams();

  const businessParam = params.get("business");
  const initialView = params.get("view") === "client" ? "client" : "bank";
  // A ?business= deep-link (from the portfolio table) always lands on Lending.
  const initialSection = businessParam
    ? "lending"
    : (SECTIONS.some(s => s.id === params.get("section")) ? params.get("section") : "lending");

  const [view, setView] = useState(initialView);
  const [section, setSection] = useState(initialSection);

  // When a business deep-link arrives, jump to Bank → Lending.
  useEffect(() => {
    if (businessParam) { setView("bank"); setSection("lending"); }
  }, [businessParam]);

  // Keep the URL in sync so views are shareable / back-navigable.
  const syncParams = (nextView, nextSection) => {
    const next = new URLSearchParams(params);
    next.set("view", nextView);
    if (nextView === "bank") next.set("section", nextSection);
    else next.delete("section");
    // Dropping a stale business filter when leaving lending keeps state clean.
    if (!(nextView === "bank" && nextSection === "lending")) next.delete("business");
    setParams(next, { replace: true });
  };

  const chooseView = (v) => { setView(v); syncParams(v, section); };
  const chooseSection = (s) => { setSection(s); syncParams("bank", s); };

  const ActiveComp = useMemo(
    () => SECTIONS.find(s => s.id === section)?.Comp || Demo,
    [section]
  );

  return (
    <div className="min-h-dvh bg-surface-dark" dir={isRTL ? "rtl" : "ltr"}>
      <TopNav />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">

        {/* Bank / Client segmented toggle */}
        <div className="flex justify-center sm:justify-start mb-6">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-surface-card
                          border border-surface-border">
            {[
              { id: "bank",   icon: Building2, en: "Bank View",   ar: "عرض البنك" },
              { id: "client", icon: User,     en: "Client View", ar: "عرض العميل" },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => chooseView(tab.id)}
                className={`relative flex items-center gap-2 px-5 sm:px-6 py-2.5
                            rounded-lg text-sm font-medium cursor-pointer
                            ${view === tab.id ? "text-cream" : "text-gray-400 hover:text-cream"}`}
                style={{ transition: "color 150ms var(--ease-out)" }}
              >
                {view === tab.id && (
                  <motion.div
                    layoutId="viewPill"
                    className="absolute inset-0 rounded-lg bg-brand-blue"
                    style={{ zIndex: -1 }}
                    transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
                  />
                )}
                <tab.icon size={16} />
                {lang === "ar" ? tab.ar : tab.en}
              </button>
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          {view === "bank" ? (
            <motion.div
              key="bank"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            >
              <SidebarShell
                sections={SECTIONS}
                active={section}
                onSelect={chooseSection}
                layoutId="bankRailPill"
              >
                <ActiveComp />
              </SidebarShell>
            </motion.div>
          ) : (
            <motion.div
              key="client"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            >
              <ClientView />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
