import { useLang } from "../i18n/LanguageContext";
import { motion } from "framer-motion";
import {
  Database, Cpu, ShieldCheck, TrendingUp,
  ArrowDown, ArrowRight, ArrowLeft,
  Building2, Sprout, CheckCircle,
  Zap, Leaf, CreditCard, Activity
} from "lucide-react";

const fadeUp = {
  hidden:  { opacity: 0, y: 20 },
  visible: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.1, duration: 0.4, ease: [0.23, 1, 0.32, 1] }
  }),
};

export default function HowItWorks() {
  const { isRTL } = useLang();
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  return (
    <div className="space-y-16 py-4">

      {/* Page header */}
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold text-white">
          {isRTL ? "كيف يعمل DataCore؟" : "How DataCore Works"}
        </h1>
        <p className="text-gray-400 max-w-xl mx-auto text-sm leading-relaxed">
          {isRTL
            ? "من بيانات نقاط البيع الخام إلى قرار ائتماني مباشر — أربع طبقات من الذكاء الاصطناعي بدون تدخل بشري"
            : "From raw POS data to a live credit decision — four layers of AI with zero manual intervention"}
        </p>
      </div>

      {/* Data sources */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-brand-gold uppercase
                       tracking-widest text-center">
          {isRTL ? "مصادر البيانات" : "Data Sources"}
        </h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: Activity,   color: "text-brand-gold",
              labelEn: "POS Transactions",    labelAr: "معاملات نقاط البيع",
              subEn:   "Real-time sales feed", subAr: "تغذية مبيعات مباشرة" },
            { icon: CreditCard, color: "text-status-blue",
              labelEn: "Bank Account",        labelAr: "الحساب البنكي",
              subEn:   "Cash flow history",    subAr: "تاريخ التدفق النقدي" },
            { icon: Leaf,       color: "text-emerald-400",
              labelEn: "Smart Energy Meter",  labelAr: "عداد الطاقة الذكي",
              subEn:   "Efficiency score",     subAr: "درجة الكفاءة" },
          ].map((src, i) => (
            <motion.div key={i} custom={i}
              variants={fadeUp} initial="hidden" whileInView="visible"
              viewport={{ once: true }}
              className="glass-card rounded-xl p-4 text-center space-y-2">
              <src.icon size={24} className={`mx-auto ${src.color}`} />
              <div className="text-white text-xs font-medium">
                {isRTL ? src.labelAr : src.labelEn}
              </div>
              <div className="text-gray-500 text-xs">
                {isRTL ? src.subAr : src.subEn}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Arrow down */}
      <div className="flex justify-center">
        <ArrowDown size={20} className="text-brand-gold/40 animate-bounce" />
      </div>

      {/* 4 AI Models pipeline */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-brand-gold uppercase
                       tracking-widest text-center">
          {isRTL ? "طبقات الذكاء الاصطناعي" : "AI Processing Layers"}
        </h2>
        <div className="space-y-3">
          {[
            {
              num: "01", icon: Database, color: "text-brand-gold",
              bg: "bg-brand-gold/10 border-brand-gold/20",
              titleEn: "Business Classifier",
              titleAr: "مصنّف الأعمال",
              techEn:  "HDBSCAN Unsupervised Clustering",
              techAr:  "تجميع HDBSCAN غير خاضع للإشراف",
              descEn:  "Reads raw transaction fingerprint. Identifies business archetype without being told what the business is. Works for any business type — even ones never seen before.",
              descAr:  "يقرأ بصمة المعاملات الخام. يحدد نمط الأعمال دون إخباره بنوع النشاط. يعمل مع أي نوع تجاري.",
            },
            {
              num: "02", icon: Cpu, color: "text-status-blue",
              bg: "bg-status-blue/10 border-status-blue/20",
              titleEn: "Expense Estimator",
              titleAr: "مقدّر المصاريف",
              techEn:  "Behavioral Feature Mapping",
              techAr:  "تعيين الميزات السلوكية",
              descEn:  "Derives COGS, labor, and overhead ratios from behavioral signals — not hardcoded rules. Inventory businesses auto-detected. Zero manual configuration.",
              descAr:  "يستخرج نسب التكلفة من الإشارات السلوكية. الشركات ذات المخزون تُكتشف تلقائياً. لا إعداد يدوي.",
            },
            {
              num: "03", icon: ShieldCheck, color: "text-status-red",
              bg: "bg-status-red/10 border-status-red/20",
              titleEn: "Fraud Detector",
              titleAr: "كاشف الاحتيال",
              techEn:  "Isolation Forest (per-business model)",
              techAr:  "Isolation Forest (نموذج لكل منشأة)",
              descEn:  "Each business gets its own model trained on its transaction history. A 3AM transaction at a real estate office is anomalous. At a 24hr minimarket it is not.",
              descAr:  "كل منشأة لها نموذجها الخاص. معاملة الساعة 3 صباحاً في مكتب عقاري شاذة. في ميني ماركت 24 ساعة ليست كذلك.",
            },
            {
              num: "04", icon: TrendingUp, color: "text-status-green",
              bg: "bg-status-green/10 border-status-green/20",
              titleEn: "Revenue Forecaster",
              titleAr: "متنبئ الإيرادات",
              techEn:  "Facebook Prophet + Saudi Weekly Seasonality",
              techAr:  "Facebook Prophet + الموسمية الأسبوعية السعودية",
              descEn:  "Forecasts next 30 days of revenue with confidence intervals. Growing businesses get higher credit limits. Declining businesses get lower limits — automatically.",
              descAr:  "يتوقع إيرادات 30 يوماً القادمة. الأعمال النامية تحصل على حدود أعلى. المتراجعة تحصل على حدود أقل — تلقائياً.",
            },
          ].map((model, i) => (
            <motion.div key={i} custom={i}
              variants={fadeUp} initial="hidden" whileInView="visible"
              viewport={{ once: true }}
              className={`glass-card rounded-xl p-5 border ${model.bg}`}>
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center gap-2 shrink-0">
                  <div className={`w-10 h-10 rounded-lg flex items-center
                                   justify-center ${model.bg}`}>
                    <model.icon size={20} className={model.color} />
                  </div>
                  {i < 3 && (
                    <div className="w-0.5 h-6 bg-surface-border" />
                  )}
                </div>
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-gray-600">
                      {model.num}
                    </span>
                    <span className="font-semibold text-white text-sm">
                      {isRTL ? model.titleAr : model.titleEn}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full
                                      ${model.bg} ${model.color} font-mono`}>
                      {isRTL ? model.techAr : model.techEn}
                    </span>
                  </div>
                  <p className="text-gray-400 text-xs leading-relaxed">
                    {isRTL ? model.descAr : model.descEn}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Arrow down */}
      <div className="flex justify-center">
        <ArrowDown size={20} className="text-brand-gold/40 animate-bounce" />
      </div>

      {/* Output */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-brand-gold uppercase
                       tracking-widest text-center">
          {isRTL ? "المخرجات" : "Output"}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              icon: CreditCard, color: "text-status-green",
              titleEn: "Dynamic Credit Limit",
              titleAr: "حد ائتماني ديناميكي",
              descEn:  "Grows with revenue. Shrinks if declining.",
              descAr:  "يرتفع مع الإيرادات. ينخفض عند التراجع.",
            },
            {
              icon: Zap, color: "text-brand-gold",
              titleEn: "Live Interest Rate",
              titleAr: "سعر فائدة حي",
              descEn:  "Base rate minus sustainability discount.",
              descAr:  "السعر الأساسي ناقص خصم الاستدامة.",
            },
            {
              icon: ShieldCheck, color: "text-status-blue",
              titleEn: "Fraud Decision",
              titleAr: "قرار الاحتيال",
              descEn:  "Clear / Flagged / Frozen — per business.",
              descAr:  "سليم / مشكوك / مجمّد — لكل منشأة.",
            },
          ].map((out, i) => (
            <motion.div key={i} custom={i}
              variants={fadeUp} initial="hidden" whileInView="visible"
              viewport={{ once: true }}
              className="glass-card rounded-xl p-5 text-center space-y-2">
              <out.icon size={24} className={`mx-auto ${out.color}`} />
              <div className="font-semibold text-white text-sm">
                {isRTL ? out.titleAr : out.titleEn}
              </div>
              <div className="text-gray-400 text-xs">
                {isRTL ? out.descAr : out.descEn}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Two pipelines */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-brand-gold uppercase
                       tracking-widest text-center">
          {isRTL ? "مسارا الإقراض" : "Two Lending Pipelines"}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* SME */}
          <div className="glass-card rounded-xl p-6 space-y-3
                          border border-brand-blue/30">
            <div className="flex items-center gap-2">
              <Building2 size={18} className="text-brand-blueLight" />
              <span className="font-semibold text-white text-sm">
                {isRTL ? "مسار المنشآت القائمة" : "Existing SME Pipeline"}
              </span>
            </div>
            <div className="space-y-2">
              {(isRTL ? [
                "ربط بيانات POS الحية",
                "تصنيف سلوك الأعمال (Model 1)",
                "تقدير المصاريف (Model 2)",
                "كشف الاحتيال (Model 3)",
                "توقع الإيرادات (Model 4)",
                "إصدار الحد الائتماني الديناميكي",
              ] : [
                "Connect live POS data",
                "Classify business behavior (Model 1)",
                "Estimate expense structure (Model 2)",
                "Detect fraud anomalies (Model 3)",
                "Forecast revenue (Model 4)",
                "Issue dynamic credit limit",
              ]).map((step, i) => (
                <div key={i}
                  className="flex items-center gap-2 text-xs text-gray-300">
                  <CheckCircle size={12} className="text-status-green shrink-0" />
                  {step}
                </div>
              ))}
            </div>
          </div>

          {/* Incubator */}
          <div className="glass-card rounded-xl p-6 space-y-3
                          border border-brand-gold/20">
            <div className="flex items-center gap-2">
              <Sprout size={18} className="text-brand-gold" />
              <span className="font-semibold text-white text-sm">
                {isRTL ? "مسار الحاضنة" : "Incubator Pipeline"}
              </span>
            </div>
            <div className="space-y-2">
              {(isRTL ? [
                "ربط حساب الراتب الشخصي",
                "حساب نسبة عبء الدين (DBR)",
                "قرض أولي مضمون بالراتب",
                "تصنيف المشروع عبر نموذج الاستبيان",
                "مراقبة نمو البيانات (يوم 0 → 30)",
                "الانتقال إلى مسار المنشآت القائمة",
              ] : [
                "Connect personal salary account",
                "Calculate Debt Burden Ratio (DBR)",
                "Issue salary-backed seed loan",
                "Classify business via intake form",
                "Monitor data growth (Day 0 → 30)",
                "Graduate to SME pipeline",
              ]).map((step, i) => (
                <div key={i}
                  className="flex items-center gap-2 text-xs text-gray-300">
                  <CheckCircle size={12} className="text-brand-gold shrink-0" />
                  {step}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
