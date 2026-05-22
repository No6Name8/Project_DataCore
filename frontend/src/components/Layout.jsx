import { Outlet, NavLink } from "react-router-dom";
import { useLang } from "../i18n/LanguageContext";
import { LayoutDashboard, GitBranch, Star, Brain, Globe } from "lucide-react";

export default function Layout() {
  const { t, lang, toggleLang } = useLang();

  const navItems = [
    { to: "/demo",         icon: LayoutDashboard, labelEn: "Demo",         labelAr: "العرض" },
    { to: "/how-it-works", icon: GitBranch,        labelEn: "How It Works", labelAr: "كيف يعمل" },
    { to: "/benefits",     icon: Star,             labelEn: "Benefits",     labelAr: "الفوائد" },
    { to: "/ai-engine",    icon: Brain,            labelEn: "AI Engine",    labelAr: "محرك الذكاء" },
  ];

  const mobileItems = [
    { to: "/demo",         icon: LayoutDashboard, labelEn: "Demo",     labelAr: "العرض" },
    { to: "/how-it-works", icon: GitBranch,        labelEn: "How It",   labelAr: "كيف" },
    { to: "/benefits",     icon: Star,             labelEn: "Benefits", labelAr: "الفوائد" },
    { to: "/ai-engine",    icon: Brain,            labelEn: "AI",       labelAr: "الذكاء" },
  ];

  const activeClass =
    "bg-brand-blue/20 text-white border-b-2 border-brand-gold";
  const inactiveClass =
    "text-gray-400 hover:text-white hover:bg-surface-hover";

  return (
    <div className="min-h-screen flex flex-col bg-surface-dark">

      {/* Top navbar */}
      <header className="sticky top-0 z-50 glass-card border-b border-surface-border">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

          {/* Logo */}
          <NavLink to="/demo" className="flex items-center gap-3 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-brand-gold flex items-center
                            justify-center text-brand-blueDark font-bold text-sm shrink-0">
              DC
            </div>
            <div className="hidden sm:block">
              <div className="font-bold text-white text-sm leading-none">
                {t.appName}
              </div>
              <div className="text-[10px] text-brand-gold leading-none mt-0.5 whitespace-nowrap">
                {t.poweredBy}
              </div>
            </div>
          </NavLink>

          {/* Nav links */}
          <nav className="flex items-center gap-1">
            {navItems.map(({ to, icon: Icon, labelEn, labelAr }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm
                   font-medium
                   ${isActive ? activeClass : inactiveClass}`
                }
              >
                <Icon size={16} className="shrink-0" />
                <span className="hidden sm:inline">
                  {lang === "ar" ? labelAr : labelEn}
                </span>
              </NavLink>
            ))}
          </nav>

          {/* Language toggle */}
          <button
            onClick={toggleLang}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg shrink-0
                       border border-surface-border text-gray-400
                       hover:text-brand-gold hover:border-brand-gold
                       text-sm font-medium"
            style={{ transition: "color 150ms var(--ease-out), border-color 150ms var(--ease-out)" }}
          >
            <Globe size={15} />
            <span>{lang === "en" ? "العربية" : "English"}</span>
          </button>

        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-6 pb-20 md:pb-6">
        <div className="page-enter">
          <Outlet />
        </div>
      </main>

      {/* Footer — hidden on mobile (bottom nav takes over) */}
      <footer className="hidden md:block border-t border-surface-border py-4
                          text-center text-xs text-gray-600">
        DataCore © 2025 — Alinma iz Business Hackathon
      </footer>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-50
                      glass-card border-t border-surface-border
                      flex items-center justify-around h-16 px-4">
        {mobileItems.map(({ to, icon: Icon, labelEn, labelAr }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 text-xs font-medium
               ${isActive ? "text-brand-gold" : "text-gray-500"}`
            }
          >
            <Icon size={20} />
            <span>{lang === "ar" ? labelAr : labelEn}</span>
          </NavLink>
        ))}
      </nav>

    </div>
  );
}
