import { motion } from "framer-motion";
import { useLang } from "../i18n/LanguageContext";
import {
  Coffee, HeartPulse, TrendingUp, ShieldCheck, Wallet,
  CircleCheck, Sparkles, ArrowRight, Sun,
} from "lucide-react";

/* Client View — what an SME owner sees about their own business.
   Friendly, non-technical, warm. Static demo data (cafe). */

const COPY = {
  en: {
    greeting: "Good morning,",
    owner: "Qahwa Corner Cafe",
    sub: "Here's how your business looks today.",

    healthTitle: "Your financial health",
    healthState: "Healthy",
    healthLine: "You comfortably earn more than enough to cover your commitments.",
    healthMetric: "For every SAR 1 you owe each month, you're bringing in",
    healthValue: "SAR 2.14",
    healthFoot: "Banks look for at least SAR 1.25 — you're well above that.",

    revenueTitle: "Next month, expect around",
    revenueValue: "SAR 96,400",
    revenueRange: "likely between SAR 88K and SAR 104K",
    revenueLine: "Weekends stay your busiest — Thursday and Friday evenings bring in the most.",
    revenueTrend: "Trending up 8% vs last month",

    securityTitle: "Your account is secure",
    securityState: "All clear",
    securityLine: "We watch your day-to-day activity and haven't seen anything unusual.",
    securityPoints: [
      "No unusual transactions this month",
      "Sales patterns match your normal rhythm",
      "You'll be alerted the moment something looks off",
    ],

    financingTitle: "Financing you qualify for",
    financingLine: "Based on your real activity — no paperwork needed.",
    offers: [
      { name: "Working Capital Line", amount: "up to SAR 180,000", rate: "from 9.5%",
        note: "Grows automatically as your revenue grows.", best: true },
      { name: "Equipment Financing", amount: "up to SAR 90,000", rate: "from 8.9%",
        note: "For a new espresso machine or oven." },
      { name: "Green Upgrade Discount", amount: "−0.8% rate", rate: "if eligible",
        note: "Lower energy use earns you a cheaper rate." },
    ],
    apply: "See my offer",
    disclaimer: "This is a demo view for illustration. Figures are sample data.",
  },
  ar: {
    greeting: "صباح الخير،",
    owner: "مقهى قهوة كورنر",
    sub: "إليك حالة منشأتك اليوم.",

    healthTitle: "صحتك المالية",
    healthState: "سليمة",
    healthLine: "دخلك يغطي التزاماتك بأريحية وأكثر.",
    healthMetric: "مقابل كل ريال تدين به شهرياً، أنت تجني",
    healthValue: "٢٫١٤ ريال",
    healthFoot: "البنوك تطلب ١٫٢٥ ريال على الأقل — وأنت أعلى من ذلك بكثير.",

    revenueTitle: "الشهر القادم، توقّع نحو",
    revenueValue: "٩٦٬٤٠٠ ريال",
    revenueRange: "غالباً بين ٨٨ ألف و١٠٤ ألف ريال",
    revenueLine: "تبقى نهايات الأسبوع الأكثر ازدحاماً — مساء الخميس والجمعة الأعلى.",
    revenueTrend: "ارتفاع ٨٪ مقارنة بالشهر الماضي",

    securityTitle: "حسابك آمن",
    securityState: "كل شيء سليم",
    securityLine: "نراقب نشاطك اليومي ولم نلاحظ أي شيء غير معتاد.",
    securityPoints: [
      "لا معاملات غير معتادة هذا الشهر",
      "أنماط مبيعاتك تطابق إيقاعك الطبيعي",
      "سنبلّغك لحظة ظهور أي شيء غريب",
    ],

    financingTitle: "تمويلات أنت مؤهل لها",
    financingLine: "بناءً على نشاطك الحقيقي — بلا أوراق.",
    offers: [
      { name: "خط رأس مال عامل", amount: "حتى ١٨٠٬٠٠٠ ريال", rate: "من ٩٫٥٪",
        note: "يزيد تلقائياً مع نمو إيراداتك.", best: true },
      { name: "تمويل معدات", amount: "حتى ٩٠٬٠٠٠ ريال", rate: "من ٨٫٩٪",
        note: "لآلة إسبريسو أو فرن جديد." },
      { name: "خصم الترقية الخضراء", amount: "−٠٫٨٪ من السعر", rate: "عند الأهلية",
        note: "استهلاك طاقة أقل يمنحك سعراً أرخص." },
    ],
    apply: "اعرض عرضي",
    disclaimer: "هذه شاشة توضيحية. الأرقام بيانات تجريبية.",
  },
};

const fade = {
  hidden: { opacity: 0, y: 16 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.4, delay: i * 0.07, ease: [0.23, 1, 0.32, 1] },
  }),
};

function Card({ children, i = 0, className = "" }) {
  return (
    <motion.div
      variants={fade} custom={i} initial="hidden" whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
      className={`grad-card p-6 sm:p-7 ${className}`}
    >
      {children}
    </motion.div>
  );
}

