import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useLang } from "../i18n/LanguageContext";
import TopNav, { DataCoreMark } from "../components/TopNav";
import {
  ArrowRight, ArrowUpRight, Sparkles, ShieldCheck, TrendingUp, Wallet,
  Plug, Cpu, CircleCheck, Landmark, Database, Rocket, ScrollText,
  Mail, Building2, Users, Coffee,
} from "lucide-react";

/* ── Bilingual copy ──────────────────────────────────────────── */
const COPY = {
  en: {
    heroA: "See every business.",
    heroB: "Fund every future.",
    heroSub:
      "The AI lending engine that helps banks understand and serve every SME — not just the ones with clean paperwork.",
    seeDemo: "See the demo",
    contact: "Contact",

    problemTag: "The Missing Middle",
    problemTitle: "Banks know giants and individuals. SMEs fall in between.",
    problemBody:
      "Large corporations get relationship managers. Individuals get scoring models. But the small business — the café, the workshop, the minimarket — sits in a blind spot: too complex for a consumer score, too small for a corporate desk. So they get judged on paperwork they were never built to produce.",
    problemStats: [
      { k: "Understood by banks", v: "Big corporates" },
      { k: "Scored automatically", v: "Individuals" },
      { k: "Left in the middle", v: "SMEs" },
    ],

    solutionTag: "The Decision Engine",
    solutionTitle: "Four AI models. One decision engine.",
    solutionSub:
      "Each model reads a business the way a seasoned banker would — from how it actually behaves, day to day.",
    models: [
      { icon: Sparkles, name: "Behavioral Classifier",
        body: "Understands each business by how it actually operates — its rhythm, ticket size and cash patterns — not by its industry label." },
      { icon: ShieldCheck, name: "Fraud Detector",
        body: "One model per business, learning what's normal for that specific business, so anomalies surface the moment they appear." },
      { icon: TrendingUp, name: "Revenue Forecaster",
        body: "Predicts 30 days ahead with Saudi weekend and seasonal patterns built in — a limit that moves with the business." },
      { icon: Wallet, name: "Two-Track System",
        body: "Serves new businesses from Day 1 with salary-secured bridge lending, then hands over to live data as it arrives." },
    ],

    howTag: "How It Works",
    howTitle: "From raw activity to a fair decision — in three steps.",
    steps: [
      { icon: Plug, name: "Connect",
        body: "The business links its live POS and banking activity. No forms, no PDFs, no waiting." },
      { icon: Cpu, name: "Analyze",
        body: "The four models read behavior, forecast revenue, and watch for fraud in real time." },
      { icon: CircleCheck, name: "Decide",
        body: "A dynamic credit limit and fair rate come back in minutes — and keep updating as the business grows." },
    ],

    benefitsTag: "Why It Matters",
    benefitsTitle: "For the bank. For the SME. For Saudi Arabia.",
    benefits: [
      { icon: Landmark, name: "Lend Like You Know Them",
        body: "Replace static paperwork with living behavior. Approve confidently, price fairly, and see risk before it becomes loss." },
      { icon: Database, name: "Every SME, a Data Asset",
        body: "Each connected business turns into a continuously-scored, monitored relationship — not a one-time application in a drawer." },
      { icon: TrendingUp, name: "SMEs Grow, Banks Grow With Them",
        body: "Limits rise with real revenue. As small businesses expand, the bank's book compounds alongside them." },
    ],

    demoTag: "Live Demo",
    demoTitle: "See the engine make a real decision.",
    demoSub:
      "Explore the bank's portfolio dashboard, or step into the shoes of an SME owner watching their own numbers.",
    openDemo: "Open the live demo",

    founderTag: "About the Founder",
    founderName: "Abdullah Ali Alanazi",
    founderRole: "Prince Sultan University, Riyadh · Solo builder",
    founderBody:
      "DataCore is built end-to-end by a single founder — the models, the data engine, and the interface you're looking at. The goal is simple: give Saudi banks a way to see the businesses they've never quite been able to see, and give those businesses a fair shot at capital.",

    roadmapTag: "What's Next",
    roadmapTitle: "Direction, not promises.",
    roadmap: [
      { icon: Sparkles,   label: "Now",        what: "Validated prototype",
        detail: "Working prototype validated against real-world datasets. Ready for pilot conversations with Saudi banks." },
      { icon: Rocket,     label: "Next",       what: "Bank pilot",
        detail: "Pilot deployment with a Saudi bank as a decision support layer, running alongside existing lending workflows." },
      { icon: ScrollText, label: "After That", what: "Protect & expand",
        detail: "Patent filing with SAIP, academic publication, expanded portfolio-level monitoring, and partnerships with additional banks." },
      { icon: Landmark,   label: "Long Term",  what: "Regulated scale",
        detail: "SAMA sandbox approval, path from decision support to production lending, expansion across the GCC." },
    ],

    contactTag: "Get in Touch",
    contactTitle: "Let's put every business on the map.",
    contactBody:
      "For pilots, partnerships, or a walkthrough of the engine — reach out directly.",
    emailCta: "Email Abdullah",
    linkedinCta: "LinkedIn",

    footerRights: "© 2026 DataCore · Abdullah Ali Alanazi",
    footerGh: "GitHub",
  },
  ar: {
    heroA: "شاهد كل منشأة.",
    heroB: "موّل كل مستقبل.",
    heroSub:
      "محرك الإقراض الذكي الذي يساعد البنوك على فهم وخدمة كل منشأة صغيرة — وليس فقط أصحاب الأوراق المكتملة.",
    seeDemo: "شاهد العرض",
    contact: "تواصل معنا",

    problemTag: "الفجوة المفقودة",
    problemTitle: "البنوك تفهم الكبار والأفراد. المنشآت الصغيرة تقع بينهما.",
    problemBody:
      "الشركات الكبرى لديها مدراء علاقات، والأفراد لديهم نماذج تقييم. أمّا المنشأة الصغيرة — المقهى، الورشة، البقالة — فتقع في نقطة عمياء: أعقد من تقييم فردي، وأصغر من مكتب الشركات. فتُحكَم بأوراق لم تُصمَّم لإنتاجها.",
    problemStats: [
      { k: "تفهمها البنوك", v: "الشركات الكبرى" },
      { k: "تُقيَّم آلياً", v: "الأفراد" },
      { k: "متروكة في المنتصف", v: "المنشآت الصغيرة" },
    ],

    solutionTag: "محرك القرار",
    solutionTitle: "أربعة نماذج ذكاء. محرك قرار واحد.",
    solutionSub:
      "كل نموذج يقرأ المنشأة كما يفعل مصرفي محنّك — من سلوكها الفعلي، يوماً بيوم.",
    models: [
      { icon: Sparkles, name: "مصنّف السلوك",
        body: "يفهم كل منشأة من طريقة عملها الفعلية — إيقاعها وحجم فواتيرها وأنماط نقدها — لا من تصنيف قطاعها." },
      { icon: ShieldCheck, name: "كاشف الاحتيال",
        body: "نموذج لكل منشأة يتعلّم ما هو الطبيعي لها تحديداً، لتظهر الشذوذات لحظة حدوثها." },
      { icon: TrendingUp, name: "متنبّئ الإيرادات",
        body: "يتنبأ بـ ٣٠ يوماً قادمة مع أنماط نهاية الأسبوع والمواسم السعودية — حدٌّ يتحرك مع المنشأة." },
      { icon: Wallet, name: "النظام ثنائي المسار",
        body: "يخدم المنشآت الجديدة من اليوم الأول بتمويل مضمون بالراتب، ثم يسلّم للبيانات الحية عند توفرها." },
    ],

    howTag: "كيف يعمل",
    howTitle: "من النشاط الخام إلى قرار عادل — في ثلاث خطوات.",
    steps: [
      { icon: Plug, name: "اربط",
        body: "تربط المنشأة نقاط بيعها ونشاطها البنكي الحي. بلا نماذج، بلا ملفات، بلا انتظار." },
      { icon: Cpu, name: "حلّل",
        body: "تقرأ النماذج الأربعة السلوك، وتتنبأ بالإيرادات، وتراقب الاحتيال آنياً." },
      { icon: CircleCheck, name: "قرّر",
        body: "يعود حدٌّ ائتماني ديناميكي وسعر عادل خلال دقائق — ويستمر بالتحدّث مع نمو المنشأة." },
    ],

    benefitsTag: "لماذا يهم",
    benefitsTitle: "للبنك. للمنشأة. للسعودية.",
    benefits: [
      { icon: Landmark, name: "أقرِض وكأنك تعرفهم",
        body: "استبدل الأوراق الثابتة بسلوك حيّ. وافق بثقة، وسعّر بعدل، وارَ المخاطر قبل أن تصبح خسارة." },
      { icon: Database, name: "كل منشأة أصلٌ من البيانات",
        body: "كل منشأة مرتبطة تتحول إلى علاقة تُقيَّم وتُراقَب باستمرار — لا طلباً لمرة واحدة في الدرج." },
      { icon: TrendingUp, name: "تنمو المنشآت وتنمو البنوك معها",
        body: "ترتفع الحدود مع الإيرادات الحقيقية. ومع توسّع المنشآت، تتضاعف محفظة البنك بجانبها." },
    ],

    demoTag: "عرض مباشر",
    demoTitle: "شاهد المحرك يتخذ قراراً حقيقياً.",
    demoSub:
      "استكشف لوحة محفظة البنك، أو ضع نفسك مكان صاحب منشأة يتابع أرقامه بنفسه.",
    openDemo: "افتح العرض المباشر",

    founderTag: "عن المؤسس",
    founderName: "عبدالله علي العنزي",
    founderRole: "جامعة الأمير سلطان، الرياض · مطوّر منفرد",
    founderBody:
      "DataCore مبنيّ بالكامل بيد مؤسس واحد — النماذج، ومحرك البيانات، والواجهة التي تراها. الهدف بسيط: منح البنوك السعودية وسيلة لرؤية المنشآت التي لم تستطع رؤيتها، ومنح تلك المنشآت فرصة عادلة للتمويل.",

    roadmapTag: "ما القادم",
    roadmapTitle: "اتجاه، لا وعود.",
    roadmap: [
      { icon: Sparkles,   label: "الآن",        what: "نموذج مُتحقَّق منه",
        detail: "نموذج أوّلي عامل تم التحقق منه مقابل بيانات واقعية. جاهز لمحادثات التجربة مع البنوك السعودية." },
      { icon: Rocket,     label: "التالي",      what: "تجربة مع بنك",
        detail: "نشر تجريبي مع بنك سعودي كطبقة دعم قرار، تعمل بجانب مسارات الإقراض القائمة." },
      { icon: ScrollText, label: "بعد ذلك",     what: "حماية وتوسّع",
        detail: "تسجيل براءة اختراع مع SAIP، ونشر علمي، ومراقبة موسّعة على مستوى المحفظة، وشراكات مع بنوك إضافية." },
      { icon: Landmark,   label: "المدى البعيد", what: "توسّع منظَّم",
        detail: "موافقة بيئة ساما التجريبية، ومسار من دعم القرار إلى الإقراض الإنتاجي، والتوسّع عبر دول الخليج." },
    ],

    contactTag: "تواصل",
    contactTitle: "لنضع كل منشأة على الخريطة.",
    contactBody:
      "للتجارب أو الشراكات أو جولة في المحرك — تواصل مباشرة.",
    emailCta: "راسل عبدالله",
    linkedinCta: "LinkedIn",

    footerRights: "© ٢٠٢٦ DataCore · عبدالله علي العنزي",
    footerGh: "GitHub",
  },
};

