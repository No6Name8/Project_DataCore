import { useState } from "react";
import { useLang } from "../i18n/LanguageContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2, Users, Globe,
  TrendingDown, FileX, ShieldOff,
  BarChart2, Database, Leaf,
  TrendingUp, Clock, Award,
  Landmark, Target, Zap,
  ChevronDown, Info,
} from "lucide-react";

// ── Benefit card ─────────────────────────────────────────────
function BenefitCard({ icon: Icon, iconColor, titleEn, titleAr,
                       detailEn, detailAr, isGold, isRTL, index }) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      custom={index}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-30px" }}
      transition={{ delay: index * 0.06, duration: 0.35, ease: [0.23, 1, 0.32, 1] }}
      onClick={() => setOpen(o => !o)}
      className={`rounded-xl p-4 cursor-pointer select-none
        ${isGold
          ? "border-2 border-brand-gold/50 bg-brand-gold/10 hover:border-brand-gold/80"
          : "glass-card border border-surface-border hover:border-brand-gold/20"
        }`}
      style={{
        transition: "border-color 180ms var(--ease-out), box-shadow 180ms var(--ease-out)",
        boxShadow: isGold
          ? undefined
          : undefined,
      }}
      whileHover={isGold
        ? { boxShadow: "0 0 24px rgba(201,168,76,0.15)" }
        : { boxShadow: "0 4px 20px rgba(0,0,0,0.3)" }
      }
    >
      {/* Header row */}
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center
                         justify-center shrink-0
                         ${isGold ? "bg-brand-gold/20" : "bg-surface-dark"}`}>
          <Icon size={16} className={isGold ? "text-brand-gold" : iconColor} />
        </div>
        <span className={`text-sm font-semibold flex-1
                          ${isGold ? "text-brand-gold" : "text-white"}`}>
          {isRTL ? titleAr : titleEn}
        </span>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
        >
          <ChevronDown size={14}
            className={isGold ? "text-brand-gold/60" : "text-gray-600"} />
        </motion.div>
      </div>

      {/* Expandable detail */}
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
            style={{ overflow: "hidden" }}
          >
            <p className={`text-xs leading-relaxed mt-3 pt-3 border-t
                           ${isGold
                             ? "text-brand-gold/80 border-brand-gold/20"
                             : "text-gray-400 border-surface-border"}`}>
              {isRTL ? detailAr : detailEn}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Column ────────────────────────────────────────────────────
function Column({ icon: Icon, iconColor, headerBg, headerBorder,
                  titleEn, titleAr, subtitleEn, subtitleAr,
                  benefits, isRTL }) {
  return (
    <div className="space-y-3">
      {/* Column header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className={`rounded-xl p-4 border ${headerBg} ${headerBorder}`}
      >
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center
                           justify-center ${headerBg}`}>
            <Icon size={20} className={iconColor} />
          </div>
          <div>
            <div className="text-white font-bold text-sm">
              {isRTL ? titleAr : titleEn}
            </div>
            <div className="text-gray-400 text-xs mt-0.5">
              {isRTL ? subtitleAr : subtitleEn}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Benefit cards */}
      <div className="space-y-2">
        {benefits.map((b, i) => (
          <BenefitCard key={i} {...b} isRTL={isRTL} index={i} />
        ))}
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────
export default function Benefits() {
  const { isRTL } = useLang();

  const bankBenefits = [
    {
      icon: TrendingDown,
      iconColor: "text-status-green",
      titleEn: "Less risk, more loans",
      titleAr: "مخاطر أقل، قروض أكثر",
      detailEn: "Real-time behavioral data catches financial decline before a business misses its first payment. The bank lends with confidence, not hope.",
      detailAr: "البيانات السلوكية الحية تكتشف التراجع المالي قبل أن تفوت المنشأة أول قسط. البنك يُقرض بثقة وليس بأمل.",
      isGold: false,
    },
    {
      icon: FileX,
      iconColor: "text-status-blue",
      titleEn: "Zero paperwork, ever",
      titleAr: "لا أوراق، أبداً",
      detailEn: "No PDF applications, no manual review, no document verification. The data speaks directly. Loan officers focus on edge cases, not routine processing.",
      detailAr: "لا نماذج PDF، لا مراجعة يدوية، لا تحقق من وثائق. البيانات تتكلم مباشرة. ضباط القروض يركزون على الحالات الاستثنائية فقط.",
      isGold: false,
    },
    {
      icon: ShieldOff,
      iconColor: "text-status-red",
      titleEn: "Fraud caught before it costs",
      titleAr: "الاحتيال يُكتشف قبل الخسارة",
      detailEn: "Each business has its own Isolation Forest model trained on its transaction history. Anomalies are flagged against that business's own baseline — not generic rules that miss context.",
      detailAr: "لكل منشأة نموذج Isolation Forest خاص مدرّب على تاريخها. الشذوذات تُكشف مقارنةً بقاعدة المنشأة ذاتها — لا قواعد عامة تفوّت السياق.",
      isGold: false,
    },
    {
      icon: BarChart2,
      iconColor: "text-status-blue",
      titleEn: "Never over-lend",
      titleAr: "لا إقراض زائد أبداً",
      detailEn: "Prophet forecasts the next 30 days of revenue. Declining businesses get lower limits automatically. The bank is never over-exposed to a business heading downward.",
      detailAr: "Prophet يتوقع 30 يوماً من الإيرادات. المنشآت المتراجعة تحصل على حدود أقل تلقائياً. البنك لا يتعرض لمخاطر زائدة من منشأة متجهة نحو الأسفل.",
      isGold: false,
    },
    {
      icon: Database,
      iconColor: "text-brand-gold",
      titleEn: "Real SME data at scale",
      titleAr: "بيانات منشآت حقيقية بالجملة",
      detailEn: "Every connected business becomes a verified, live, dynamic data asset. Transaction patterns, revenue trends, energy consumption — all timestamped and immutable. This data is worth more than the loan interest. It powers credit models, government contracts, economic policy, and future AI training.",
      detailAr: "كل منشأة متصلة تصبح أصلاً بيانياً حياً وديناميكياً وموثقاً. أنماط المعاملات، اتجاهات الإيرادات، استهلاك الطاقة — كلها مختومة بالوقت وغير قابلة للتغيير. هذه البيانات تساوي أكثر من فائدة القرض. إنها تُغذي نماذج الائتمان والعقود الحكومية والسياسة الاقتصادية وتدريب الذكاء الاصطناعي مستقبلاً.",
      isGold: true,
    },
  ];

  const ownerBenefits = [
    {
      icon: Award,
      iconColor: "text-brand-gold",
      titleEn: "Loan based on what you do",
      titleAr: "قرض بناءً على ما تفعل",
      detailEn: "No credit score gatekeeping. No relationship with a bank manager. Your POS data is your application. A thriving street business gets the same access as an established company.",
      detailAr: "لا حاجز لدرجة الائتمان. لا علاقة مع مدير البنك. بيانات نقاط البيع هي طلبك. منشأة شارع مزدهرة تحصل على نفس الوصول كشركة راسخة.",
      isGold: false,
    },
    {
      icon: TrendingUp,
      iconColor: "text-status-green",
      titleEn: "Limit grows as you grow",
      titleAr: "الحد يرتفع مع نموك",
      detailEn: "As revenue grows, Prophet detects the trend and the credit limit increases automatically. No reapplication, no new paperwork, no waiting. Growth is rewarded in real time.",
      detailAr: "مع نمو الإيرادات، Prophet يكتشف الاتجاه والحد الائتماني يرتفع تلقائياً. لا إعادة طلب، لا أوراق جديدة، لا انتظار. النمو يُكافأ في الوقت الفعلي.",
      isGold: false,
    },
    {
      icon: Clock,
      iconColor: "text-status-blue",
      titleEn: "Your salary is enough to start",
      titleAr: "راتبك يكفي للبدء",
      detailEn: "New entrepreneurs with no business history get a salary-backed seed loan. DBR is calculated against SAMA's 33% cap. If you qualify, the loan is issued immediately with automatic salary deduction as security.",
      detailAr: "رواد الأعمال الجدد بلا تاريخ تجاري يحصلون على قرض أولي مضمون بالراتب. نسبة عبء الدين تُحسب مقابل حد ساما 33%. إذا تأهلت، القرض يصدر فوراً مع خصم تلقائي من الراتب كضمان.",
      isGold: false,
    },
    {
      icon: Leaf,
      iconColor: "text-emerald-400",
      titleEn: "Go green, pay less",
      titleAr: "كُن أخضر، ادفع أقل",
      detailEn: "Smart meter data cross-referenced with transaction volume computes an energy efficiency score. Businesses above the threshold get an automatic interest rate discount — no application required.",
      detailAr: "بيانات العداد الذكي مقارنةً بحجم المعاملات تحسب درجة كفاءة الطاقة. المنشآت التي تتجاوز العتبة تحصل على خصم تلقائي على سعر الفائدة — دون أي طلب.",
      isGold: false,
    },
    {
      icon: Zap,
      iconColor: "text-brand-gold",
      titleEn: "Know your health first",
      titleAr: "اعرف صحتك قبل البنك",
      detailEn: "Business owners see their own DSCR score, fraud status, revenue forecast, and credit limit in real time — before the bank makes a decision. No surprises. Full transparency. The owner and the bank see the same data.",
      detailAr: "أصحاب المنشآت يرون درجة DSCR وحالة الاحتيال وتوقعات الإيرادات والحد الائتماني في الوقت الفعلي — قبل أن يتخذ البنك قراره. لا مفاجآت. شفافية كاملة. المالك والبنك يرون نفس البيانات.",
      isGold: false,
    },
  ];

  const economyBenefits = [
    {
      icon: Landmark,
      iconColor: "text-status-blue",
      titleEn: "More SMEs get funded",
      titleAr: "تمويل أكثر للمنشآت الصغيرة",
      detailEn: "Saudi SMEs represent 99% of businesses but receive disproportionately low credit access. DataCore removes the paperwork barrier and replaces it with live data — unlocking credit for businesses that were previously unassessable.",
      detailAr: "المنشآت الصغيرة السعودية تمثل 99% من الأعمال لكنها تحصل على وصول ائتماني منخفض. DataCore يزيل حاجز الأوراق ويستبدله بالبيانات الحية — يفتح الائتمان للمنشآت التي كانت غير قابلة للتقييم سابقاً.",
      isGold: false,
    },
    {
      icon: Users,
      iconColor: "text-status-green",
      titleEn: "More entrepreneurs enter banking",
      titleAr: "المزيد من رواد الأعمال يدخلون النظام البنكي",
      detailEn: "The Incubator pipeline pulls new entrepreneurs into the formal banking ecosystem before they even open their business. Earlier entry means more history, better assessment, stronger economy.",
      detailAr: "مسار الحاضنة يجذب رواد الأعمال الجدد إلى النظام البنكي الرسمي قبل أن يفتحوا مشاريعهم حتى. الدخول المبكر يعني تاريخاً أكثر، تقييماً أفضل، اقتصاداً أقوى.",
      isGold: false,
    },
    {
      icon: Target,
      iconColor: "text-brand-gold",
      titleEn: "Vision 2030 SME target",
      titleAr: "هدف رؤية 2030 للمنشآت الصغيرة",
      detailEn: "Vision 2030 targets raising SME contribution to GDP from 30% to 35%. DataCore directly enables this by removing the friction that prevents eligible SMEs from accessing credit and growing.",
      detailAr: "رؤية 2030 تستهدف رفع مساهمة المنشآت الصغيرة في الناتج المحلي من 30% إلى 35%. DataCore يُمكّن هذا مباشرةً بإزالة الاحتكاك الذي يمنع المنشآت المؤهلة من الوصول إلى الائتمان والنمو.",
      isGold: false,
    },
    {
      icon: Leaf,
      iconColor: "text-emerald-400",
      titleEn: "Greener businesses, nationally",
      titleAr: "منشآت أكثر خضرة على المستوى الوطني",
      detailEn: "The sustainability discount creates a direct financial incentive for SMEs to reduce energy consumption. At scale, this produces measurable national impact on commercial energy efficiency aligned with Saudi Green Initiative.",
      detailAr: "خصم الاستدامة يخلق حافزاً مالياً مباشراً للمنشآت الصغيرة لتقليل استهلاك الطاقة. على نطاق واسع، هذا ينتج تأثيراً وطنياً قابلاً للقياس على كفاءة الطاقة التجارية منسجماً مع مبادرة السعودية الخضراء.",
      isGold: false,
    },
    {
      icon: Database,
      iconColor: "text-brand-gold",
      titleEn: "Verified economic data, live",
      titleAr: "بيانات اقتصادية موثقة وحية",
      detailEn: "Every connected SME produces a verified, timestamped, tamper-proof economic data stream. At national scale this becomes an unprecedented real-time map of the Saudi SME economy — more accurate than any survey, more current than any report. Available for government contracts, economic policy, and national planning.",
      detailAr: "كل منشأة صغيرة متصلة تنتج تدفقاً بيانياً اقتصادياً موثقاً ومختوماً بالوقت وغير قابل للتلاعب. على المستوى الوطني يصبح هذا خريطة غير مسبوقة للاقتصاد السعودي للمنشآت الصغيرة في الوقت الفعلي — أدق من أي مسح، وأحدث من أي تقرير. متاح للعقود الحكومية والسياسة الاقتصادية والتخطيط الوطني.",
      isGold: true,
    },
  ];

  return (
    <div className="space-y-10 py-4">

      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="text-center space-y-3"
      >
        <h1 className="text-2xl font-bold text-white">
          {isRTL ? "من يستفيد؟ الجميع." : "Who Benefits? Everyone."}
        </h1>
        <p className="text-gray-400 text-sm max-w-lg mx-auto">
          {isRTL
            ? "DataCore لا يحل مشكلة واحدة — يحل ثلاثاً في آنٍ واحد"
            : "DataCore doesn't solve one problem — it solves three simultaneously"}
        </p>
        <div className="flex items-center justify-center gap-1.5
                        text-xs text-gray-500">
          <Info size={12} />
          {isRTL
            ? "انقر على أي بطاقة لمعرفة التفاصيل"
            : "Click any card to see details"}
        </div>
      </motion.div>

      {/* Three columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Column
          icon={Building2}
          iconColor="text-brand-blueLight"
          headerBg="bg-brand-blue/10"
          headerBorder="border-brand-blue/20"
          titleEn="Alinma Bank"
          titleAr="بنك الإنماء"
          subtitleEn="What the bank gains"
          subtitleAr="ما يكسبه البنك"
          benefits={bankBenefits}
          isRTL={isRTL}
        />
        <Column
          icon={Users}
          iconColor="text-brand-gold"
          headerBg="bg-brand-gold/10"
          headerBorder="border-brand-gold/20"
          titleEn="Business Owners"
          titleAr="أصحاب المنشآت"
          subtitleEn="What owners gain"
          subtitleAr="ما يكسبه الملاك"
          benefits={ownerBenefits}
          isRTL={isRTL}
        />
        <Column
          icon={Globe}
          iconColor="text-emerald-400"
          headerBg="bg-emerald-400/10"
          headerBorder="border-emerald-400/20"
          titleEn="Saudi Economy"
          titleAr="الاقتصاد السعودي"
          subtitleEn="What the nation gains"
          subtitleAr="ما تكسبه المملكة"
          benefits={economyBenefits}
          isRTL={isRTL}
        />
      </div>

      {/* Bottom summary strip */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="glass-card rounded-xl p-6 border border-brand-gold/20"
      >
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
          {[
            {
              value: "250K+",
              labelEn: "SAR Prize at Stake",
              labelAr: "ريال جائزة على المحك",
              color: "text-brand-gold",
            },
            {
              value: "99%",
              labelEn: "of Saudi Businesses are SMEs",
              labelAr: "من الأعمال السعودية منشآت صغيرة",
              color: "text-status-green",
            },
            {
              value: "35%",
              labelEn: "Vision 2030 SME GDP Target",
              labelAr: "هدف رؤية 2030 لمساهمة المنشآت",
              color: "text-status-blue",
            },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
            >
              <div className={`text-3xl font-bold ${stat.color}`}>
                {stat.value}
              </div>
              <div className="text-gray-400 text-xs mt-1">
                {isRTL ? stat.labelAr : stat.labelEn}
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

    </div>
  );
}