export default function ClientView() {
  const { lang, isRTL } = useLang();
  const c = COPY[lang];

  return (
    <div className="max-w-5xl mx-auto" dir={isRTL ? "rtl" : "ltr"}>

      {/* Warm greeting header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
        className="warm-panel rounded-3xl p-6 sm:p-8 flex items-center gap-4 mb-6"
      >
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-gold to-brand-goldDark
                        flex items-center justify-center shrink-0 shadow-lg">
          <Coffee size={26} className="text-ink" />
        </div>
        <div>
          <div className="text-sm text-cream-dim flex items-center gap-1.5">
            <Sun size={14} className="text-brand-gold" />
            {c.greeting}
          </div>
          <h1 className="font-display font-bold text-xl sm:text-2xl text-cream">
            {c.owner}
          </h1>
          <div className="text-sm text-cream-dim mt-0.5">{c.sub}</div>
        </div>
      </motion.div>

      <div className="grid gap-5 md:grid-cols-2">

        {/* Financial health */}
        <Card i={0}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-sage/12 border border-sage/25
                              flex items-center justify-center">
                <HeartPulse size={19} className="text-sage" />
              </div>
              <h2 className="font-display font-semibold text-base text-cream">
                {c.healthTitle}
              </h2>
            </div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                             text-xs font-semibold text-sage bg-sage/12 border border-sage/25">
              <CircleCheck size={13} />
              {c.healthState}
            </span>
          </div>
          <p className="mt-4 text-sm text-cream-dim leading-relaxed">{c.healthLine}</p>
          <div className="mt-5 rounded-2xl bg-surface-dark/60 border border-surface-border p-4">
            <div className="text-xs text-cream-dim">{c.healthMetric}</div>
            <div className="mt-1 font-display font-bold text-3xl text-sage">
              {c.healthValue}
            </div>
          </div>
          <p className="mt-3 text-xs text-cream-dim/80">{c.healthFoot}</p>
        </Card>

        {/* Next month revenue */}
        <Card i={1}>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-brand-gold/12 border border-brand-gold/20
                            flex items-center justify-center">
              <TrendingUp size={19} className="text-brand-gold" />
            </div>
            <h2 className="font-display font-semibold text-base text-cream">
              {c.revenueTitle}
            </h2>
          </div>
          <div className="mt-4 font-display font-bold text-4xl text-cream">
            {c.revenueValue}
          </div>
          <div className="mt-1 text-xs text-cream-dim">{c.revenueRange}</div>

          {/* Weekly rhythm bars */}
          <div className="mt-5 flex items-end gap-1.5 h-20">
            {[
              { d: isRTL ? "أحد" : "Su", h: 46 },
              { d: isRTL ? "إثن" : "Mo", h: 40 },
              { d: isRTL ? "ثلا" : "Tu", h: 44 },
              { d: isRTL ? "أرب" : "We", h: 52 },
              { d: isRTL ? "خمي" : "Th", h: 84 },
              { d: isRTL ? "جمع" : "Fr", h: 96 },
              { d: isRTL ? "سبت" : "Sa", h: 70 },
            ].map((b, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full rounded-md bg-gradient-to-t from-brand-gold/25 to-brand-gold"
                     style={{ height: `${b.h}%` }} />
                <span className="text-[10px] text-cream-dim">{b.d}</span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm text-cream-dim leading-relaxed">{c.revenueLine}</p>
          <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium
                          text-sage bg-sage/10 border border-sage/20 rounded-full px-3 py-1">
            <TrendingUp size={12} />
            {c.revenueTrend}
          </div>
        </Card>

        {/* Account security */}
        <Card i={2}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-sage/12 border border-sage/25
                              flex items-center justify-center">
                <ShieldCheck size={19} className="text-sage" />
              </div>
              <h2 className="font-display font-semibold text-base text-cream">
                {c.securityTitle}
              </h2>
            </div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                             text-xs font-semibold text-sage bg-sage/12 border border-sage/25">
              <CircleCheck size={13} />
              {c.securityState}
            </span>
          </div>
          <p className="mt-4 text-sm text-cream-dim leading-relaxed">{c.securityLine}</p>
          <ul className="mt-4 space-y-2.5">
            {c.securityPoints.map((p, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-cream">
                <CircleCheck size={16} className="text-sage shrink-0 mt-0.5" />
                {p}
              </li>
            ))}
          </ul>
        </Card>

        {/* Financing options */}
        <Card i={3}>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-brand-gold/12 border border-brand-gold/20
                            flex items-center justify-center">
              <Wallet size={19} className="text-brand-gold" />
            </div>
            <div>
              <h2 className="font-display font-semibold text-base text-cream">
                {c.financingTitle}
              </h2>
              <div className="text-xs text-cream-dim mt-0.5">{c.financingLine}</div>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            {c.offers.map((o, i) => (
              <div key={i}
                className={`rounded-2xl p-4 border
                  ${o.best
                    ? "bg-brand-gold/8 border-brand-gold/35"
                    : "bg-surface-dark/60 border-surface-border"}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-display font-semibold text-sm text-cream">
                    {o.name}
                  </span>
                  {o.best && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold
                                     text-brand-gold bg-brand-gold/15 rounded-full px-2 py-0.5">
                      <Sparkles size={10} />
                      {isRTL ? "الأنسب لك" : "Best fit"}
                    </span>
                  )}
                </div>
                <div className="mt-1.5 flex items-baseline gap-2 flex-wrap">
                  <span className="font-display font-bold text-lg text-brand-gold">
                    {o.amount}
                  </span>
                  <span className="text-xs text-cream-dim">· {o.rate}</span>
                </div>
                <div className="mt-1 text-xs text-cream-dim">{o.note}</div>
              </div>
            ))}
          </div>

          <button className="cta-gold mt-5 w-full inline-flex items-center justify-center gap-2
                             px-6 py-3 text-sm">
            {c.apply}
            <ArrowRight size={16} className={isRTL ? "rotate-180" : ""} />
          </button>
        </Card>
      </div>

      <p className="mt-6 text-center text-xs text-cream-dim/60">{c.disclaimer}</p>
    </div>
  );
}
