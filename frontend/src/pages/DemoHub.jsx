import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useLang } from "../i18n/LanguageContext";
import TopNav from "../components/TopNav";
import {
  LayoutDashboard, Briefcase, GitBranch, Star, Brain,
  Building2, User,
} from "lucide-react";

import Demo from "./Demo";
import Portfolio from "./Portfolio";
import HowItWorks from "./HowItWorks";
import Benefits from "./Benefits";
import AIEngine from "./AIEngine";
import ClientView from "./ClientView";

/* Bank View sidebar sections — merge of the previously separate pages */
const SECTIONS = [
  { id: "lending",   icon: LayoutDashboard, en: "Lending Engine", ar: "محرك الإقراض", Comp: Demo },
  { id: "portfolio", icon: Briefcase,       en: "Portfolio",      ar: "المحفظة",       Comp: Portfolio },
  { id: "how",       icon: GitBranch,       en: "How It Works",   ar: "كيف يعمل",      Comp: HowItWorks },
  { id: "benefits",  icon: Star,            en: "Benefits",       ar: "الفوائد",       Comp: Benefits },
  { id: "ai",        icon: Brain,           en: "AI Engine",      ar: "محرك الذكاء",   Comp: AIEngine },
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
                            rounded-lg text-sm font-medium
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
              className="flex flex-col lg:flex-row gap-6"
            >
              {/* Desktop sidebar */}
              <aside className="hidden lg:block w-56 shrink-0">
                <nav className="sticky top-24 space-y-1">
                  {SECTIONS.map(s => (
                    <button
                      key={s.id}
                      onClick={() => chooseSection(s.id)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl
                                  text-sm font-medium text-start
                                  ${section === s.id
                                    ? "bg-brand-gold/10 text-brand-gold border border-brand-gold/25"
                                    : "text-gray-400 hover:text-cream hover:bg-white/5 border border-transparent"}`}
                      style={{ transition: "color 150ms var(--ease-out), background-color 150ms var(--ease-out)" }}
                    >
                      <s.icon size={17} className="shrink-0" />
                      {lang === "ar" ? s.ar : s.en}
                    </button>
                  ))}
                </nav>
              </aside>

              {/* Mobile / tablet section chips */}
              <div className="lg:hidden -mx-4 px-4 overflow-x-auto">
                <div className="flex gap-2 pb-1 w-max">
                  {SECTIONS.map(s => (
                    <button
                      key={s.id}
                      onClick={() => chooseSection(s.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg
                                  text-sm font-medium whitespace-nowrap
                                  ${section === s.id
                                    ? "bg-brand-gold/10 text-brand-gold border border-brand-gold/25"
                                    : "text-gray-400 border border-surface-border"}`}
                    >
                      <s.icon size={15} />
                      {lang === "ar" ? s.ar : s.en}
                    </button>
                  ))}
                </div>
              </div>

              {/* Section content */}
              <div className="flex-1 min-w-0">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={section}
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
                  >
                    <ActiveComp />
                  </motion.div>
                </AnimatePresence>
              </div>
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
