import { useLang } from "../i18n/LanguageContext";
import { motion } from "framer-motion";
import {
  Wifi, Brain, ShieldCheck, TrendingUp,
  FileText, Calculator, Rocket, GraduationCap,
  Building2, Sprout, ArrowDown, CheckCircle,
  Cpu, Activity, Leaf, CreditCard,
} from "lucide-react";

const fadeUp = {
  hidden:  { opacity: 0, y: 20 },
  visible: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.08, duration: 0.4, ease: [0.23, 1, 0.32, 1] },
  }),
};

// ── Step card (hoisted outside to avoid recreation on re-render) ──
function StepCard({ step, index, isLast, isRTL }) {
  return (
    <div className="relative">
      <motion.div
        custom={index}
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-50px" }}
        className={`glass-card rounded-xl p-5 border ${step.bg} space-y-3`}
      >
        {/* Step number + icon */}
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center
                           justify-center shrink-0 ${step.bg}`}>
            <step.icon size={20} className={step.color} />
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-gray-600 font-mono uppercase tracking-widest">
              {isRTL ? `الخطوة ${index + 1}` : `Step ${index + 1}`}
            </span>
            <span className="text-white font-bold text-sm leading-tight">
              {isRTL ? step.titleAr : step.titleEn}
            </span>
          </div>
        </div>

        {/* Description lines */}
        <div className="space-y-1.5">
          <p className="text-gray-300 text-xs leading-relaxed">
            {isRTL ? step.line1Ar : step.line1En}
          </p>
          <p className="text-gray-500 text-xs leading-relaxed">
            {isRTL ? step.line2Ar : step.line2En}
          </p>
        </div>

        {/* Tech tag */}
        <div className={`inline-flex items-center gap-1.5 px-2 py-1
                         rounded-lg text-xs font-mono border
                         ${step.bg} ${step.color}`}>
          <Cpu size={10} />
          {isRTL ? step.tagAr : step.tagEn}
        </div>
      </motion.div>

      {/* Connector line to next step */}
      {!isLast && (
        <motion.div
          initial={{ scaleY: 0 }}
          whileInView={{ scaleY: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1], delay: 0.2 }}
          style={{ transformOrigin: "top" }}
          className="absolute left-1/2 -translate-x-1/2 w-0.5 h-6
                     bg-gradient-to-b from-surface-border to-transparent
                     top-full"
        />
      )}
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────
export default function HowItWorks() {
  const { isRTL } = useLang();

  const track1 = [
    {
      icon: Wifi,
      color: "text-brand-gold",
      bg:    "bg-brand-gold/10 border-brand-gold/20",
      titleEn: "Connect",
      titleAr: "الربط",
      line1En: "Business links POS system, bank account, and smart energy meter",
      line1Ar: "المنشأة تربط نظام نقاط البيع والحساب البنكي وعداد الطاقة",
      line2En: "Live data streams replace static PDF applications forever",
      line2Ar: "البيانات الحية تحل محل نماذج PDF الثابتة إلى الأبد",
      tagEn: "Open Banking API",
      tagAr: "واجهة برمجة المصرفية المفتوحة",
    },
    {
      icon: Brain,
      color: "text-status-blue",
      bg:    "bg-status-blue/10 border-status-blue/20",
      titleEn: "Understand",
      titleAr: "الفهم",
      line1En: "AI reads transaction fingerprint — identifies business type without labels",
      line1Ar: "الذكاء الاصطناعي يقرأ بصمة المعاملات ويحدد نوع النشاط بدون تصنيف مسبق",
      line2En: "A café and a car dealer treated completely differently — automatically",
      line2Ar: "المقهى ومعرض السيارات يُعاملان بشكل مختلف تماماً — تلقائياً",
      tagEn: "HDBSCAN Clustering",
      tagAr: "تجميع HDBSCAN",
    },
    {
      icon: ShieldCheck,
      color: "text-status-red",
      bg:    "bg-status-red/10 border-status-red/20",
      titleEn: "Assess",
      titleAr: "التقييم",
      line1En: "Fraud checked against this business's own baseline — not generic rules",
      line1Ar: "الاحتيال يُكشف مقارنةً بقاعدة هذه المنشأة تحديداً — لا قواعد عامة",
      line2En: "Expenses estimated, DSCR calculated, revenue forecasted 30 days ahead",
      line2Ar: "المصاريف تُقدَّر، DSCR يُحسب، الإيرادات تُتوقع 30 يوماً مقدماً",
      tagEn: "Isolation Forest + Prophet",
      tagAr: "Isolation Forest + Prophet",
    },
    {
      icon: TrendingUp,
      color: "text-status-green",
      bg:    "bg-status-green/10 border-status-green/20",
      titleEn: "Decide",
      titleAr: "القرار",
      line1En: "Dynamic credit limit issued instantly — grows with the business",
      line1Ar: "حد ائتماني ديناميكي يصدر فوراً — يرتفع مع نمو المنشأة",
      line2En: "Energy-efficient businesses get a lower interest rate automatically",
      line2Ar: "المنشآت الكفؤة في الطاقة تحصل على فائدة أقل تلقائياً",
      tagEn: "DSCR + Sustainability Score",
      tagAr: "DSCR + درجة الاستدامة",
    },
  ];

  const track2 = [
    {
      icon: FileText,
      color: "text-brand-gold",
      bg:    "bg-brand-gold/10 border-brand-gold/20",
      titleEn: "Declare",
      titleAr: "الإعلان",
      line1En: "New entrepreneur fills a simple 8-question intake form",
      line1Ar: "رائد الأعمال الجديد يملأ نموذجاً من 8 أسئلة فقط",
      line2En: "AI maps answers to the same 15 behavioral features as real POS data",
      line2Ar: "الذكاء الاصطناعي يحوّل الإجابات إلى نفس 15 ميزة سلوكية من بيانات نقاط البيع",
      tagEn: "Intake → Feature Mapping",
      tagAr: "استبيان → تعيين الميزات",
    },
    {
      icon: Calculator,
      color: "text-status-blue",
      bg:    "bg-status-blue/10 border-status-blue/20",
      titleEn: "Qualify",
      titleAr: "التأهيل",
      line1En: "Personal salary account connected — DBR calculated against SAMA 33% cap",
      line1Ar: "حساب الراتب الشخصي يُربط — نسبة عبء الدين تُحسب مقابل حد ساما 33%",
      line2En: "Seed loan issued and secured entirely by automatic salary deduction",
      line2Ar: "القرض الأولي يصدر ومضمون بالكامل بخصم تلقائي من الراتب",
      tagEn: "DBR Assessment",
      tagAr: "تقييم نسبة عبء الدين",
    },
    {
      icon: Rocket,
      color: "text-status-yellow",
      bg:    "bg-status-yellow/10 border-status-yellow/20",
      titleEn: "Launch",
      titleAr: "الإطلاق",
      line1En: "Business opens — first real transactions start flowing in",
      line1Ar: "المنشأة تفتح — أول المعاملات الحقيقية تبدأ بالتدفق",
      line2En: "AI watches and learns — confidence grows from 40% toward 95%",
      line2Ar: "الذكاء الاصطناعي يراقب ويتعلم — الثقة ترتفع من 40% نحو 95%",
      tagEn: "Day 0 → Day 30",
      tagAr: "اليوم 0 → اليوم 30",
    },
    {
      icon: GraduationCap,
      color: "text-status-green",
      bg:    "bg-status-green/10 border-status-green/20",
      titleEn: "Graduate",
      titleAr: "التخرج",
      line1En: "30 days of real data collected — transitions to full SME pipeline",
      line1Ar: "30 يوماً من البيانات الحقيقية — الانتقال إلى مسار المنشآت الكامل",
      line2En: "Intake form retired, real behavioral fingerprint takes over completely",
      line2Ar: "الاستبيان يُتقاعد، البصمة السلوكية الحقيقية تستلم الأمر كلياً",
      tagEn: "Full SME Pipeline",
      tagAr: "مسار المنشآت الكامل",
    },
  ];

  return (
    <div className="space-y-12 py-4">

      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="text-center space-y-3"
      >
        <h1 className="text-2xl font-bold text-white">
          {isRTL ? "كيف يعمل DataCore؟" : "How DataCore Works"}
        </h1>
        <p className="text-gray-400 text-sm max-w-lg mx-auto">
          {isRTL
            ? "من بيانات خام إلى قرار ائتماني — بدون أوراق، بدون تدخل بشري"
            : "From raw data to a credit decision — no paperwork, no manual intervention"}
        </p>
      </motion.div>

      {/* Data sources strip */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="glass-card rounded-xl p-4"
      >
        <div className="text-xs text-gray-500 uppercase tracking-widest
                        text-center mb-3">
          {isRTL ? "مصادر البيانات" : "Data Sources"}
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              icon: Activity, color: "text-brand-gold",
              labelEn: "POS Transactions", labelAr: "معاملات نقاط البيع",
              subEn: "Every sale, every hour", subAr: "كل عملية بيع، كل ساعة",
            },
            {
              icon: CreditCard, color: "text-status-blue",
              labelEn: "Bank Account",    labelAr: "الحساب البنكي",
              subEn: "Cash flow history", subAr: "تاريخ التدفق النقدي",
            },
            {
              icon: Leaf, color: "text-emerald-400",
              labelEn: "Energy Meter",   labelAr: "عداد الطاقة",
              subEn: "Efficiency score", subAr: "درجة الكفاءة",
            },
          ].map((src, i) => (
            <div key={i} className="text-center space-y-1.5">
              <div className="w-8 h-8 rounded-lg mx-auto flex items-center
                              justify-center bg-surface-dark">
                <src.icon size={16} className={src.color} />
              </div>
              <div className="text-white text-xs font-medium">
                {isRTL ? src.labelAr : src.labelEn}
              </div>
              <div className="text-gray-600 text-xs">
                {isRTL ? src.subAr : src.subEn}
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Bouncing arrow */}
      <div className="flex justify-center">
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        >
          <ArrowDown size={18} className="text-brand-gold/40" />
        </motion.div>
      </div>

      {/* Two track columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Track 1 — Existing Business */}
        <div className="space-y-3">
          <motion.div
            initial={{ opacity: 0, x: isRTL ? 20 : -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
            className="flex items-center gap-3 p-3 rounded-xl
                       bg-brand-blue/10 border border-brand-blue/20"
          >
            <div className="w-8 h-8 rounded-lg bg-brand-blue/20
                            flex items-center justify-center shrink-0">
              <Building2 size={16} className="text-brand-blueLight" />
            </div>
            <div>
              <div className="text-white text-sm font-semibold">
                {isRTL ? "مسار المنشآت القائمة" : "Existing Business"}
              </div>
              <div className="text-gray-400 text-xs">
                {isRTL ? "لديك بيانات POS حية" : "You have live POS data"}
              </div>
            </div>
          </motion.div>

          <div className="space-y-3">
            {track1.map((step, i) => (
              <StepCard
                key={i}
                step={step}
                index={i}
                isLast={i === track1.length - 1}
                isRTL={isRTL}
              />
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1], delay: 0.2 }}
            className="glass-card rounded-xl p-4 border border-status-green/30
                       bg-status-green/5 flex items-center gap-3"
          >
            <CheckCircle size={20} className="text-status-green shrink-0" />
            <div>
              <div className="text-status-green font-semibold text-sm">
                {isRTL ? "حد ائتماني ديناميكي" : "Dynamic Credit Limit"}
              </div>
              <div className="text-gray-400 text-xs">
                {isRTL
                  ? "يتحدث تلقائياً مع كل دورة بيانات"
                  : "Auto-updates with every data cycle"}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Track 2 — New Business */}
        <div className="space-y-3">
          <motion.div
            initial={{ opacity: 0, x: isRTL ? -20 : 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
            className="flex items-center gap-3 p-3 rounded-xl
                       bg-brand-gold/10 border border-brand-gold/20"
          >
            <div className="w-8 h-8 rounded-lg bg-brand-gold/20
                            flex items-center justify-center shrink-0">
              <Sprout size={16} className="text-brand-gold" />
            </div>
            <div>
              <div className="text-white text-sm font-semibold">
                {isRTL ? "مسار المشاريع الجديدة" : "New Business"}
              </div>
              <div className="text-gray-400 text-xs">
                {isRTL ? "لا تاريخ، راتبك يكفي" : "No history, your salary is enough"}
              </div>
            </div>
          </motion.div>

          <div className="space-y-3">
            {track2.map((step, i) => (
              <StepCard
                key={i}
                step={step}
                index={i}
                isLast={i === track2.length - 1}
                isRTL={isRTL}
              />
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1], delay: 0.2 }}
            className="glass-card rounded-xl p-4 border border-brand-gold/30
                       bg-brand-gold/5 flex items-center gap-3"
          >
            <GraduationCap size={20} className="text-brand-gold shrink-0" />
            <div>
              <div className="text-brand-gold font-semibold text-sm">
                {isRTL ? "تخرج إلى مسار المنشآت" : "Graduates to SME Pipeline"}
              </div>
              <div className="text-gray-400 text-xs">
                {isRTL
                  ? "بعد 30 يوماً من البيانات الحقيقية"
                  : "After 30 days of real transaction data"}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Merge point */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="glass-card rounded-xl p-6 text-center space-y-3
                   border border-brand-gold/20"
      >
        <div className="flex justify-center gap-8 mb-4">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Building2 size={14} className="text-brand-blueLight" />
            {isRTL ? "منشأة قائمة" : "Existing Business"}
          </div>
          <div className="text-gray-600">+</div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Sprout size={14} className="text-brand-gold" />
            {isRTL ? "مشروع جديد" : "New Business"}
          </div>
        </div>
        <ArrowDown size={16} className="text-brand-gold/40 mx-auto" />
        <div className="text-brand-gold font-bold text-lg text-gold-gradient">
          {isRTL
            ? "نظام إقراض واحد يفهم الجميع"
            : "One Lending System That Understands Everyone"}
        </div>
        <div className="text-gray-400 text-sm max-w-md mx-auto">
          {isRTL
            ? "لا يهم نوع المنشأة أو عمرها — DataCore يقيّمها بعدالة"
            : "No matter the business type or age — DataCore assesses it fairly"}
        </div>
      </motion.div>

    </div>
  );
}
