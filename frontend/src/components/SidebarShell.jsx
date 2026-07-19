import { motion, AnimatePresence } from "framer-motion";
import { useLang } from "../i18n/LanguageContext";

/*
 * Shared dashboard sidebar layout.
 *  - Desktop: sticky left rail with an animated gold active pill.
 *  - Mobile/tablet: horizontal scrolling chips.
 *  - Content transitions smoothly when `active` changes.
 *
 * props:
 *   sections  [{ id, icon, en, ar }]
 *   active     current section id
 *   onSelect   (id) => void
 *   layoutId   unique id for the active-pill layout animation
 *   children   the active section's content
 */
export default function SidebarShell({ sections, active, onSelect, layoutId = "railPill", children }) {
  const { lang } = useLang();
  const label = (s) => (lang === "ar" ? s.ar : s.en);

  return (
    <div className="flex flex-col lg:flex-row gap-6">

      {/* Desktop rail */}
      <aside className="hidden lg:block w-56 shrink-0">
        <nav className="sticky top-24 space-y-1.5">
          {sections.map((s) => {
            const isActive = active === s.id;
            return (
              <button
                key={s.id}
                onClick={() => onSelect(s.id)}
                aria-current={isActive ? "page" : undefined}
                className={`relative w-full flex items-center gap-3 px-4 py-3 rounded-xl
                            text-sm font-medium text-start cursor-pointer
                            ${isActive
                              ? "text-brand-gold"
                              : "text-gray-400 hover:text-cream hover:bg-white/[0.04]"}`}
                style={{ transition: "color 160ms var(--ease-out), background-color 160ms var(--ease-out)" }}
              >
                {isActive && (
                  <motion.span
                    layoutId={layoutId}
                    className="absolute inset-0 rounded-xl bg-brand-gold/10
                               border border-brand-gold/30"
                    style={{ zIndex: 0 }}
                    transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
                  />
                )}
                <s.icon size={18} className="relative z-10 shrink-0" />
                <span className="relative z-10">{label(s)}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Mobile / tablet chips */}
      <div className="lg:hidden -mx-4 px-4 overflow-x-auto">
        <div className="flex gap-2 pb-1 w-max">
          {sections.map((s) => {
            const isActive = active === s.id;
            return (
              <button
                key={s.id}
                onClick={() => onSelect(s.id)}
                aria-current={isActive ? "page" : undefined}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg
                            text-sm font-medium whitespace-nowrap cursor-pointer
                            ${isActive
                              ? "bg-brand-gold/10 text-brand-gold border border-brand-gold/30"
                              : "text-gray-400 border border-surface-border"}`}
                style={{ transition: "color 160ms var(--ease-out)" }}
              >
                <s.icon size={15} />
                {label(s)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
