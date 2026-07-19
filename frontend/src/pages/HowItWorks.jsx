import { useLang } from "../i18n/LanguageContext";
import { motion } from "framer-motion";
import {
  Database, Cpu, ScrollText,
  Sparkles, ShieldCheck, TrendingUp, Calculator,
  ArrowRight, Info,
} from "lucide-react";

/* ── Bilingual content ───────────────────────────────────────── */
const COPY = {
  en: {
    lead: "DataCore plugs into a bank's own systems and turns raw SME activity into decisions a credit officer can actually defend. Here's what happens, concretely.",

    phases: [
      {
        icon: Database,
        tag: "Phase 1",
        title: "Data Connection",
        body: "The bank connects DataCore to its existing SME customer data through an API. There's no SME upload and no forms to fill in. DataCore reads transaction history, bank statements, and any available live POS feeds directly from the bank's own systems — the business never has to prepare paperwork it was never built to produce.",
        points: [
          "Connects via API to the bank's existing SME records",
          "Reads transaction history and bank statements directly",
          "Ingests live POS feeds where the bank already has them",
        ],
      },
      {
        icon: Cpu,
        tag: "Phase 2",
        title: "Live Analysis",
        body: "Four AI models process the connected data continuously — not once at application time, but every time new activity arrives.",
        models: [
          { icon: Sparkles,   name: "Behavioral classification",
            text: "Groups the business by its actual transaction patterns — rhythm, ticket size, timing — rather than an industry label." },
          { icon: ShieldCheck, name: "Fraud detection",
            text: "Trains a per-business model to catch anomalies specific to that business, measured against its own baseline instead of generic rules." },
          { icon: TrendingUp,  name: "Revenue forecasting",
            text: "Predicts the next 30 days of revenue with Saudi weekend and seasonal patterns built into the model." },
          { icon: Calculator,  name: "Expense estimation",
            text: "Derives the cost structure from observed behavior, so a usable margin appears with no accounting documents needed." },
        ],
      },
      {
        icon: ScrollText,
        tag: "Phase 3",
        title: "Explainable Decisions",
        body: "Every output is a decision with a reason attached. The bank doesn't just see \"approved\" or \"flagged\" — it sees the exact evidence behind it: which transaction triggered a fraud flag, why a business was placed in a specific archetype, and what drives the recommended credit limit. Credit officers stay in control of the call; DataCore surfaces the intelligence they act on.",
        points: [
          "Each flag links back to the specific transaction that caused it",
          "Each classification shows the pattern that drove it",
          "Each limit recommendation shows what it's based on",
        ],
      },
    ],

    note: "New businesses with no history yet start on the Two-Track System: a salary-secured bridge loan assessed against the SAMA debt-burden cap, which hands over to live-data scoring as real transactions accumulate.",
  },

  ar: {
    lead: "يتصل DataCore بأنظمة البنك نفسها ويحوّل نشاط المنشآت الخام إلى قرارات يستطيع موظف الائتمان الدفاع عنها فعلاً. إليك ما يحدث، بشكل ملموس.",

    phases: [
      {
        icon: Database,
        tag: "المرحلة ١",
        title: "ربط البيانات",
        body: "يربط البنك DataCore ببيانات عملائه من المنشآت الصغيرة عبر واجهة برمجية. لا رفع من المنشأة ولا نماذج تُملأ. يقرأ DataCore تاريخ المعاملات وكشوف الحساب وأي بيانات نقاط بيع حية متاحة مباشرةً من أنظمة البنك — دون أن تُعدّ المنشأة أوراقاً لم تُصمَّم لإنتاجها.",
        points: [
          "يتصل عبر واجهة برمجية بسجلات المنشآت لدى البنك",
          "يقرأ تاريخ المعاملات وكشوف الحساب مباشرة",
          "يستوعب بيانات نقاط البيع الحية حيثما توفّرت لدى البنك",
        ],
      },
      {
        icon: Cpu,
        tag: "المرحلة ٢",
        title: "التحليل الحي",
        body: "أربعة نماذج ذكاء تعالج البيانات المتصلة باستمرار — لا مرة واحدة عند التقديم، بل مع كل نشاط جديد يصل.",
        models: [
          { icon: Sparkles,   name: "التصنيف السلوكي",
            text: "يجمّع المنشأة حسب أنماط معاملاتها الفعلية — الإيقاع وحجم الفاتورة والتوقيت — لا حسب تصنيف قطاعها." },
          { icon: ShieldCheck, name: "كشف الاحتيال",
            text: "يدرّب نموذجاً لكل منشأة لالتقاط الشذوذات الخاصة بها، مقارنةً بقاعدتها هي لا بقواعد عامة." },
          { icon: TrendingUp,  name: "توقّع الإيرادات",
            text: "يتنبأ بإيرادات الـ ٣٠ يوماً القادمة مع أنماط نهاية الأسبوع والمواسم السعودية المدمجة في النموذج." },
          { icon: Calculator,  name: "تقدير المصاريف",
            text: "يستنتج هيكل التكلفة من السلوك المرصود، فيظهر هامش قابل للاستخدام دون أي مستندات محاسبية." },
        ],
      },
      {
        icon: ScrollText,
        tag: "المرحلة ٣",
        title: "قرارات قابلة للتفسير",
        body: "كل مخرج قرارٌ مرفق بسبب. لا يرى البنك «موافق» أو «مُعلَّم» فحسب — بل يرى الدليل الدقيق وراءه: أي معاملة أثارت تنبيه الاحتيال، ولماذا صُنِّفت المنشأة في نمط بعينه، وما الذي يحرّك الحد الائتماني المقترح. يبقى موظفو الائتمان مسيطرين على القرار؛ وDataCore يوفّر الذكاء الذي يبنون عليه.",
        points: [
          "كل تنبيه يعود إلى المعاملة المحددة التي سببته",
          "كل تصنيف يُظهر النمط الذي قاده",
          "كل حد مقترح يُظهر ما يستند إليه",
        ],
      },
    ],

    note: "المنشآت الجديدة بلا تاريخ تبدأ على النظام ثنائي المسار: قرض جسر مضمون بالراتب يُقيَّم مقابل حد عبء الدين لدى ساما، ثم يُسلَّم إلى التقييم بالبيانات الحية مع تراكم المعاملات الحقيقية.",
  },
};

