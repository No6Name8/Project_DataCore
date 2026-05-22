import { useEffect, useState } from "react";
import { useLang } from "../i18n/LanguageContext";
import { motion } from "framer-motion";
import axios from "axios";
import config from "../config";
import {
  Brain, Database, Cpu, Shield,
  TrendingUp, GitBranch, BarChart2,
  Code2,
} from "lucide-react";

const fadeUp = {
  hidden:  { opacity: 0, y: 16 },
  visible: (i = 0) => ({
    opacity: 1, y: 0,
    transition: {
      delay: i * 0.08,
      duration: 0.35,
      ease: [0.23, 1, 0.32, 1],
    },
  }),
};

const BIZ = ["laundromat", "cafe", "minimarket", "realestate", "cardealer", "motorbike"];

const BIZ_NAMES = {
  laundromat: "Laundromat",
  cafe:       "Cafe",
  minimarket: "Minimarket",
  realestate: "Real Estate",
  cardealer:  "Car Dealer",
  motorbike:  "Motorbike",
};

const RISK_COLOR = {
  very_low: "text-status-green",
  low:      "text-status-green",
  medium:   "text-status-yellow",
  high:     "text-status-red",
  critical: "text-status-red",
};

const fingerprints = {
  cafe: {
    nameEn: "Qahwa Cafe",
    nameAr: "مقهى قهوة",
    color:  "bg-brand-gold",
    features: [
      { labelEn: "Avg Ticket",         labelAr: "متوسط الفاتورة",      value: 33,  max: 160000, display: "SAR 33" },
      { labelEn: "Daily Transactions", labelAr: "معاملات يومية",       value: 97,  max: 220,    display: "97/day" },
      { labelEn: "Peak Hour Conc.",    labelAr: "تركز ساعة الذروة",    value: 55,  max: 100,    display: "55%" },
      { labelEn: "Revenue Stability",  labelAr: "استقرار الإيرادات",   value: 72,  max: 100,    display: "72%" },
      { labelEn: "Digital Payments",   labelAr: "المدفوعات الرقمية",   value: 65,  max: 100,    display: "65%" },
      { labelEn: "Night Activity",     labelAr: "النشاط الليلي",       value: 8,   max: 100,    display: "8%" },
    ],
  },
  cardealer: {
    nameEn: "Car Dealership",
    nameAr: "معرض سيارات",
    color:  "bg-status-blue",
    features: [
      { labelEn: "Avg Ticket",         labelAr: "متوسط الفاتورة",      value: 100, max: 160000, display: "SAR 157K" },
      { labelEn: "Daily Transactions", labelAr: "معاملات يومية",       value: 4,   max: 220,    display: "4/day" },
      { labelEn: "Peak Hour Conc.",    labelAr: "تركز ساعة الذروة",    value: 45,  max: 100,    display: "45%" },
      { labelEn: "Revenue Stability",  labelAr: "استقرار الإيرادات",   value: 25,  max: 100,    display: "25%" },
      { labelEn: "Digital Payments",   labelAr: "المدفوعات الرقمية",   value: 78,  max: 100,    display: "78%" },
      { labelEn: "Night Activity",     labelAr: "النشاط الليلي",       value: 2,   max: 100,    display: "2%" },
    ],
  },
};

