import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { useLang } from "../i18n/LanguageContext";
import TopNav from "../components/TopNav";
import SidebarShell from "../components/SidebarShell";
import { GitBranch, Star, Brain } from "lucide-react";

import HowItWorks from "./HowItWorks";
import Benefits from "./Benefits";
import AIEngine from "./AIEngine";

/* Learn destination — the narrative pages relocated out of the demo dashboard */
const SECTIONS = [
  { id: "how",      icon: GitBranch, en: "How It Works", ar: "كيف يعمل",    Comp: HowItWorks },
  { id: "benefits", icon: Star,      en: "Benefits",     ar: "الفوائد",      Comp: Benefits },
  { id: "ai",       icon: Brain,     en: "AI Engine",    ar: "محرك الذكاء",  Comp: AIEngine },
];

export default function Guide() {
  const { lang, isRTL } = useLang();
  const [params, setParams] = useSearchParams();

  const initialSection = SECTIONS.some(s => s.id === params.get("section"))
    ? params.get("section")
    : "how";
  const [section, setSection] = useState(initialSection);

  const chooseSection = (s) => {
    setSection(s);
    const next = new URLSearchParams(params);
    next.set("section", s);
    setParams(next, { replace: true });
  };

  const ActiveComp = useMemo(
    () => SECTIONS.find(s => s.id === section)?.Comp || HowItWorks,
    [section]
  );

  return (
    <div className="min-h-dvh bg-surface-dark" dir={isRTL ? "rtl" : "ltr"}>
      <TopNav />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">

        {/* Cohesive page header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
          className="mb-6"
        >
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                           text-xs font-medium tracking-wide uppercase
                           text-brand-gold bg-brand-gold/10 border border-brand-gold/20">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-gold" />
            {lang === "ar" ? "تعرّف على DataCore" : "Understand DataCore"}
          </span>
          <h1 className="mt-3 font-display font-bold text-2xl sm:text-3xl text-cream">
            {lang === "ar" ? "كيف يعمل" : "How It Works"}
          </h1>
          <p className="mt-1.5 text-sm text-cream-dim max-w-2xl">
            {lang === "ar"
              ? "الطريقة، والفوائد، والمحرك الذكي وراء كل قرار إقراض."
              : "The method, the benefits, and the AI engine behind every lending decision."}
          </p>
        </motion.div>

        <SidebarShell
          sections={SECTIONS}
          active={section}
          onSelect={chooseSection}
          layoutId="guideRailPill"
        >
          <ActiveComp />
        </SidebarShell>
      </div>
    </div>
  );
}