const GITHUB_URL = "https://github.com/";
const LINKEDIN_URL = "https://linkedin.com/in/abdullah-alanazi";
const EMAIL = "abud2754@gmail.com";

/* Distinct accent per roadmap phase — momentum from bright "Now" to muted "Long Term" */
const PHASE_ACCENTS = [
  { node: "bg-brand-gold border border-brand-gold", nodeIcon: "text-ink",
    pill: "bg-brand-gold text-ink" },
  { node: "bg-brand-gold/12 border border-brand-gold/35", nodeIcon: "text-brand-gold",
    pill: "bg-brand-gold/12 text-brand-gold border border-brand-gold/35" },
  { node: "bg-sage/12 border border-sage/35", nodeIcon: "text-sage",
    pill: "bg-sage/12 text-sage border border-sage/30" },
  { node: "bg-white/5 border border-white/12", nodeIcon: "text-cream-dim",
    pill: "bg-white/5 text-cream-dim border border-white/12" },
];

/* ── Motion helper ───────────────────────────────────────────── */
const reveal = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: [0.23, 1, 0.32, 1] },
  }),
};

function Reveal({ children, i = 0, className = "" }) {
  return (
    <motion.div
      className={className}
      variants={reveal}
      custom={i}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.25 }}
    >
      {children}
    </motion.div>
  );
}