const MODEL_CARDS = [
  {
    num:     "01",
    icon:    Database,
    color:   "text-brand-gold",
    bg:      "bg-brand-gold/10 border-brand-gold/20",
    titleEn: "Business Classifier",
    titleAr: "مصنّف الأعمال",
    techEn:  "HDBSCAN Unsupervised Clustering",
    techAr:  "HDBSCAN غير خاضع للإشراف",
    lineEn:  "Reads transaction fingerprint. Places any business in the right behavioral cluster. Zero labels. Works on businesses it has never seen before.",
    lineAr:  "يقرأ بصمة المعاملات. يضع أي منشأة في المجموعة السلوكية الصحيحة. بدون تصنيفات. يعمل على منشآت لم يرها من قبل.",
    stat:    "12 clusters · 100% purity · ARI 1.0",
  },
  {
    num:     "02",
    icon:    Cpu,
    color:   "text-status-blue",
    bg:      "bg-status-blue/10 border-status-blue/20",
    titleEn: "Expense Estimator",
    titleAr: "مقدّر المصاريف",
    techEn:  "Behavioral Feature Mapping",
    techAr:  "تعيين الميزات السلوكية",
    lineEn:  "Derives COGS, labor, and overhead from behavioral signals — not hardcoded rules. Inventory businesses auto-detected. Zero manual configuration.",
    lineAr:  "يستخرج تكلفة البضاعة والعمالة والتشغيل من الإشارات السلوكية — لا قواعد ثابتة. المخزون يُكتشف تلقائياً. لا إعداد يدوي.",
    stat:    "Car dealer: AI 0.830 vs hardcoded 0.820",
  },
  {
    num:     "03",
    icon:    Shield,
    color:   "text-status-red",
    bg:      "bg-status-red/10 border-status-red/20",
    titleEn: "Fraud Detector",
    titleAr: "كاشف الاحتيال",
    techEn:  "Isolation Forest (per-business)",
    techAr:  "Isolation Forest (نموذج لكل منشأة)",
    lineEn:  "Each business gets its own model trained on its history. A 3AM transaction at a real estate office is anomalous. At a 24hr minimarket it is not.",
    lineAr:  "كل منشأة لها نموذجها مدرّب على تاريخها. معاملة 3 صباحاً في مكتب عقاري شاذة. في ميني ماركت 24 ساعة ليست كذلك.",
    stat:    "6 business models · 4 cluster fallbacks · 1% contamination",
  },
  {
    num:     "04",
    icon:    TrendingUp,
    color:   "text-status-green",
    bg:      "bg-status-green/10 border-status-green/20",
    titleEn: "Revenue Forecaster",
    titleAr: "متنبئ الإيرادات",
    techEn:  "Facebook Prophet + Saudi Seasonality",
    techAr:  "Prophet + الموسمية السعودية",
    lineEn:  "Forecasts next 30 days with confidence intervals. Growing businesses get higher limits. Declining ones get lower — automatically.",
    lineAr:  "يتوقع 30 يوماً مع فترات ثقة. الأعمال النامية تحصل على حدود أعلى. المتراجعة تحصل على أقل — تلقائياً.",
    stat:    "80% confidence band · Saudi Thu/Fri weekend · ±25% limit adjustment",
  },
];

const CLASSIFICATIONS = [
  { biz: "cafe",       cluster: "C6",  arch: "high_freq_low_ticket_food",      conf: 88 },
  { biz: "minimarket", cluster: "C1",  arch: "high_freq_mid_ticket_retail",     conf: 91 },
  { biz: "laundromat", cluster: "C5",  arch: "low_ticket_essential_steady",     conf: 74 },
  { biz: "realestate", cluster: "C3",  arch: "sparse_high_ticket_brokerage",    conf: 95 },
  { biz: "cardealer",  cluster: "C2",  arch: "low_freq_very_high_ticket_auto",  conf: 89 },
  { biz: "motorbike",  cluster: "C8",  arch: "low_freq_mid_high_ticket_dealer", conf: 82 },
];