/* ── Page ────────────────────────────────────────────────────── */
export default function HowItWorks() {
  const { lang, isRTL } = useLang();
  const c = COPY[lang];

  return (
    <div className="space-y-6 max-w-3xl">

      {/* Lead-in */}
      <motion.p
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="text-base sm:text-lg leading-relaxed text-cream-dim"
      >
        {c.lead}
      </motion.p>

      {/* Phases */}
      <div className="space-y-5">
        {c.phases.map((p, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.45, delay: i * 0.05, ease: [0.23, 1, 0.32, 1] }}
            className="grad-card p-6 sm:p-8"
          >
            {/* Header */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-gold/12 border border-brand-gold/25
                              flex items-center justify-center shrink-0">
                <p.icon size={22} className="text-brand-gold" />
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-widest text-brand-gold">
                  {p.tag}
                </div>
                <h2 className="font-display font-semibold text-xl sm:text-2xl text-cream">
                  {p.title}
                </h2>
              </div>
            </div>

            {/* Body */}
            <p className="mt-5 text-sm sm:text-base leading-relaxed text-cream-dim">
              {p.body}
            </p>

            {/* Model breakdown (Phase 2) */}
            {p.models && (
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {p.models.map((m, j) => (
                  <div key={j}
                    className="rounded-2xl bg-surface-dark/50 border border-surface-border
                               p-4 flex gap-3">
                    <div className="w-9 h-9 rounded-xl bg-sage/12 border border-sage/25
                                    flex items-center justify-center shrink-0">
                      <m.icon size={17} className="text-sage" />
                    </div>
                    <div>
                      <div className="font-display font-semibold text-sm text-cream">
                        {m.name}
                      </div>
                      <div className="mt-1 text-xs leading-relaxed text-cream-dim">
                        {m.text}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Point list (Phases 1 & 3) */}
            {p.points && (
              <ul className="mt-5 space-y-2.5">
                {p.points.map((pt, j) => (
                  <li key={j} className="flex items-start gap-2.5 text-sm text-cream">
                    <ArrowRight
                      size={15}
                      className={`text-brand-gold shrink-0 mt-0.5 ${isRTL ? "rotate-180" : ""}`} />
                    {pt}
                  </li>
                ))}
              </ul>
            )}
          </motion.div>
        ))}
      </div>

      {/* Honest note about new businesses */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="warm-panel rounded-2xl p-5 flex items-start gap-3"
      >
        <Info size={16} className="text-brand-gold shrink-0 mt-0.5" />
        <p className="text-sm leading-relaxed text-cream-dim">{c.note}</p>
      </motion.div>

    </div>
  );
}
