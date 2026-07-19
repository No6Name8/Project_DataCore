import { useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useLang } from "../i18n/LanguageContext";
import { Globe, Menu, X } from "lucide-react";

/* DataCore mark — reused from the original Layout logo */
export function DataCoreMark({ size = 34 }) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} fill="none"
         xmlns="http://www.w3.org/2000/svg" className="shrink-0">
      <path
        d="M14 10 L14 54 L34 54 C48 54 56 44 56 32 C56 20 48 10 34 10 Z"
        stroke="#C9A84C" strokeWidth="8" strokeLinejoin="round"
        strokeLinecap="round" fill="none" />
      <circle cx="36" cy="32" r="5" fill="#8FB996" />
    </svg>
  );
}

export default function TopNav() {
  const { lang, isRTL, toggleLang } = useLang();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const links = [
    { to: "/",     labelEn: "Home",    labelAr: "الرئيسية" },
    { to: "/demo", labelEn: "Demo",    labelAr: "العرض" },
  ];

  // Contact lives as an anchor on the marketing page.
  const goContact = (e) => {
    e.preventDefault();
    setOpen(false);
    if (location.pathname === "/") {
      document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" });
    } else {
      navigate("/#contact");
    }
  };

  const linkBase =
    "px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150";

  return (
    <header className="sticky top-0 z-50 border-b border-white/5
                       bg-surface-dark/80 backdrop-blur-xl">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 h-16
                      flex items-center justify-between gap-4">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group">
          <DataCoreMark />
          <span className="font-display font-bold text-cream text-base tracking-tight">
            DataCore
          </span>
        </Link>

        {/* Center links — desktop */}
        <nav className="hidden md:flex items-center gap-1">
          {links.map(({ to, labelEn, labelAr }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `${linkBase} ${isActive
                  ? "text-cream bg-white/5"
                  : "text-cream-dim hover:text-cream hover:bg-white/5"}`}
            >
              {lang === "ar" ? labelAr : labelEn}
            </NavLink>
          ))}
          <a href="/#contact" onClick={goContact}
             className={`${linkBase} text-cream-dim hover:text-cream hover:bg-white/5`}>
            {lang === "ar" ? "تواصل معنا" : "Contact"}
          </a>
        </nav>

        {/* Right controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleLang}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg shrink-0
                       border border-white/10 text-cream-dim
                       hover:text-brand-gold hover:border-brand-gold/50
                       text-sm font-medium transition-colors duration-150"
          >
            <Globe size={15} />
            <span>{lang === "en" ? "العربية" : "English"}</span>
          </button>

          {/* Mobile menu toggle */}
          <button
            onClick={() => setOpen(o => !o)}
            className="md:hidden p-2 rounded-lg border border-white/10 text-cream"
            aria-label="Menu"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className="md:hidden border-t border-white/5 bg-surface-dark/95 backdrop-blur-xl">
          <nav className="max-w-7xl mx-auto px-4 py-3 flex flex-col gap-1"
               dir={isRTL ? "rtl" : "ltr"}>
            {links.map(({ to, labelEn, labelAr }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `${linkBase} ${isActive
                    ? "text-cream bg-white/5"
                    : "text-cream-dim hover:text-cream"}`}
              >
                {lang === "ar" ? labelAr : labelEn}
              </NavLink>
            ))}
            <a href="/#contact" onClick={goContact}
               className={`${linkBase} text-cream-dim hover:text-cream`}>
              {lang === "ar" ? "تواصل معنا" : "Contact"}
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