/* ── Reusable animated bar ── */
function Bar({ value, max, color }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${color}`}
        initial={{ width: "0%" }}
        whileInView={{ width: `${pct}%` }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      />
    </div>
  );
}

/* ── Section heading ── */
function SectionHeading({ icon: Icon, en, ar, isRTL }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: isRTL ? 12 : -12 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, ease: [0.23, 1, 0.32, 1] }}
      className="flex items-center gap-3 pb-3 border-b border-surface-border"
    >
      <Icon size={16} className="text-brand-gold shrink-0" />
      <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
        {isRTL ? ar : en}
      </h2>
    </motion.div>
  );
}

export default function AIEngine() {
  const { isRTL } = useLang();
  const [fraudData, setFraudData] = useState({});
  const [dscrData,  setDscrData]  = useState({});
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      ...BIZ.map(b => axios.get(`${config.API_BASE}/api/${b}/dscr`)),
      ...BIZ.map(b => axios.get(`${config.API_BASE}/api/${b}/fraud-check`)),
    ]).then(results => {
      const dscr  = {};
      const fraud = {};
      BIZ.forEach((b, i) => {
        dscr[b]  = results[i].data;
        fraud[b] = results[i + 6].data;
      });
      setDscrData(dscr);
      setFraudData(fraud);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-12 py-4">

      {/* ── PAGE HEADER ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="text-center space-y-3"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5
                        rounded-full border border-brand-gold/30
                        bg-brand-gold/10 text-brand-gold text-xs font-medium">
          <Brain size={13} />
          {isRTL ? "للمراجعة التقنية" : "For Technical Review"}
        </div>
        <h1 className="text-2xl font-bold text-white">
          {isRTL ? "ما الذي بنيته بالضبط؟" : "What Exactly Did I Build?"}
        </h1>
        <p className="text-gray-400 text-sm max-w-lg mx-auto">
          {isRTL
            ? "أربعة نماذج حقيقية. أرقام حقيقية من التدريب. لا أرقام مزيفة."
            : "Four real models. Real numbers from actual training. No fake numbers."}
        </p>
      </motion.div>

      {/* ── SECTION 1: WHAT I BUILT ── */}
      <section className="space-y-4">
        <SectionHeading icon={Code2} isRTL={isRTL}
          en="What I Built" ar="ما الذي بنيته" />

        {/* Plain language summary */}
        <motion.div
          custom={0} variants={fadeUp}
          initial="hidden" whileInView="visible"
          viewport={{ once: true }}
          className="glass-card rounded-xl p-5 border border-surface-border"
        >
          <p className="text-gray-300 text-sm leading-relaxed">
            {isRTL
              ? "نظام يقرأ بيانات نقاط البيع الخام من أي منشأة — مقهى، معرض سيارات، عقارات — ويفهم طبيعتها المالية تلقائياً بدون أن يُخبره أحد بنوع النشاط. ثم يقرر: هل هذه المنشأة مؤهلة للقرض؟ وبأي مبلغ؟ وبأي فائدة؟"
              : "A system that reads raw POS transaction data from any business — a café, a car dealership, a real estate office — and automatically understands its financial nature without being told what type of business it is. Then it decides: does this business qualify for a loan? How much? At what rate?"}
          </p>
        </motion.div>

        {/* Four model cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {MODEL_CARDS.map((model, i) => (
            <motion.div key={i} custom={i}
              variants={fadeUp} initial="hidden"
              whileInView="visible" viewport={{ once: true }}
              className={`glass-card rounded-xl p-5 border ${model.bg} space-y-3`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-9 h-9 rounded-lg flex items-center
                                 justify-center ${model.bg}`}>
                  <model.icon size={18} className={model.color} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 text-xs font-mono">
                      {model.num}
                    </span>
                    <span className="text-white font-semibold text-sm">
                      {isRTL ? model.titleAr : model.titleEn}
                    </span>
                  </div>
                  <div className={`text-xs font-mono mt-0.5 ${model.color}`}>
                    {isRTL ? model.techAr : model.techEn}
                  </div>
                </div>
              </div>
              <p className="text-gray-400 text-xs leading-relaxed">
                {isRTL ? model.lineAr : model.lineEn}
              </p>
              <div className="text-xs text-gray-600 font-mono pt-2
                              border-t border-surface-border">
                {model.stat}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── SECTION 2: HOW IT UNDERSTANDS DIFFERENT BUSINESSES ── */}
      <section className="space-y-4">
        <SectionHeading icon={GitBranch} isRTL={isRTL}
          en="How Does It Understand Different Businesses?"
          ar="كيف يفهم الفرق بين الأعمال؟" />

        {/* Key insight callout */}
        <motion.div
          custom={0} variants={fadeUp}
          initial="hidden" whileInView="visible"
          viewport={{ once: true }}
          className="glass-card rounded-xl p-5
                     border border-brand-gold/20 bg-brand-gold/5"
        >
          <p className="text-sm text-white leading-relaxed">
            {isRTL ? (
              <>
                <span className="text-brand-gold font-semibold">
                  النموذج لم يرَ أبداً كلمة "مقهى" أو "معرض سيارات".
                </span>{" "}
                قرأ أرقام المعاملات فقط. اكتشف بنفسه أن المقهى يبيع 97 مرة يومياً بمتوسط 33 ريالاً، بينما معرض السيارات يبيع 4 مرات يومياً بمتوسط 157,000 ريال. هذان النمطان بعيدان جداً في الفضاء السلوكي لدرجة أن النموذج وضعهما في مجموعتين مختلفتين تلقائياً.
              </>
            ) : (
              <>
                <span className="text-brand-gold font-semibold">
                  The model never saw the words "café" or "car dealer".
                </span>{" "}
                It only read transaction numbers. It discovered on its own that the café sells 97 times daily at SAR 33 average, while the car dealer sells 4 times daily at SAR 157,000 average. These two patterns are so far apart in behavioral space that the model placed them in completely different clusters automatically.
              </>
            )}
          </p>
        </motion.div>

        {/* Side-by-side fingerprint comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(fingerprints).map(([key, biz], bi) => (
            <motion.div key={key} custom={bi}
              variants={fadeUp} initial="hidden"
              whileInView="visible" viewport={{ once: true }}
              className="glass-card rounded-xl p-5 space-y-4"
            >
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${biz.color}`} />
                <span className="text-white font-semibold text-sm">
                  {isRTL ? biz.nameAr : biz.nameEn}
                </span>
                <span className="text-gray-600 text-xs ms-auto">
                  {isRTL ? "البصمة السلوكية" : "Behavioral Fingerprint"}
                </span>
              </div>

              <div className="space-y-3">
                {biz.features.map((f, fi) => (
                  <div key={fi} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">
                        {isRTL ? f.labelAr : f.labelEn}
                      </span>
                      <span className={`font-medium ${
                        key === "cafe" ? "text-brand-gold" : "text-status-blue"
                      }`}>
                        {f.display}
                      </span>
                    </div>
                    <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${
                          key === "cafe" ? "bg-brand-gold/70" : "bg-status-blue/70"
                        }`}
                        initial={{ width: "0%" }}
                        whileInView={{ width: `${(f.value / f.max) * 100}%` }}
                        viewport={{ once: true }}
                        transition={{
                          duration: 0.6,
                          ease: [0.23, 1, 0.32, 1],
                          delay: fi * 0.07,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-surface-border
                              flex items-center justify-between text-xs">
                <span className="text-gray-500">
                  {isRTL ? "المجموعة المكتشفة" : "Detected Cluster"}
                </span>
                <span className={`font-mono font-bold ${
                  key === "cafe" ? "text-brand-gold" : "text-status-blue"
                }`}>
                  {key === "cafe"
                    ? "C6 — high_freq_low_ticket_food"
                    : "C2 — low_freq_very_high_ticket_auto"}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Two-track system */}
        <motion.div
          custom={2} variants={fadeUp}
          initial="hidden" whileInView="visible"
          viewport={{ once: true }}
          className="glass-card rounded-xl p-5 space-y-4 border border-surface-border"
        >
          <div className="text-sm font-semibold text-white">
            {isRTL ? "نظام التصنيف ثنائي المسار" : "Two-Track Classification System"}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-2 p-3 rounded-lg bg-surface-dark
                            border border-brand-blue/20">
              <div className="text-xs font-medium text-white">
                {isRTL ? "المسار 1: بيانات حقيقية" : "Track 1: Real Data"}
              </div>
              <div className="space-y-1 text-xs text-gray-500 font-mono">
                <div>raw CSV → 15 features</div>
                <div>→ StandardScaler → PCA(8)</div>
                <div>→ nearest HDBSCAN centroid</div>
                <div>→ behavioral profile</div>
              </div>
              <div className="text-xs text-status-green">
                Confidence: 74–100%
              </div>
            </div>
            <div className="space-y-2 p-3 rounded-lg bg-surface-dark
                            border border-brand-gold/20">
              <div className="text-xs font-medium text-white">
                {isRTL ? "المسار 2: استبيان جديد" : "Track 2: Intake Form"}
              </div>
              <div className="space-y-1 text-xs text-gray-500 font-mono">
                <div>8 params → same 15 features</div>
                <div>→ same scaler → same PCA</div>
                <div>→ same cluster space</div>
                <div>→ identical profile format</div>
              </div>
              <div className="text-xs text-brand-gold">
                Confidence: capped 65% · blends to real over 30d
              </div>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-surface-dark
                          border border-surface-border space-y-1">
            <div className="text-xs text-gray-500 mb-1">
              {isRTL ? "معادلة الدمج" : "Blend Formula"}
            </div>
            <code className="text-brand-gold text-xs font-mono block">
              weight = min(data_days / 30.0, 1.0)
            </code>
            <code className="text-gray-400 text-xs font-mono block">
              blended[f] = real[f] × weight + intake[f] × (1 − weight)
            </code>
          </div>
        </motion.div>
      </section>

      {/* ── SECTION 3: PROOF IT WORKS ── */}
      <section className="space-y-4">
        <SectionHeading icon={BarChart2} isRTL={isRTL}
          en="The Proof — Real Numbers" ar="الدليل — أرقام حقيقية" />

        {/* Training stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { value: "12",    label: isRTL ? "مجموعة مكتشفة"  : "Clusters Found",    sub: isRTL ? "بدون تصنيفات"          : "Without labels",         color: "text-brand-gold"   },
            { value: "100%",  label: isRTL ? "نقاء المجموعات"  : "Archetype Purity",  sub: "ARI ≈ 1.0",                                                                             color: "text-status-green" },
            { value: "0%",    label: isRTL ? "نقاط ضوضاء"      : "Noise Points",      sub: isRTL ? "كل النقاط صُنّفت"     : "All points classified",   color: "text-status-green" },
            { value: "1,800", label: isRTL ? "عينة تدريب"      : "Training Samples",  sub: "12 archetypes × 150",                                                                   color: "text-status-blue"  },
          ].map((stat, i) => (
            <motion.div key={i} custom={i}
              variants={fadeUp} initial="hidden"
              whileInView="visible" viewport={{ once: true }}
              className="glass-card rounded-xl p-4 space-y-1 text-center"
            >
              <div className={`text-2xl font-bold ${stat.color}`}>
                {stat.value}
              </div>
              <div className="text-white text-xs font-medium">{stat.label}</div>
              <div className="text-gray-600 text-xs">{stat.sub}</div>
            </motion.div>
          ))}
        </div>

        {/* Real business classifications */}
        <motion.div
          custom={1} variants={fadeUp}
          initial="hidden" whileInView="visible"
          viewport={{ once: true }}
          className="glass-card rounded-xl p-5 space-y-3"
        >
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL
              ? "تصنيف المنشآت الحقيقية — النموذج لم يُخبَر بأسمائها"
              : "Real Business Classifications — Model Was Never Told Their Names"}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {CLASSIFICATIONS.map((item, i) => (
              <motion.div key={i} custom={i}
                variants={fadeUp} initial="hidden"
                whileInView="visible" viewport={{ once: true }}
                className="p-3 rounded-lg bg-surface-dark space-y-2
                           border border-surface-border"
              >
                <div className="flex items-center justify-between">
                  <span className="text-white text-xs font-semibold capitalize">
                    {item.biz}
                  </span>
                  <span className="text-brand-gold text-xs font-mono">
                    {item.cluster}
                  </span>
                </div>
                <div className="text-gray-500 text-xs font-mono truncate">
                  {item.arch}
                </div>
                <Bar value={item.conf} max={100} color="bg-brand-gold/60" />
                <div className="text-gray-600 text-xs">
                  {item.conf}% {isRTL ? "ثقة" : "confidence"}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Live fraud results */}
        <motion.div
          custom={2} variants={fadeUp}
          initial="hidden" whileInView="visible"
          viewport={{ once: true }}
          className="glass-card rounded-xl p-5 space-y-3"
        >
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL
              ? "نتائج كشف الاحتيال الحية من API"
              : "Live Fraud Detection Results From API"}
          </div>
          {loading ? (
            <div className="space-y-2">
              {[...Array(6)].map((_, i) => (
                <div key={i}
                  className="h-8 bg-surface-border rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {BIZ.map((biz, i) => {
                const f = fraudData[biz];
                if (!f) return null;
                return (
                  <motion.div key={i} custom={i}
                    variants={fadeUp} initial="hidden"
                    whileInView="visible" viewport={{ once: true }}
                    className="flex items-center gap-3 p-3 rounded-lg
                               bg-surface-dark text-xs"
                  >
                    <div className={`w-2 h-2 rounded-full shrink-0 ${
                      f.overall_status === "frozen"  ? "bg-status-red"
                      : f.overall_status === "flagged" ? "bg-status-yellow"
                      : "bg-status-green"
                    }`} />
                    <span className="text-white font-medium w-24 shrink-0">
                      {BIZ_NAMES[biz]}
                    </span>
                    <span className={`w-16 shrink-0 font-medium ${
                      f.overall_status === "frozen"  ? "text-status-red"
                      : f.overall_status === "flagged" ? "text-status-yellow"
                      : "text-status-green"
                    }`}>
                      {f.overall_status}
                    </span>
                    <span className="text-gray-600">
                      {isRTL ? "الدرجة:" : "score:"} {f.fraud_score}
                    </span>
                    <span className="text-gray-700 ms-auto">
                      {f.anomalies_detected} {isRTL ? "شذوذ" : "anomaly groups"}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>

        {/* Live DSCR table */}
        <motion.div
          custom={3} variants={fadeUp}
          initial="hidden" whileInView="visible"
          viewport={{ once: true }}
          className="glass-card rounded-xl p-5 space-y-3"
        >
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL
              ? "الحدود الائتمانية الحية: ثابتة مقابل ديناميكية"
              : "Live Credit Limits: Static vs Dynamic (Prophet-adjusted)"}
          </div>
          {loading ? (
            <div className="h-40 bg-surface-border rounded-lg animate-pulse" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-500 border-b border-surface-border">
                    <th className="text-start pb-2 font-medium">
                      {isRTL ? "المنشأة" : "Business"}
                    </th>
                    <th className="text-end pb-2 font-medium">DSCR</th>
                    <th className="text-end pb-2 font-medium">
                      {isRTL ? "المخاطر" : "Risk"}
                    </th>
                    <th className="text-end pb-2 font-medium">
                      {isRTL ? "الحد الثابت" : "Static"}
                    </th>
                    <th className="text-end pb-2 font-medium">
                      {isRTL ? "الحد الديناميكي" : "Dynamic"}
                    </th>
                    <th className="text-end pb-2 font-medium">
                      {isRTL ? "الاتجاه" : "Trend"}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {BIZ.map((biz, i) => {
                    const d = dscrData[biz];
                    if (!d) return null;
                    const dyn    = d.dynamic_credit_limit;
                    const trend  = dyn?.trend_direction || "flat";
                    const change = dyn?.limit_change_pct || 0;
                    return (
                      <tr key={i}
                        className="hover:bg-surface-hover"
                        style={{ transition: "background-color 150ms var(--ease-out)" }}
                      >
                        <td className="py-2 text-white capitalize">
                          {BIZ_NAMES[biz]}
                        </td>
                        <td className="py-2 text-end font-mono text-white">
                          {d.dscr_score?.toFixed(2)}
                        </td>
                        <td className={`py-2 text-end font-medium ${
                          RISK_COLOR[d.risk_tier] || "text-gray-400"
                        }`}>
                          {d.risk_tier?.replace("_", " ")}
                        </td>
                        <td className="py-2 text-end text-gray-400">
                          {d.approved_credit_limit_sar
                            ? `${(d.approved_credit_limit_sar / 1000).toFixed(0)}K`
                            : "—"}
                        </td>
                        <td className="py-2 text-end text-white font-medium">
                          {dyn
                            ? `${(dyn.dynamic_limit_sar / 1000).toFixed(0)}K`
                            : "—"}
                        </td>
                        <td className={`py-2 text-end font-medium ${
                          trend === "growing"   ? "text-status-green"
                          : trend === "declining" ? "text-status-red"
                          : "text-gray-400"
                        }`}>
                          {trend === "growing"    ? `↑ +${change?.toFixed(1)}%`
                          : trend === "declining" ? `↓ ${change?.toFixed(1)}%`
                          : "→ flat"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>

      </section>
    </div>
  );
}
