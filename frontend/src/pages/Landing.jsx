import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLang } from "../i18n/LanguageContext";
import { getBusinesses } from "../services/api";
import {
  Zap, TrendingUp, Leaf, Shield,
  ArrowRight, ArrowLeft, Building2,
  Sprout, Activity
} from "lucide-react";

export default function Landing() {
  const { t, isRTL } = useLang();
  const navigate = useNavigate();
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  const [stats, setStats] = useState({
    businesses: 6,
    avgLimit: "1.5M",
    avgDscr: "2.1"
  });

  useEffect(() => {
    getBusinesses()
      .then(res => {
        const count = res.data.businesses?.length || 6;
        setStats(s => ({ ...s, businesses: count }));
      })
      .catch(() => {});
  }, []);

  const features = [
    {
      icon: Zap,
      color: "text-brand-gold",
      bg: "bg-brand-gold/10",
      title: t.featureRealTime,
      desc: t.featureRealTimeDesc,
    },
    {
      icon: TrendingUp,
      color: "text-status-green",
      bg: "bg-status-green/10",
      title: t.featureDynamic,
      desc: t.featureDynamicDesc,
    },
    {
      icon: Leaf,
      color: "text-emerald-400",
      bg: "bg-emerald-400/10",
      title: t.featureGreen,
      desc: t.featureGreenDesc,
    },
    {
      icon: Shield,
      color: "text-status-blue",
      bg: "bg-status-blue/10",
      title: t.featureFraud,
      desc: t.featureFraudDesc,
    },
  ];

  const titleWords = t.landingTitle.split(" ");
  const titleMain = titleWords.slice(0, -2).join(" ");
  const titleGold = titleWords.slice(-2).join(" ");

  return (
    <div className="space-y-16 py-8">

      {/* ── HERO ─────────────────────────────────────────────── */}
      <section className="text-center space-y-6 pt-8">

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5
                        rounded-full border border-brand-gold/30
                        bg-brand-gold/10 text-brand-gold text-sm font-medium">
          <Activity size={14} />
          {t.appTagline}
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-6xl font-bold text-white
                       leading-tight max-w-3xl mx-auto">
          {titleMain}{" "}
          <span className="text-gold-gradient">{titleGold}</span>
        </h1>

        {/* Subtext */}
        <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
          {t.landingSubtitle}
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center justify-center gap-2
                       bg-brand-gold hover:bg-brand-goldLight
                       text-brand-blueDark font-semibold
                       px-8 py-3 rounded-xl transition-all
                       hover:scale-105 active:scale-95"
          >
            {t.connectData}
            <Arrow size={18} />
          </button>
          <button
            onClick={() => navigate("/incubator")}
            className="flex items-center justify-center gap-2
                       border border-surface-border
                       text-gray-300 hover:text-white
                       hover:border-brand-gold/50
                       px-8 py-3 rounded-xl transition-all"
          >
            {t.learnMore}
          </button>
        </div>
      </section>

      {/* ── STATS BAR ────────────────────────────────────────── */}
      <section className="glass-card rounded-xl p-6">
        <div className="grid grid-cols-3 divide-x divide-surface-border">
          {[
            {
              value: stats.businesses,
              label: isRTL ? "منشأة متصلة" : "Businesses Connected",
              color: "text-brand-gold",
            },
            {
              value: "SAR 1.5M",
              label: isRTL ? "متوسط الحد الائتماني" : "Avg Credit Limit",
              color: "text-status-green",
            },
            {
              value: "2.1x",
              label: isRTL ? "متوسط معدل تغطية الدين" : "Avg DSCR Score",
              color: "text-status-blue",
            },
          ].map((stat, i) => (
            <div key={i} className="text-center px-4">
              <div className={`text-3xl font-bold ${stat.color}`}>
                {stat.value}
              </div>
              <div className="text-gray-400 text-sm mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURE CARDS ────────────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white text-center">
          {isRTL ? "لماذا DataCore؟" : "Why DataCore?"}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map(({ icon: Icon, color, bg, title, desc }) => (
            <div
              key={title}
              className="glass-card rounded-xl p-5 space-y-3
                         hover:border-brand-gold/30 transition-all
                         hover:-translate-y-1 cursor-default"
            >
              <div className={`w-10 h-10 rounded-lg ${bg}
                              flex items-center justify-center`}>
                <Icon size={20} className={color} />
              </div>
              <h3 className="font-semibold text-white text-sm">{title}</h3>
              <p className="text-gray-400 text-xs leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PIPELINE VISUAL ──────────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white text-center">
          {isRTL ? "مسارات الإقراض" : "Two Lending Pipelines"}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* SME Pipeline */}
          <div className="glass-card rounded-xl p-6 space-y-4
                          border border-brand-blue/40
                          hover:border-brand-blue/70 transition-all">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-brand-blue/20
                              flex items-center justify-center shrink-0">
                <Building2 size={20} className="text-brand-blueLight" />
              </div>
              <div>
                <div className="font-semibold text-white text-sm">
                  {isRTL ? "مسار المنشآت القائمة" : "Existing SME Pipeline"}
                </div>
                <div className="text-xs text-gray-400">
                  {isRTL ? "للمنشآت ذات البيانات الحية" : "For businesses with live data"}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              {(isRTL
                ? ["ربط بيانات نقاط البيع", "تحليل التدفق النقدي بالذكاء الاصطناعي", "حساب DSCR ديناميكي", "حد ائتماني فوري"]
                : ["Connect POS Data", "AI Cash Flow Analysis", "Dynamic DSCR Calculation", "Instant Credit Limit"]
              ).map((step, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-gray-300">
                  <div className="w-5 h-5 rounded-full bg-brand-blue/30
                                  flex items-center justify-center
                                  text-brand-gold text-xs font-bold shrink-0">
                    {i + 1}
                  </div>
                  {step}
                </div>
              ))}
            </div>

            <button
              onClick={() => navigate("/dashboard")}
              className="w-full flex items-center justify-center gap-2
                         bg-brand-blue hover:bg-brand-blueLight
                         text-white text-sm font-medium
                         py-2.5 rounded-lg transition-all"
            >
              {isRTL ? "عرض اللوحة" : "View Dashboard"}
              <Arrow size={15} />
            </button>
          </div>

          {/* Incubator Pipeline */}
          <div className="glass-card rounded-xl p-6 space-y-4
                          border border-brand-gold/20
                          hover:border-brand-gold/50 transition-all">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-brand-gold/10
                              flex items-center justify-center shrink-0">
                <Sprout size={20} className="text-brand-gold" />
              </div>
              <div>
                <div className="font-semibold text-white text-sm">
                  {isRTL ? "مسار الحاضنة" : "Incubator Pipeline"}
                </div>
                <div className="text-xs text-gray-400">
                  {isRTL ? "لرواد الأعمال الجدد" : "For new entrepreneurs"}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              {(isRTL
                ? ["ربط حساب الراتب", "تقييم نسبة عبء الدين", "قرض أولي مضمون بالراتب", "الانتقال إلى مسار المنشآت"]
                : ["Connect Salary Account", "DBR Assessment", "Salary-Backed Seed Loan", "Graduate to SME Pipeline"]
              ).map((step, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-gray-300">
                  <div className="w-5 h-5 rounded-full bg-brand-gold/20
                                  flex items-center justify-center
                                  text-brand-gold text-xs font-bold shrink-0">
                    {i + 1}
                  </div>
                  {step}
                </div>
              ))}
            </div>

            <button
              onClick={() => navigate("/incubator")}
              className="w-full flex items-center justify-center gap-2
                         bg-brand-gold hover:bg-brand-goldLight
                         text-brand-blueDark text-sm font-medium
                         py-2.5 rounded-lg transition-all"
            >
              {isRTL ? "استكشف الحاضنة" : "Explore Incubator"}
              <Arrow size={15} />
            </button>
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ────────────────────────────────────────── */}
      <section className="glass-card rounded-xl p-8 text-center
                          border border-brand-gold/20 space-y-4">
        <h2 className="text-2xl font-bold text-white">
          {isRTL
            ? "جاهز لتحويل بيانات منشأتك إلى قرار ائتماني؟"
            : "Ready to turn your business data into a credit decision?"}
        </h2>
        <p className="text-gray-400 text-sm max-w-xl mx-auto">
          {isRTL
            ? "انضم إلى المنشآت التي تستخدم DataCore للحصول على تمويل فوري وذكي."
            : "Join businesses using DataCore for instant, intelligent financing."}
        </p>
        <button
          onClick={() => navigate("/dashboard")}
          className="inline-flex items-center gap-2
                     bg-brand-gold hover:bg-brand-goldLight
                     text-brand-blueDark font-semibold
                     px-10 py-3 rounded-xl transition-all
                     hover:scale-105 active:scale-95"
        >
          {t.connectData}
          <Arrow size={18} />
        </button>
      </section>

    </div>
  );
}
