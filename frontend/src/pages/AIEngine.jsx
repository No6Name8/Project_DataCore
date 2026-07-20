import { useLang } from "../i18n/LanguageContext";
import { motion } from "framer-motion";
import {
  Cpu, Sparkles, Calculator, ShieldCheck, TrendingUp,
  Layers, Scale, Info,
} from "lucide-react";

/* ── Bilingual content ───────────────────────────────────────── */
const COPY = {
  en: {
    title: "The Engine Behind DataCore",
    subtitle:
      "Four AI models working together to turn live business data into explainable lending decisions.",

    models: [
      {
        icon: Sparkles,
        tag: "Model 01",
        name: "Behavioral Classification",
        does: "Groups businesses by how they actually operate — transaction rhythms, ticket sizes, time-of-day patterns — instead of by their registered industry category.",
        approach: "Density-based unsupervised clustering. The system identifies natural groupings in behavioral data without needing labeled training examples.",
        validation: "Tested against public retail datasets from UCI, Kaggle, and others. On datasets that match the classifier's design assumptions — hour-level transaction timestamps and SME retail behavior — the classifier correctly identifies the archetype every time in current testing. On datasets outside this scope (e.g. wholesale, aggregated reports), it correctly declines to force-fit, which is the intended behavior.",
        limit: "Designed for SME retail with granular transaction data. Businesses without hour-level timestamps or with fundamentally different transaction structures fall outside its scope by design.",
      },
      {
        icon: Calculator,
        tag: "Model 02",
        name: "Behavioral Expense Estimation",
        does: "Estimates a business's cost structure — cost of goods, labor, overhead — from how the business behaves, not from tax filings or accountant reports.",
        approach: "Multi-layer feature mapping from behavioral signals to expense ratios, calibrated against published industry benchmarks. Includes commission-based business detection for real estate, insurance, and similar sectors where standard cost models fail.",
        validation: "Benchmark pass rate on real-world datasets is currently strong for standard retail and food service, with documented gaps in edge cases like extremely sparse datasets.",
        limit: "Requires sufficient transaction density to produce stable estimates. Very low-volume businesses will show wider uncertainty ranges.",
      },
      {
        icon: ShieldCheck,
        tag: "Model 03",
        name: "Fraud Detection",
        does: "Detects anomalies specific to each individual business — not by generic industry rules.",
        approach: "A separate anomaly detection model is trained for every business, learning what normal transaction behavior looks like for that specific business. Severity is rate-based rather than count-based, avoiding false alarms from small-sample noise.",
        validation: "Every fraud flag comes with an explanation: which transaction, what amount, what date, and why it looked wrong. Credit officers review the evidence — they don't just receive a score.",
        limit: "New businesses with limited transaction history use a cluster-level fallback until enough per-business data accumulates. This is shown transparently in the system output.",
      },
      {
        icon: TrendingUp,
        tag: "Model 04",
        name: "Revenue Forecasting",
        does: "Predicts a business's revenue for the next 30 days, informing dynamic credit limit calculations.",
        approach: "Time-series forecasting with regional seasonality built in — including Saudi Thursday–Friday weekend patterns rather than assumed global defaults.",
        validation: "Forecasts include confidence intervals, not just point estimates. The bank sees the range of likely outcomes, not a single number that hides uncertainty.",
        limit: "Forecasts for businesses with less than 90 days of history carry wider uncertainty. The system flags this openly rather than pretending to know.",
      },
    ],

    labelDoes: "What it does",
    labelApproach: "Approach",
    labelValidation: "Validation",
    labelLimit: "Honest limit",

    togetherTag: "Integration",
    togetherTitle: "How they work together",
    togetherBody:
      "The four models feed into a single lending decision layer. The classifier informs the expense estimator. The fraud detector runs independently, but its output gates the credit decision. The revenue forecaster shapes the dynamic credit limit. Every output includes reasons a credit officer can review, audit, and act on.",

    claimTag: "Boundaries",
    claimTitle: "What we don't claim",
    claimBody:
      "DataCore is a decision support layer, not autonomous lending. It surfaces evidence, ranks risk, and explains its reasoning — but credit officers make the final call. This is deliberate: SAMA-regulated lending requires human accountability, and the tool is designed to strengthen that, not replace it.",
  },

  ar: {
    title: "المحرك وراء DataCore",
    subtitle:
      "أربعة نماذج ذكاء تعمل معاً لتحويل بيانات المنشآت الحية إلى قرارات إقراض قابلة للتفسير.",

    models: [
      {
        icon: Sparkles,
        tag: "النموذج ٠١",
        name: "التصنيف السلوكي",
        does: "يجمّع المنشآت حسب طريقة عملها الفعلية — إيقاع المعاملات وأحجام الفواتير وأنماط أوقات اليوم — بدلاً من تصنيفها الصناعي المسجَّل.",
        approach: "تجميع غير خاضع للإشراف قائم على الكثافة. يتعرّف النظام على التجمّعات الطبيعية في البيانات السلوكية دون الحاجة إلى أمثلة تدريب مُصنّفة.",
        validation: "اختُبر مقابل مجموعات بيانات تجزئة عامة من UCI وKaggle وغيرها. على البيانات التي تطابق افتراضات تصميم المصنّف — طوابع زمنية بدقة الساعة وسلوك تجزئة للمنشآت الصغيرة — يحدّد المصنّف النمط بشكل صحيح في كل مرة في الاختبارات الحالية. وخارج هذا النطاق (كالجملة أو التقارير المجمّعة) يمتنع عن الإقحام القسري، وهو السلوك المقصود.",
        limit: "مصمَّم لتجزئة المنشآت الصغيرة ببيانات معاملات دقيقة. المنشآت بلا طوابع زمنية بدقة الساعة أو ذات بُنى معاملات مختلفة جذرياً تقع خارج نطاقه بحكم التصميم.",
      },
      {
        icon: Calculator,
        tag: "النموذج ٠٢",
        name: "تقدير المصاريف السلوكي",
        does: "يقدّر هيكل تكلفة المنشأة — تكلفة البضاعة والعمالة والتشغيل — من سلوكها، لا من الإقرارات الضريبية أو تقارير المحاسبين.",
        approach: "تعيين ميزات متعدد الطبقات من الإشارات السلوكية إلى نسب المصاريف، معايَر مقابل معايير صناعية منشورة. يشمل كشف الأعمال القائمة على العمولة للعقار والتأمين والقطاعات المشابهة حيث تفشل نماذج التكلفة القياسية.",
        validation: "معدّل اجتياز المعايير على بيانات واقعية قويٌّ حالياً للتجزئة القياسية وخدمات الطعام، مع فجوات موثّقة في الحالات الحدّية كالبيانات شديدة التناثر.",
        limit: "يتطلب كثافة معاملات كافية لإنتاج تقديرات مستقرة. المنشآت منخفضة الحجم جداً ستُظهر نطاقات عدم يقين أوسع.",
      },
      {
        icon: ShieldCheck,
        tag: "النموذج ٠٣",
        name: "كشف الاحتيال",
        does: "يكشف الشذوذات الخاصة بكل منشأة على حدة — لا بقواعد صناعية عامة.",
        approach: "يُدرَّب نموذج كشف شذوذ منفصل لكل منشأة، يتعلّم كيف يبدو السلوك الطبيعي لتلك المنشأة تحديداً. الشدّة قائمة على المعدّل لا على العدد، ما يتجنّب الإنذارات الكاذبة من ضوضاء العينات الصغيرة.",
        validation: "كل تنبيه احتيال مرفق بتفسير: أي معاملة، وأي مبلغ، وأي تاريخ، ولماذا بدا خاطئاً. يراجع موظفو الائتمان الدليل — لا يتلقّون درجة فحسب.",
        limit: "المنشآت الجديدة بتاريخ معاملات محدود تستخدم بديلاً على مستوى التجمّع حتى تتراكم بيانات كافية لكل منشأة. ويظهر ذلك بشفافية في مخرجات النظام.",
      },
      {
        icon: TrendingUp,
        tag: "النموذج ٠٤",
        name: "توقّع الإيرادات",
        does: "يتنبأ بإيرادات المنشأة للثلاثين يوماً القادمة، بما يغذّي حسابات الحد الائتماني الديناميكي.",
        approach: "توقّع للسلاسل الزمنية بموسمية إقليمية مدمجة — تشمل نمط عطلة الخميس والجمعة السعودية بدلاً من افتراضات عالمية.",
        validation: "التوقّعات تتضمّن فترات ثقة، لا تقديرات نقطية فقط. يرى البنك نطاق النتائج المحتملة، لا رقماً واحداً يُخفي عدم اليقين.",
        limit: "توقّعات المنشآت بأقل من ٩٠ يوماً من التاريخ تحمل عدم يقين أوسع. ويُشير النظام إلى ذلك صراحةً بدل ادّعاء المعرفة.",
      },
    ],

    labelDoes: "ماذا يفعل",
    labelApproach: "المنهج",
    labelValidation: "التحقّق",
    labelLimit: "الحدّ الصريح",

    togetherTag: "التكامل",
    togetherTitle: "كيف تعمل معاً",
    togetherBody:
      "تتغذّى النماذج الأربعة في طبقة قرار إقراض واحدة. المصنّف يُرشد مقدّر المصاريف. كاشف الاحتيال يعمل مستقلاً، لكن مخرجه يحكم قرار الائتمان. متنبّئ الإيرادات يشكّل الحد الائتماني الديناميكي. كل مخرج يتضمّن أسباباً يستطيع موظف الائتمان مراجعتها وتدقيقها والتصرّف بناءً عليها.",

    claimTag: "الحدود",
    claimTitle: "ما الذي لا ندّعيه",
    claimBody:
      "DataCore طبقة دعم قرار، لا إقراض ذاتي. يُبرز الأدلة، ويرتّب المخاطر، ويشرح استدلاله — لكن موظفي الائتمان يتخذون القرار النهائي. وهذا متعمَّد: الإقراض المنظَّم من ساما يتطلب مساءلة بشرية، والأداة مصمَّمة لتعزيزها لا لاستبدالها.",
  },
};

