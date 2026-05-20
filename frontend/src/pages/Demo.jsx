import Dashboard from "./Dashboard";
import Incubator from "./Incubator";
import { useLang } from "../i18n/LanguageContext";
import { Activity } from "lucide-react";

export default function Demo() {
  const { isRTL } = useLang();

  return (
    <div className="space-y-12">

      {/* Brief hero strip */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {isRTL ? "محرك الإقراض الذكي" : "AI Lending Engine"}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {isRTL
              ? "بيانات حية · تقييم فوري · حد ائتماني ديناميكي"
              : "Live data · Instant assessment · Dynamic credit limits"}
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full
                        border border-status-green/30 bg-status-green/10">
          <div className="w-2 h-2 rounded-full bg-status-green animate-pulse" />
          <span className="text-status-green text-xs font-medium">
            {isRTL ? "مباشر" : "Live"}
          </span>
        </div>
      </div>

      {/* SME Dashboard section */}
      <section id="sme-dashboard">
        <Dashboard />
      </section>

      {/* Section divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-surface-border" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-4 bg-surface-dark text-xs text-gray-500 uppercase
                           tracking-widest">
            {isRTL ? "مسار الحاضنة" : "Incubator Pipeline"}
          </span>
        </div>
      </div>

      {/* Incubator section */}
      <section id="incubator">
        <Incubator />
      </section>

    </div>
  );
}
