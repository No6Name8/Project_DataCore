import { createContext, useContext, useState, useEffect } from "react";
import translations from "./translations";

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState("en");
  const t = translations[lang];
  const isRTL = lang === "ar";

  useEffect(() => {
    document.documentElement.dir = isRTL ? "rtl" : "ltr";
    document.documentElement.lang = lang;
  }, [lang, isRTL]);

  const toggleLang = () => setLang(prev => prev === "en" ? "ar" : "en");

  return (
    <LanguageContext.Provider value={{ lang, t, isRTL, toggleLang }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLang = () => useContext(LanguageContext);