/* ── Labeled paragraph block ─────────────────────────────────── */
function Field({ label, children }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-widest text-brand-gold/80">
        {label}
      </div>
      <p className="mt-1 text-sm leading-relaxed text-cream-dim">{children}</p>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────── */
export default function AIEngine() {
  const { lang, isRTL } = useLang();
  const c = COPY[lang];

  return (
    <div className="space-y-6 max-w-3xl">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
      >
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                         text-xs font-medium tracking-wide uppercase
                         text-brand-gold bg-brand-gold/10 border border-brand-gold/20">
          <Cpu size={13} />
          {lang === "ar" ? "المحرك" : "The Engine"}
        </span>
        <h2 className="mt-3 font-display font-bold text-2xl sm:text-3xl text-cream">
          {c.title}
        </h2>
        <p className="mt-2 text-base sm:text-lg leading-relaxed text-cream-dim max-w-2xl">
          {c.subtitle}
        </p>
      </motion.div>

      {/* Model cards */}
      <div className="space-y-5">
        {c.models.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.45, delay: i * 0.04, ease: [0.23, 1, 0.32, 1] }}
            className="grad-card p-6 sm:p-8"
          >
            {/* Card header */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-gold/12 border border-brand-gold/25
                              flex items-center justify-center shrink-0">
                <m.icon size={22} className="text-brand-gold" />
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-widest text-brand-gold">
                  {m.tag}
                </div>
                <h3 className="font-display font-semibold text-xl sm:text-2xl text-cream">
                  {m.name}
                </h3>
              </div>
            </div>

            {/* Fields */}
            <div className="mt-5 space-y-4">
              <Field label={c.labelDoes}>{m.does}</Field>
              <Field label={c.labelApproach}>{m.approach}</Field>
              <Field label={c.labelValidation}>{m.validation}</Field>
            </div>

            {/* Honest limit — distinct muted panel */}
            <div className="mt-5 warm-panel rounded-2xl p-4 flex items-start gap-3">
              <Info size={15} className="text-sage shrink-0 mt-0.5" />
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-widest text-sage">
                  {c.labelLimit}
                </div>
                <p className="mt-1 text-sm leading-relaxed text-cream-dim">{m.limit}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* How they work together */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="grad-card p-6 sm:p-8"
      >
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-sage/12 border border-sage/25
                          flex items-center justify-center shrink-0">
            <Layers size={20} className="text-sage" />
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-widest text-sage">
              {c.togetherTag}
            </div>
            <h3 className="font-display font-semibold text-xl text-cream">
              {c.togetherTitle}
            </h3>
          </div>
        </div>
        <p className="mt-4 text-sm sm:text-base leading-relaxed text-cream-dim">
          {c.togetherBody}
        </p>
      </motion.div>

      {/* What we don't claim */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="rounded-[1.5rem] p-6 sm:p-8 border border-brand-gold/25
                   bg-brand-gold/[0.06]"
      >
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-brand-gold/15 border border-brand-gold/30
                          flex items-center justify-center shrink-0">
            <Scale size={20} className="text-brand-gold" />
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-widest text-brand-gold">
              {c.claimTag}
            </div>
            <h3 className="font-display font-semibold text-xl text-cream">
              {c.claimTitle}
            </h3>
          </div>
        </div>
        <p className="mt-4 text-sm sm:text-base leading-relaxed text-cream-dim">
          {c.claimBody}
        </p>
      </motion.div>

    </div>
  );
}