function Tag({ children }) {
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                     text-xs font-medium tracking-wide uppercase
                     text-brand-gold bg-brand-gold/10 border border-brand-gold/20">
      <span className="w-1.5 h-1.5 rounded-full bg-brand-gold" />
      {children}
    </span>
  );
}

/* ── Page ────────────────────────────────────────────────────── */
export default function Marketing() {
  const { lang, isRTL } = useLang();
  const c = COPY[lang];

  return (
    <div className="min-h-dvh bg-surface-dark text-cream" dir={isRTL ? "rtl" : "ltr"}>
      <TopNav />

      {/* ── 1. Hero ─────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="hero-glow" />
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6
                        pt-24 pb-20 sm:pt-32 sm:pb-28 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}>
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full
                             text-xs sm:text-sm font-medium mb-8
                             text-cream-dim bg-white/5 border border-white/10">
              <Sparkles size={14} className="text-brand-gold" />
              {lang === "ar" ? "محرك الإقراض الذكي للمنشآت" : "AI lending engine for SMEs"}
            </span>
          </motion.div>

          <h1 className="font-display font-bold leading-[1.05]
                         text-[2.75rem] sm:text-6xl lg:text-7xl">
            <motion.span
              className="block text-cream"
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.05, ease: [0.23, 1, 0.32, 1] }}>
              {c.heroA}
            </motion.span>
            <motion.span
              className="block text-cream-gradient"
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15, ease: [0.23, 1, 0.32, 1] }}>
              {c.heroB}
            </motion.span>
          </h1>

          <motion.p
            className="mt-7 mx-auto max-w-2xl text-lg sm:text-xl leading-relaxed text-cream-dim"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.25, ease: [0.23, 1, 0.32, 1] }}>
            {c.heroSub}
          </motion.p>

          <motion.div
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.35, ease: [0.23, 1, 0.32, 1] }}>
            <Link to="/demo"
              className="cta-gold inline-flex items-center gap-2 px-7 py-3.5 text-base w-full sm:w-auto justify-center">
              {c.seeDemo}
              <ArrowRight size={18} className={isRTL ? "rotate-180" : ""} />
            </Link>
            <a href="#contact"
              className="cta-ghost inline-flex items-center gap-2 px-7 py-3.5 text-base w-full sm:w-auto justify-center">
              {c.contact}
            </a>
          </motion.div>
        </div>
      </section>

      {/* ── 2. The Missing Middle ───────────────────────────── */}
      <Section>
        <Reveal><Tag>{c.problemTag}</Tag></Reveal>
        <Reveal i={1}>
          <h2 className="mt-5 font-display font-bold text-3xl sm:text-4xl lg:text-5xl
                         text-cream max-w-3xl leading-tight">
            {c.problemTitle}
          </h2>
        </Reveal>
        <Reveal i={2}>
          <p className="mt-6 max-w-2xl text-base sm:text-lg leading-relaxed text-cream-dim">
            {c.problemBody}
          </p>
        </Reveal>
        <div className="mt-12 grid gap-4 sm:grid-cols-3">
          {c.problemStats.map((s, i) => (
            <Reveal key={i} i={i}>
              <div className={`warm-panel rounded-2xl p-6 h-full
                               ${i === 2 ? "ring-1 ring-brand-gold/40" : ""}`}>
                <div className={`text-xs uppercase tracking-wide
                                 ${i === 2 ? "text-brand-gold" : "text-cream-dim"}`}>
                  {s.k}
                </div>
                <div className="mt-2 font-display font-semibold text-xl sm:text-2xl text-cream">
                  {s.v}
                </div>
                {i === 2 && (
                  <div className="mt-3 inline-flex items-center gap-1.5 text-xs text-brand-gold">
                    <ArrowUpRight size={13} className={isRTL ? "-scale-x-100" : ""} />
                    {lang === "ar" ? "هنا يعمل DataCore" : "Where DataCore works"}
                  </div>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ── 3. Four AI Models ───────────────────────────────── */}
      <Section className="dot-grid">
        <div className="text-center">
          <Reveal><Tag>{c.solutionTag}</Tag></Reveal>
          <Reveal i={1}>
            <h2 className="mt-5 font-display font-bold text-3xl sm:text-4xl lg:text-5xl
                           text-cream mx-auto max-w-3xl leading-tight">
              {c.solutionTitle}
            </h2>
          </Reveal>
          <Reveal i={2}>
            <p className="mt-5 mx-auto max-w-2xl text-base sm:text-lg text-cream-dim">
              {c.solutionSub}
            </p>
          </Reveal>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2">
          {c.models.map((m, i) => (
            <Reveal key={i} i={i}>
              <div className="grad-card p-7 h-full flex flex-col">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-brand-gold/12
                                  border border-brand-gold/20
                                  flex items-center justify-center shrink-0">
                    <m.icon size={22} className="text-brand-gold" />
                  </div>
                  <h3 className="font-display font-semibold text-xl text-cream">
                    {m.name}
                  </h3>
                </div>
                <p className="mt-4 text-sm sm:text-base leading-relaxed text-cream-dim">
                  {m.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ── 4. How It Works ─────────────────────────────────── */}
      <Section>
        <div className="text-center">
          <Reveal><Tag>{c.howTag}</Tag></Reveal>
          <Reveal i={1}>
            <h2 className="mt-5 font-display font-bold text-3xl sm:text-4xl lg:text-5xl
                           text-cream mx-auto max-w-3xl leading-tight">
              {c.howTitle}
            </h2>
          </Reveal>
        </div>

        <div className="mt-14 grid gap-5 md:grid-cols-3 relative">
          {c.steps.map((s, i) => (
            <Reveal key={i} i={i}>
              <div className="warm-panel rounded-3xl p-8 h-full text-center md:text-start">
                <div className="flex items-center justify-between">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br
                                  from-brand-gold/25 to-sage/15
                                  border border-brand-gold/25
                                  flex items-center justify-center mx-auto md:mx-0">
                    <s.icon size={24} className="text-brand-gold" />
                  </div>
                  <span className="hidden md:block font-display font-bold text-5xl text-white/5">
                    0{i + 1}
                  </span>
                </div>
                <h3 className="mt-6 font-display font-semibold text-xl text-cream">
                  {s.name}
                </h3>
                <p className="mt-3 text-sm sm:text-base leading-relaxed text-cream-dim">
                  {s.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ── 5. Benefits ─────────────────────────────────────── */}
      <Section className="dot-grid">
        <div className="text-center">
          <Reveal><Tag>{c.benefitsTag}</Tag></Reveal>
          <Reveal i={1}>
            <h2 className="mt-5 font-display font-bold text-3xl sm:text-4xl lg:text-5xl
                           text-cream mx-auto max-w-3xl leading-tight">
              {c.benefitsTitle}
            </h2>
          </Reveal>
        </div>

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {c.benefits.map((b, i) => (
            <Reveal key={i} i={i}>
              <div className="grad-card p-8 h-full">
                <div className="w-12 h-12 rounded-2xl bg-sage/12 border border-sage/25
                                flex items-center justify-center">
                  <b.icon size={22} className="text-sage" />
                </div>
                <h3 className="mt-5 font-display font-semibold text-lg sm:text-xl text-cream">
                  {b.name}
                </h3>
                <p className="mt-3 text-sm sm:text-base leading-relaxed text-cream-dim">
                  {b.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ── 6. Live Demo Preview ────────────────────────────── */}
      <Section>
        <Reveal>
          <div className="relative overflow-hidden rounded-[2rem]
                          warm-panel p-8 sm:p-12 lg:p-16">
            <div className="hero-glow opacity-70" />
            <div className="relative grid lg:grid-cols-2 gap-10 items-center">
              <div>
                <Tag>{c.demoTag}</Tag>
                <h2 className="mt-5 font-display font-bold text-3xl sm:text-4xl
                               text-cream leading-tight">
                  {c.demoTitle}
                </h2>
                <p className="mt-5 text-base sm:text-lg text-cream-dim max-w-lg">
                  {c.demoSub}
                </p>
                <Link to="/demo"
                  className="cta-gold mt-8 inline-flex items-center gap-2 px-7 py-3.5 text-base">
                  {c.openDemo}
                  <ArrowRight size={18} className={isRTL ? "rotate-180" : ""} />
                </Link>
              </div>

              {/* Stylised dashboard mock */}
              <div className="relative">
                <div className="rounded-2xl bg-surface-card border border-surface-border
                                p-5 shadow-2xl">
                  <div className="flex items-center gap-2 mb-4">
                    <DataCoreMark size={22} />
                    <span className="font-display font-semibold text-sm text-cream">
                      DataCore
                    </span>
                    <span className="ms-auto inline-flex items-center gap-1.5 text-xs
                                     text-status-green">
                      <span className="w-1.5 h-1.5 rounded-full bg-status-green animate-pulse" />
                      Live
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { l: "DSCR", v: "2.14", c: "text-sage" },
                      { l: "Credit Limit", v: "SAR 180K", c: "text-brand-gold" },
                      { l: "Fraud", v: "Clean", c: "text-sage" },
                      { l: "Forecast", v: "+8.3%", c: "text-brand-gold" },
                    ].map((k, i) => (
                      <div key={i} className="rounded-xl bg-surface-dark/70 border
                                              border-surface-border p-3">
                        <div className="text-[10px] uppercase tracking-wide text-gray-500">
                          {k.l}
                        </div>
                        <div className={`mt-1 font-display font-bold text-lg ${k.c}`}>
                          {k.v}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 h-16 rounded-xl bg-surface-dark/70 border
                                  border-surface-border flex items-end gap-1 p-3">
                    {[40, 55, 48, 62, 58, 74, 70, 88].map((h, i) => (
                      <div key={i}
                        className="flex-1 rounded-sm bg-gradient-to-t from-brand-gold/30 to-brand-gold"
                        style={{ height: `${h}%` }} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </Section>

      {/* ── 7. About the Founder ────────────────────────────── */}
      <Section className="dot-grid">
        <Reveal>
          <div className="max-w-3xl mx-auto text-center">
            <Tag>{c.founderTag}</Tag>
            <div className="mt-8 flex flex-col items-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br
                              from-brand-gold to-brand-goldDark
                              flex items-center justify-center
                              font-display font-bold text-2xl text-ink shadow-lg">
                {isRTL ? "ع" : "AA"}
              </div>
              <h2 className="mt-5 font-display font-bold text-2xl sm:text-3xl text-cream">
                {c.founderName}
              </h2>
              <div className="mt-2 text-sm text-brand-gold">{c.founderRole}</div>
              <p className="mt-6 text-base sm:text-lg leading-relaxed text-cream-dim">
                {c.founderBody}
              </p>
            </div>
          </div>
        </Reveal>
      </Section>

      {/* ── 8. Roadmap ──────────────────────────────────────── */}
      <Section>
        <div className="text-center">
          <Reveal><Tag>{c.roadmapTag}</Tag></Reveal>
          <Reveal i={1}>
            <h2 className="mt-5 font-display font-bold text-3xl sm:text-4xl lg:text-5xl
                           text-cream mx-auto max-w-2xl leading-tight">
              {c.roadmapTitle}
            </h2>
          </Reveal>
        </div>

        <div className="mt-14">

          {/* Desktop node rail — a connecting line with a node per phase */}
          <div className="hidden md:block relative mb-7">
            <div className="absolute top-1/2 -translate-y-1/2 left-[12.5%] right-[12.5%]
                            h-0.5 bg-gradient-to-r from-brand-gold/50 via-sage/30 to-white/10" />
            <div className="relative grid grid-cols-4">
              {c.roadmap.map((r, i) => {
                const a = PHASE_ACCENTS[i];
                return (
                  <Reveal key={i} i={i} className="flex justify-center">
                    <div className={`w-14 h-14 rounded-full flex items-center justify-center
                                     ${a.node}`}>
                      <r.icon size={22} className={a.nodeIcon} />
                    </div>
                  </Reveal>
                );
              })}
            </div>
          </div>

          {/* Phase cards */}
          <div className="grid gap-5 md:grid-cols-4">
            {c.roadmap.map((r, i) => {
              const a = PHASE_ACCENTS[i];
              return (
                <Reveal key={i} i={i}>
                  <div className="warm-panel rounded-3xl p-6 h-full flex flex-col">
                    <div className="flex items-center gap-3">
                      {/* Icon shown inline on mobile (rail hidden there) */}
                      <div className={`md:hidden w-10 h-10 rounded-xl flex items-center
                                       justify-center shrink-0 ${a.node}`}>
                        <r.icon size={19} className={a.nodeIcon} />
                      </div>
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                                        text-xs font-semibold uppercase tracking-wide ${a.pill}`}>
                        {i === 0 && (
                          <span className="w-1.5 h-1.5 rounded-full bg-ink/70 animate-pulse" />
                        )}
                        {r.label}
                      </span>
                    </div>
                    <h3 className="mt-4 font-display font-semibold text-lg text-cream">
                      {r.what}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-cream-dim">
                      {r.detail}
                    </p>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </div>
      </Section>

      {/* ── 9. Contact ──────────────────────────────────────── */}
      <section id="contact" className="relative overflow-hidden py-24 sm:py-32">
        <div className="hero-glow" />
        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <Reveal><Tag>{c.contactTag}</Tag></Reveal>
          <Reveal i={1}>
            <h2 className="mt-5 font-display font-bold text-3xl sm:text-5xl
                           text-cream leading-tight">
              {c.contactTitle}
            </h2>
          </Reveal>
          <Reveal i={2}>
            <p className="mt-5 text-base sm:text-lg text-cream-dim">{c.contactBody}</p>
          </Reveal>
          <Reveal i={3}>
            <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3">
              <a href={`mailto:${EMAIL}`}
                className="cta-gold inline-flex items-center justify-center gap-2
                           px-7 py-3.5 text-base w-full sm:w-52">
                <Mail size={18} />
                {c.emailCta}
              </a>
              <a href={LINKEDIN_URL} target="_blank" rel="noopener noreferrer"
                className="cta-ghost inline-flex items-center justify-center gap-2
                           px-7 py-3.5 text-base w-full sm:w-52">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.35V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.07 2.07 0 110-4.14 2.07 2.07 0 010 4.14zM7.12 20.45H3.55V9h3.57v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.22.79 24 1.77 24h20.45c.98 0 1.78-.78 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z" />
                </svg>
                {c.linkedinCta}
              </a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── 10. Footer ──────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6
                        flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <DataCoreMark size={26} />
            <span className="font-display font-semibold text-sm text-cream">DataCore</span>
          </div>
          <div className="text-xs text-cream-dim">{c.footerRights}</div>
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer"
             className="inline-flex items-center gap-2 text-xs text-cream-dim
                        hover:text-brand-gold transition-colors">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
                       0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
                       -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
                       .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                       -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
                       1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
                       1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
                       1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            {c.footerGh}
          </a>
        </div>
      </footer>
    </div>
  );
}

/* Section shell — generous vertical rhythm, Tabby-style breathing room */
function Section({ children, className = "" }) {
  return (
    <section className={`relative py-20 sm:py-28 ${className}`}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6">{children}</div>
    </section>
  );
}
