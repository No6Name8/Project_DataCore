import { useState } from "react";
import { useLang } from "../i18n/LanguageContext";
import { assessDBR, getBusinessProfile } from "../services/api";
import {
  Sprout, Calculator, Building2,
  CheckCircle, XCircle, ArrowRight,
  ArrowLeft, Loader2, TrendingUp,
  ShieldCheck, AlertCircle, Info,
} from "lucide-react";

const fmtFull = (n) => new Intl.NumberFormat("en-SA").format(Math.round(n));

// ── Input ─────────────────────────────────────────────────────
function Field({ label, value, onChange, type = "number", min, max, step, hint }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-400">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        min={min} max={max} step={step}
        className="w-full bg-surface-dark border border-surface-border
                   rounded-lg px-3 py-2 text-sm text-white
                   focus:outline-none focus:border-brand-gold
                   transition-colors placeholder-gray-600"
      />
      {hint && <p className="text-xs text-gray-600">{hint}</p>}
    </div>
  );
}

// ── Select ────────────────────────────────────────────────────
function SelectField({ label, value, onChange, options }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-400">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-surface-dark border border-surface-border
                   rounded-lg px-3 py-2 text-sm text-white
                   focus:outline-none focus:border-brand-gold transition-colors"
      >
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

// ── Toggle ────────────────────────────────────────────────────
function ToggleField({ label, value, onChange, hint }) {
  return (
    <div className="flex items-center justify-between py-1">
      <div>
        <div className="text-xs font-medium text-gray-400">{label}</div>
        {hint && <div className="text-xs text-gray-600">{hint}</div>}
      </div>
      <button
        onClick={() => onChange(!value)}
        className={`w-11 h-6 rounded-full transition-all relative shrink-0
                    ${value ? "bg-brand-gold" : "bg-surface-border"}`}
      >
        <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white
                         shadow transition-all
                         ${value ? "left-5" : "left-0.5"}`} />
      </button>
    </div>
  );
}

// ── DBR Gauge ─────────────────────────────────────────────────
function DBRGauge({ ratio }) {
  const pct     = Math.min(ratio / 0.6, 1) * 100;
  const limitX  = (0.33 / 0.6) * 100;
  const barColor =
    ratio <= 0.33              ? "bg-status-green" :
    ratio <= 0.38              ? "bg-status-yellow" :
                                 "bg-status-red";
  return (
    <div className="space-y-1">
      <div className="relative h-3 bg-surface-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute top-0 h-full w-0.5 bg-white/60"
          style={{ left: `${limitX}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>0%</span>
        <span className="text-white/60">SAMA 33%</span>
        <span>60%</span>
      </div>
    </div>
  );
}

// ── DBR Calculator ────────────────────────────────────────────
function DBRCalculator({ t, isRTL }) {
  const Arrow = isRTL ? ArrowLeft : ArrowRight;

  const [form, setForm] = useState({
    salary: 15000, obligations: 2000, loan: 50000, term: 24,
  });
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const set    = key => val => setForm(f => ({ ...f, [key]: Number(val) }));

  const calculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await assessDBR({
        monthly_salary:       form.salary,
        existing_obligations: form.obligations,
        requested_loan:       form.loan,
        loan_term_months:     form.term,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card rounded-xl p-6 space-y-5">

      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-brand-gold/10 flex items-center justify-center">
          <Calculator size={18} className="text-brand-gold" />
        </div>
        <div>
          <div className="font-semibold text-white text-sm">{t.salaryBacked}</div>
          <div className="text-xs text-gray-400">{t.samaLimit}</div>
        </div>
      </div>

      <div className="space-y-3">
        <Field
          label={`${t.yourSalary} (SAR)`}
          value={form.salary}
          onChange={set("salary")}
          min={3000} step={500}
          hint={isRTL ? "راتبك الشهري الصافي" : "Your monthly net salary"}
        />
        <Field
          label={`${t.existingLoans} (SAR)`}
          value={form.obligations}
          onChange={set("obligations")}
          min={0} step={100}
          hint={isRTL ? "أقساط القروض القائمة" : "Existing monthly loan payments"}
        />
        <Field
          label={`${t.loanAmount} (SAR)`}
          value={form.loan}
          onChange={set("loan")}
          min={5000} step={1000}
          hint={isRTL ? "مبلغ القرض الأولي المطلوب" : "Seed loan amount requested"}
        />
        <Field
          label={t.loanTerm}
          value={form.term}
          onChange={set("term")}
          min={6} max={60} step={6}
          hint={isRTL ? "مدة السداد بالأشهر" : "Repayment period in months"}
        />
      </div>

      <button
        onClick={calculate}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2
                   bg-brand-gold hover:bg-brand-goldLight
                   disabled:opacity-50 disabled:cursor-not-allowed
                   text-brand-blueDark font-semibold text-sm
                   py-3 rounded-xl transition-all"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Calculator size={16} />}
        {t.calculateDBR}
      </button>

      {error && (
        <div className="flex items-center gap-2 text-status-red text-xs p-3
                        rounded-lg bg-status-red/10 border border-status-red/30">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {result && (
        <div className={`space-y-4 p-4 rounded-xl border
                         ${result.approved
                           ? "bg-status-green/5 border-status-green/30"
                           : "bg-status-red/5   border-status-red/30"}`}>

          <div className="flex items-center gap-2">
            {result.approved
              ? <CheckCircle size={18} className="text-status-green" />
              : <XCircle     size={18} className="text-status-red" />}
            <span className={`font-bold text-sm
                              ${result.approved ? "text-status-green" : "text-status-red"}`}>
              {result.approved ? t.approved : t.denied}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">{t.dbrRatio}</span>
              <span className={`font-bold ${result.approved ? "text-status-green" : "text-status-red"}`}>
                {(result.dbr_ratio * 100).toFixed(1)}%
              </span>
            </div>
            <DBRGauge ratio={result.dbr_ratio} />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-0.5">
              <div className="text-gray-400">{t.monthlyPayment}</div>
              <div className="text-white font-medium">
                SAR {fmtFull(result.monthly_payment)}
              </div>
            </div>
            <div className="space-y-0.5">
              <div className="text-gray-400">
                {result.approved ? t.loanAmount : t.maxEligible}
              </div>
              <div className={`font-medium ${result.approved ? "text-status-green" : "text-status-yellow"}`}>
                SAR {fmtFull(result.approved
                  ? result.requested_loan_sar
                  : result.max_eligible_loan_sar ?? 0)}
              </div>
            </div>
          </div>

          {result.reason && (
            <div className="text-xs text-gray-400 flex items-start gap-1.5">
              <Info size={12} className="shrink-0 mt-0.5" />
              {result.reason}
            </div>
          )}

          {result.approved && (
            <div className="flex items-start gap-2 p-3 rounded-lg
                            bg-brand-blue/10 border border-brand-blue/30 text-xs text-gray-300">
              <ShieldCheck size={14} className="text-brand-blueLight shrink-0 mt-0.5" />
              {isRTL
                ? "سيتم خصم الأقساط تلقائياً من راتبك. رأس مال البنك محمي بالكامل."
                : "Installments will be deducted automatically from your salary. Bank capital is fully protected."}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Business Intake ───────────────────────────────────────────
function BusinessIntake({ t, isRTL }) {
  const [form, setForm] = useState({
    typical_ticket_sar:       50,
    expected_daily_customers: 30,
    operating_hours_per_day:  10,
    is_consumer_facing:       true,
    sells_high_value_items:   false,
    expected_payment_mix:     "mixed",
    operates_late_night:      false,
    business_days_per_week:   6,
    holds_physical_inventory: false,
  });
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const set    = key => val => setForm(f => ({ ...f, [key]: val }));
  const setNum = key => val => setForm(f => ({ ...f, [key]: Number(val) }));

  const assess = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getBusinessProfile({ ...form });
      setResult(res.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const RISK_BADGE = {
    low:    "text-status-green  bg-status-green/10  border-status-green/30",
    medium: "text-status-yellow bg-status-yellow/10 border-status-yellow/30",
    high:   "text-status-red    bg-status-red/10    border-status-red/30",
  };

  return (
    <div className="glass-card rounded-xl p-6 space-y-5">

      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-brand-blue/20 flex items-center justify-center">
          <Building2 size={18} className="text-brand-blueLight" />
        </div>
        <div>
          <div className="font-semibold text-white text-sm">
            {isRTL ? "تقييم المشروع الجديد" : "New Business Profile"}
          </div>
          <div className="text-xs text-gray-400">
            {isRTL ? "صنّف مشروعك قبل إطلاقه" : "Classify your business before launch"}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <Field
          label={isRTL ? "متوسط قيمة الفاتورة (SAR)" : "Avg Ticket Value (SAR)"}
          value={form.typical_ticket_sar}
          onChange={setNum("typical_ticket_sar")}
          min={1} step={10}
        />
        <Field
          label={isRTL ? "عدد العملاء المتوقع يومياً" : "Expected Daily Customers"}
          value={form.expected_daily_customers}
          onChange={setNum("expected_daily_customers")}
          min={1}
        />
        <Field
          label={isRTL ? "ساعات العمل اليومية" : "Daily Operating Hours"}
          value={form.operating_hours_per_day}
          onChange={setNum("operating_hours_per_day")}
          min={1} max={24}
        />
        <Field
          label={isRTL ? "أيام العمل أسبوعياً" : "Business Days Per Week"}
          value={form.business_days_per_week}
          onChange={setNum("business_days_per_week")}
          min={1} max={7}
        />
        <SelectField
          label={isRTL ? "طريقة الدفع الأساسية" : "Primary Payment Method"}
          value={form.expected_payment_mix}
          onChange={set("expected_payment_mix")}
          options={[
            { value: "mostly_cash",    label: isRTL ? "نقدي بشكل رئيسي" : "Mostly Cash" },
            { value: "mixed",          label: isRTL ? "مختلط"            : "Mixed" },
            { value: "mostly_digital", label: isRTL ? "رقمي بشكل رئيسي" : "Mostly Digital" },
          ]}
        />
        <div className="space-y-2 pt-1 border-t border-surface-border">
          <ToggleField
            label={isRTL ? "موجه للمستهلكين (B2C)" : "Consumer-Facing (B2C)"}
            value={form.is_consumer_facing}
            onChange={set("is_consumer_facing")}
          />
          <ToggleField
            label={isRTL ? "منتجات عالية القيمة (+10,000 SAR)" : "High-Value Items (+10K SAR)"}
            value={form.sells_high_value_items}
            onChange={set("sells_high_value_items")}
          />
          <ToggleField
            label={isRTL ? "يعمل بعد 11 مساءً" : "Late Night Operations (after 11PM)"}
            value={form.operates_late_night}
            onChange={set("operates_late_night")}
          />
          <ToggleField
            label={isRTL ? "يحمل مخزوناً مادياً" : "Holds Physical Inventory"}
            value={form.holds_physical_inventory}
            onChange={set("holds_physical_inventory")}
            hint={isRTL
              ? "سيارات، إلكترونيات، ملابس، أدوية..."
              : "Vehicles, electronics, clothing, pharma..."}
          />
        </div>
      </div>

      <button
        onClick={assess}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2
                   bg-brand-blue hover:bg-brand-blueLight
                   disabled:opacity-50 disabled:cursor-not-allowed
                   text-white font-semibold text-sm
                   py-3 rounded-xl transition-all"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Sprout size={16} />}
        {isRTL ? "تحليل المشروع" : "Analyse Business"}
      </button>

      {error && (
        <div className="flex items-center gap-2 text-status-red text-xs p-3
                        rounded-lg bg-status-red/10 border border-status-red/30">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4 p-4 rounded-xl border border-surface-border bg-surface-dark">

          <div className="space-y-1">
            <div className="text-xs text-gray-400">
              {isRTL ? "نوع المشروع المكتشف" : "Detected Business Archetype"}
            </div>
            <div className="text-sm font-medium text-brand-gold">
              {result.archetype_description}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>{isRTL ? "ثقة:" : "Confidence:"} {((result.confidence ?? 0) * 100).toFixed(0)}%</span>
              <span>•</span>
              <span>{isRTL ? "المصدر:" : "Source:"} {result.refinement_status}</span>
            </div>
          </div>

          <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-gold rounded-full transition-all duration-700"
              style={{ width: `${(result.confidence ?? 0) * 100}%` }}
            />
          </div>

          {result.expense_estimate && (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-0.5">
                <div className="text-gray-400">
                  {isRTL ? "نسبة المصاريف المتوقعة" : "Est. Expense Ratio"}
                </div>
                <div className="text-white font-bold text-base">
                  {((result.expense_estimate.total_expense_ratio ?? 0) * 100).toFixed(1)}%
                </div>
              </div>
              <div className="space-y-0.5">
                <div className="text-gray-400">
                  {isRTL ? "هامش الربح المتوقع" : "Est. Net Margin"}
                </div>
                <div className="text-status-green font-bold text-base">
                  {((result.expense_estimate.net_margin_estimate ?? 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {result.preliminary_credit_profile && (
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg
                             border text-xs font-medium
                             ${RISK_BADGE[result.preliminary_credit_profile.risk_indication]
                               ?? RISK_BADGE.medium}`}>
              <TrendingUp size={13} />
              {isRTL ? "مؤشر المخاطر الأولي: " : "Preliminary Risk: "}
              {result.preliminary_credit_profile.risk_indication?.toUpperCase()}
            </div>
          )}

          <div className="flex items-start gap-1.5 text-xs text-gray-500">
            <Info size={12} className="shrink-0 mt-0.5" />
            {isRTL
              ? "هذا تقييم أولي. ربط بيانات نقاط البيع يرفع الدقة إلى 95%."
              : "Preliminary assessment. Connecting POS data raises accuracy to 95%."}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Pipeline Transition Explainer ─────────────────────────────
function PipelineExplainer({ isRTL }) {
  const steps = isRTL ? [
    { day: "يوم 0",  label: "نموذج الاستبيان",      sub: "تقييم أولي بالذكاء الاصطناعي",     conf: 40 },
    { day: "يوم 7",  label: "7 أيام بيانات حقيقية", sub: "دمج البيانات الحقيقية والمتوقعة",  conf: 55 },
    { day: "يوم 14", label: "14 يوم بيانات",         sub: "البيانات الحقيقية تتصدر",           conf: 72 },
    { day: "يوم 30", label: "مسار المنشآت الكامل",   sub: "تقييم DSCR كامل بالتاريخ الحقيقي", conf: 95 },
  ] : [
    { day: "Day 0",  label: "Intake Form",      sub: "AI preliminary assessment",      conf: 40 },
    { day: "Day 7",  label: "7 Days POS Data",  sub: "Hybrid real + predicted blend",  conf: 55 },
    { day: "Day 14", label: "14 Days POS Data", sub: "Real data takes over",           conf: 72 },
    { day: "Day 30", label: "Full SME Pipeline", sub: "Complete DSCR on real history", conf: 95 },
  ];

  return (
    <div className="glass-card rounded-xl p-6 space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp size={18} className="text-brand-gold" />
        <span className="font-semibold text-white text-sm">
          {isRTL
            ? "رحلة الانتقال: من الحاضنة إلى مسار المنشآت"
            : "Transition Journey: Incubator → SME Pipeline"}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {steps.map((s, i) => (
          <div key={i} className="space-y-2">
            {/* Step indicator + connector */}
            <div className="flex items-center gap-1">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center
                               text-xs font-bold shrink-0
                               ${i === 3
                                 ? "bg-brand-gold text-brand-blueDark"
                                 : "bg-brand-blue/30 text-brand-gold"}`}>
                {i + 1}
              </div>
              {i < 3 && (
                <div className="flex-1 h-0.5 bg-brand-blue/30" />
              )}
            </div>
            <div className="space-y-1">
              <div className="text-xs font-semibold text-brand-gold">{s.day}</div>
              <div className="text-xs text-white">{s.label}</div>
              <div className="text-xs text-gray-500">{s.sub}</div>
              <div className="h-1 bg-surface-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-gold/60 rounded-full transition-all duration-700"
                  style={{ width: `${s.conf}%` }}
                />
              </div>
              <div className="text-xs text-gray-500">{s.conf}% conf.</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────
export default function Incubator() {
  const { t, isRTL } = useLang();

  return (
    <div className="space-y-6">

      {/* Hero */}
      <div className="text-center space-y-2 py-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5
                        rounded-full border border-brand-gold/30
                        bg-brand-gold/10 text-brand-gold text-sm">
          <Sprout size={14} />
          {t.incubatorTitle}
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-white">
          {t.incubatorSubtitle}
        </h1>
        <p className="text-gray-400 text-sm max-w-xl mx-auto">
          {isRTL
            ? "لا تاريخ ائتماني؟ لا مشكلة. راتبك يضمن قرضك الأول."
            : "No credit history? No problem. Your salary secures your first loan."}
        </p>
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <DBRCalculator t={t} isRTL={isRTL} />
        <BusinessIntake t={t} isRTL={isRTL} />
      </div>

      {/* Pipeline explainer */}
      <PipelineExplainer isRTL={isRTL} />

    </div>
  );
}
