import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useLang } from "../i18n/LanguageContext";
import { motion, AnimatePresence } from "framer-motion";
import { getDashboard, getForecast, assessDBR, getBusinessProfile, getPortfolioBusiness } from "../services/api";
import AnimatedNumber from "../components/AnimatedNumber";
import {
  Building2, Sprout, Activity, CreditCard,
  BarChart2, Zap, Shield, ShieldAlert, ShieldX,
  Leaf, TrendingUp,
  CheckCircle, XCircle, AlertTriangle,
  Loader2,
  AlertCircle, Info, ShieldCheck, Calculator
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";

// ── Constants ────────────────────────────────────────────────
const BUSINESSES = [
  { id: "cafe",       nameEn: "Qahwa Corner Cafe",   nameAr: "مقهى قهوة كورنر",     sector: "Food & Beverage" },
  { id: "minimarket", nameEn: "Baraka Minimarket",    nameAr: "مينيماركت بركة",       sector: "Retail" },
  { id: "laundromat", nameEn: "Al Noor Laundromat",  nameAr: "مغسلة النور",          sector: "Services" },
  { id: "realestate", nameEn: "Majd Real Estate",    nameAr: "مجد للعقارات",         sector: "Real Estate" },
  { id: "cardealer",  nameEn: "Rawabi Auto Gallery", nameAr: "معرض روابي للسيارات",  sector: "Automotive" },
  { id: "motorbike",  nameEn: "Saqr Motorbikes",     nameAr: "صقر للدراجات النارية", sector: "Automotive" },
];

// ── Helpers ──────────────────────────────────────────────────
const fmt = (n) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M`
  : n >= 1_000   ? `${(n / 1_000).toFixed(0)}K`
  : String(Math.round(n ?? 0));

const fmtFull = (n) =>
  new Intl.NumberFormat("en-SA").format(Math.round(n ?? 0));

const RISK_COLOR = {
  very_low: "text-status-green",
  low:      "text-status-green",
  medium:   "text-status-yellow",
  high:     "text-status-red",
  critical: "text-status-red",
};

// ── Health verdict ────────────────────────────────────────────
function getVerdict(dscr, fraud) {
  if (!dscr) return null;
  if (fraud?.approval_frozen)
    return { label: "Approval Frozen", labelAr: "الموافقة مجمدة",  color: "text-status-red",    bg: "bg-status-red/10 border-status-red/30",       icon: ShieldX };
  if (fraud?.overall_status === "flagged")
    return { label: "Under Review",    labelAr: "قيد المراجعة",    color: "text-status-yellow", bg: "bg-status-yellow/10 border-status-yellow/30",  icon: ShieldAlert };
  if (dscr.risk_tier === "critical")
    return { label: "High Risk",       labelAr: "مخاطر عالية",     color: "text-status-red",    bg: "bg-status-red/10 border-status-red/30",       icon: ShieldX };
  if (dscr.risk_tier === "high")
    return { label: "Needs Attention", labelAr: "يحتاج متابعة",    color: "text-status-yellow", bg: "bg-status-yellow/10 border-status-yellow/30",  icon: ShieldAlert };
  return   { label: "Healthy Business",labelAr: "منشأة سليمة",     color: "text-status-green",  bg: "bg-status-green/10 border-status-green/30",    icon: CheckCircle };
}

// ── Track 1: Existing Business ────────────────────────────────
function Track1({ isRTL, portfolioBid }) {
  const [selected, setSelected] = useState(portfolioBid || "cafe");
  const [data,     setData]     = useState(null);
  const [forecast, setForecast] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);
  const cache = useRef({});

  const load = useCallback((id) => {
    if (cache.current[id]) {
      setData(cache.current[id].dash);
      setForecast(cache.current[id].fore);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);

    // Portfolio businesses load from a single combined endpoint
    const isPortfolio = id.startsWith("biz_");
    const fetchFn = isPortfolio
      ? getPortfolioBusiness(id).then(res => {
          const detail = res.data;
          const series = detail?.forecast?.series || [];
          const fore = series.map(d => ({
            date:  d.date.slice(5),
            value: Math.round(d.predicted_revenue),
            upper: Math.round(d.upper_bound),
            lower: Math.round(d.lower_bound),
          }));
          cache.current[id] = { dash: detail, fore };
          setData(detail);
          setForecast(fore);
        })
      : Promise.all([getDashboard(id), getForecast(id)])
          .then(([dashRes, foreRes]) => {
            const dash = dashRes.data;
            const series = foreRes.data.series || [];
            const fore = series.map(d => ({
              date:  d.date.slice(5),
              value: Math.round(d.predicted_revenue),
              upper: Math.round(d.upper_bound),
              lower: Math.round(d.lower_bound),
            }));
            cache.current[id] = { dash, fore };
            setData(dash);
            setForecast(fore);
          });

    fetchFn
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Sync if portfolioBid changes (navigating from portfolio page)
  useEffect(() => {
    if (portfolioBid && portfolioBid !== selected) {
      setSelected(portfolioBid);
      setData(null);
    }
  }, [portfolioBid]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { load(selected); }, [selected, load]);

  const dscr    = data?.dscr;
  const fraud   = data?.fraud;
  const summary = data?.summary;
  const txs     = data?.recent_transactions || [];
  const verdict = getVerdict(dscr, fraud);
  const VIcon   = verdict?.icon || CheckCircle;
  const dynamic = dscr?.dynamic_credit_limit;
  const trend   = dynamic?.trend_direction || "flat";

  return (
    <div className="space-y-6">

      {/* Business selector */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {/* Portfolio business chip — shown only when navigated from /portfolio */}
        {selected.startsWith("biz_") && (
          <button
            key={selected}
            className="relative flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap text-white"
            style={{ transition: "color 150ms var(--ease-out)" }}
          >
            <motion.div
              layoutId="bizPill"
              className="absolute inset-0 rounded-lg bg-brand-blue"
              style={{ zIndex: -1 }}
              transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            />
            {data?.business?.name || selected}
          </button>
        )}
        {BUSINESSES.map(biz => (
          <button
            key={biz.id}
            onClick={() => { setSelected(biz.id); if (!cache.current[biz.id]) setData(null); }}
            className={`relative flex-shrink-0 px-4 py-2 rounded-lg
                        text-sm font-medium whitespace-nowrap
                        ${selected === biz.id ? "text-white" : "text-gray-400 hover:text-white"}`}
            style={{ transition: "color 150ms var(--ease-out)" }}
          >
            {selected === biz.id && (
              <motion.div
                layoutId="bizPill"
                className="absolute inset-0 rounded-lg bg-brand-blue"
                style={{ zIndex: -1 }}
                transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
              />
            )}
            {isRTL ? biz.nameAr : biz.nameEn}
          </button>
        ))}
      </div>

      {/* Business name + sector + verdict */}
      <AnimatePresence mode="wait">
        {data && (
          <motion.div
            key={selected}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
            className="flex items-center justify-between flex-wrap gap-3"
          >
            <div>
              <h2 className="text-lg font-bold text-white">
                {selected.startsWith("biz_")
                  ? (data?.business?.name || selected)
                  : isRTL
                    ? BUSINESSES.find(b => b.id === selected)?.nameAr
                    : BUSINESSES.find(b => b.id === selected)?.nameEn}
              </h2>
              <div className="text-xs text-gray-400 mt-0.5">
                {selected.startsWith("biz_")
                  ? (data?.business?.sector || "SME Portfolio")
                  : BUSINESSES.find(b => b.id === selected)?.sector}
                {dscr?.archetype_description && (
                  <span className="text-brand-gold/60 ms-2">
                    · {dscr.archetype_description.slice(0, 40)}
                  </span>
                )}
              </div>
            </div>
            {verdict && (
              <div className={`flex items-center gap-2 px-3 py-1.5
                               rounded-full border text-xs font-medium
                               ${verdict.bg} ${verdict.color}`}>
                <VIcon size={13} />
                {isRTL ? verdict.labelAr : verdict.label}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading skeletons */}
      {loading && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass-card rounded-xl p-5 space-y-3 animate-pulse">
              <div className="w-9 h-9 rounded-lg bg-surface-border" />
              <div className="h-7 bg-surface-border rounded w-2/3" />
              <div className="h-3 bg-surface-border rounded w-full" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-status-red text-sm
                        p-4 rounded-xl glass-card border border-status-red/30">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* KPI Cards */}
      {!loading && data && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              icon: Activity, iconBg: "bg-brand-gold/10",
              iconColor: "text-brand-gold",
              label: isRTL ? "إجمالي الإيرادات" : "Total Revenue",
              value: (
                <>
                  <span className="text-xs text-gray-400 me-1">SAR</span>
                  <AnimatedNumber value={summary?.total_revenue_sar || 0} />
                </>
              ),
              sub: isRTL ? "يونيو ٢٠٢٥" : "June 2025",
            },
            {
              icon: CreditCard, iconBg: "bg-status-green/10",
              iconColor: "text-status-green",
              label: isRTL ? "الحد الائتماني" : "Credit Limit",
              value: `SAR ${fmt(dynamic?.dynamic_limit_sar || dscr?.approved_credit_limit_sar)}`,
              sub: trend === "growing"   ? (isRTL ? "نامٍ"    : "Growing")
                 : trend === "declining" ? (isRTL ? "متراجع"  : "Declining")
                 : (isRTL ? "مستقر" : "Stable"),
              subColor: trend === "growing"   ? "text-status-green"
                       : trend === "declining" ? "text-status-red"
                       : "text-gray-400",
            },
            {
              icon: BarChart2, iconBg: "bg-status-blue/10",
              iconColor: "text-status-blue",
              label: isRTL ? "معدل تغطية الدين" : "DSCR Score",
              value: dscr?.dscr_score?.toFixed(2) || "—",
              sub: dscr?.risk_tier?.replace("_", " ") || "",
              subColor: RISK_COLOR[dscr?.risk_tier] || "text-gray-400",
            },
            {
              icon: Zap, iconBg: "bg-brand-gold/10",
              iconColor: "text-brand-gold",
              label: isRTL ? "سعر الفائدة" : "Interest Rate",
              value: dscr ? `${(dscr.final_interest_rate * 100).toFixed(2)}%` : "—",
              sub: dscr?.sustainability_eligible
                ? (isRTL ? "يشمل خصم الطاقة" : "Includes green discount")
                : "",
              subIcon: dscr?.sustainability_eligible ? Leaf : null,
            },
          ].map((card, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07, duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className="glass-card rounded-xl p-5 space-y-3"
              style={{ transition: "border-color 180ms var(--ease-out)" }}
            >
              <div className={`w-9 h-9 rounded-lg ${card.iconBg}
                               flex items-center justify-center`}>
                <card.icon size={18} className={card.iconColor} />
              </div>
              <div className="text-2xl font-bold text-white">{card.value}</div>
              <div className="text-xs text-gray-400">{card.label}</div>
              {card.sub && (
                <div className={`text-xs flex items-center gap-1
                                 ${card.subColor || "text-gray-500"}`}>
                  {card.subIcon && <card.subIcon size={11} />}
                  {card.sub}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {/* Fraud + Energy row */}
      {!loading && data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">

          {/* Fraud panel */}
          <div className={`glass-card rounded-xl p-5 space-y-4 border
            ${fraud?.approval_frozen
              ? "border-status-red/30 bg-status-red/5"
              : fraud?.overall_status === "flagged"
              ? "border-status-yellow/30 bg-status-yellow/5"
              : "border-status-green/30 bg-status-green/5"}`}>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={16} className="text-gray-400" />
                <span className="text-sm font-medium text-white">
                  {isRTL ? "حالة الاحتيال" : "Fraud Status"}
                </span>
              </div>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full
                ${fraud?.approval_frozen
                  ? "text-status-red bg-status-red/20"
                  : fraud?.overall_status === "flagged"
                  ? "text-status-yellow bg-status-yellow/20"
                  : "text-status-green bg-status-green/20"}`}>
                {fraud?.overall_status?.toUpperCase() || "—"}
              </span>
            </div>

            {/* Score bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-400">
                <span>{isRTL ? "درجة الخطر" : "Risk Score"}</span>
                <span>{fraud?.fraud_score || 0}/100</span>
              </div>
              <div className="h-2 bg-surface-border rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full
                    ${(fraud?.fraud_score || 0) > 55 ? "bg-status-red"
                    : (fraud?.fraud_score || 0) > 25 ? "bg-status-yellow"
                    : "bg-status-green"}`}
                  initial={{ width: "0%" }}
                  animate={{ width: `${fraud?.fraud_score || 0}%` }}
                  transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1], delay: 0.3 }}
                />
              </div>
            </div>

            {/* Anomalies */}
            {fraud?.anomalies?.length > 0 ? (
              <div className="space-y-2">
                {fraud.anomalies.slice(0, 2).map((a, i) => (
                  <div key={i}
                    className="flex items-start gap-2 p-2 rounded-lg bg-surface-dark text-xs">
                    <AlertTriangle
                      size={11}
                      className={`shrink-0 mt-0.5 ${a.severity === "critical"
                        ? "text-status-red"
                        : "text-status-yellow"}`}
                    />
                    <div>
                      <span className="text-gray-400">{a.date} — </span>
                      <span className="text-gray-500">
                        {a.description?.slice(0, 55)}...
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-status-green flex items-center gap-1.5">
                <CheckCircle size={12} />
                {isRTL ? "لا توجد شذوذات" : "No anomalies detected"}
              </div>
            )}
          </div>

          {/* Energy panel */}
          <div className="glass-card rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Leaf size={16} className="text-emerald-400" />
              <span className="text-sm font-medium text-white">
                {isRTL ? "كفاءة الطاقة" : "Energy Efficiency"}
              </span>
            </div>

            <div className="flex items-center gap-4">
              {/* SVG gauge */}
              <div className="relative w-16 h-16 shrink-0">
                <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
                  <circle cx="18" cy="18" r="15.9"
                    fill="none" stroke="#1E2D42" strokeWidth="3" />
                  <motion.circle
                    cx="18" cy="18" r="15.9"
                    fill="none"
                    stroke={
                      (dscr?.avg_energy_efficiency || 0) > 0.7 ? "#22C55E"
                      : (dscr?.avg_energy_efficiency || 0) > 0.4 ? "#F59E0B"
                      : "#EF4444"
                    }
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeDasharray="100"
                    initial={{ strokeDashoffset: 100 }}
                    animate={{
                      strokeDashoffset: 100 - Math.round((dscr?.avg_energy_efficiency || 0) * 100)
                    }}
                    transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1], delay: 0.4 }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-bold text-white">
                    {Math.round((dscr?.avg_energy_efficiency || 0) * 100)}%
                  </span>
                </div>
              </div>

              <div className="space-y-2 flex-1">
                <div className="text-sm text-white">
                  {dscr?.green_days_count || 0} {isRTL ? "أيام خضراء" : "green days"}
                </div>
                <div className={`text-xs px-2 py-1 rounded-lg inline-flex
                                 items-center gap-1.5
                  ${dscr?.sustainability_eligible
                    ? "bg-emerald-400/10 text-emerald-400 border border-emerald-400/20"
                    : "bg-surface-dark text-gray-500 border border-surface-border"}`}>
                  <Leaf size={11} />
                  {dscr?.sustainability_eligible
                    ? (isRTL
                      ? `خصم ${((dscr.sustainability_discount || 0) * 100).toFixed(1)}% على الفائدة`
                      : `${((dscr.sustainability_discount || 0) * 100).toFixed(1)}% rate discount`)
                    : (isRTL ? "لا يوجد خصم" : "No discount yet")}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Forecast chart */}
      {!loading && forecast.length > 0 && (
        <div className="glass-card rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-brand-gold" />
              <span className="text-sm font-medium text-white">
                {isRTL ? "توقعات الإيرادات — يوليو ٢٠٢٥" : "Revenue Forecast — July 2025"}
              </span>
            </div>
            <div className={`text-xs font-medium px-2 py-0.5 rounded-full
              ${trend === "growing"   ? "text-status-green bg-status-green/10"
              : trend === "declining" ? "text-status-red bg-status-red/10"
              : "text-gray-400 bg-surface-dark"}`}>
              {trend === "growing"   ? (isRTL ? "نامٍ"   : "Growing")
              : trend === "declining" ? (isRTL ? "متراجع" : "Declining")
              : (isRTL ? "مستقر" : "Stable")}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={forecast}
              margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="goldGrad2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#C9A84C" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#C9A84C" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2D42" />
              <XAxis dataKey="date"
                tick={{ fill: "#6B7280", fontSize: 10 }}
                tickLine={false} axisLine={false} />
              <YAxis
                tick={{ fill: "#6B7280", fontSize: 10 }}
                tickLine={false} axisLine={false}
                tickFormatter={v => `${(v / 1000).toFixed(0)}K`} />
              <Tooltip
                contentStyle={{
                  background: "rgba(22,32,48,0.95)",
                  border: "1px solid rgba(201,168,76,0.2)",
                  borderRadius: "10px", fontSize: "12px",
                  backdropFilter: "blur(12px)",
                }}
                labelStyle={{ color: "#C9A84C", fontWeight: 600 }}
                formatter={v => [`SAR ${fmtFull(v)}`, ""]}
              />
              <Area type="monotone" dataKey="value"
                stroke="#C9A84C" strokeWidth={2}
                fill="url(#goldGrad2)" dot={false}
                activeDot={{ r: 4, fill: "#C9A84C" }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent transactions */}
      {!loading && txs.length > 0 && (
        <div className="glass-card rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-brand-gold" />
            <span className="text-sm font-medium text-white">
              {isRTL ? "آخر المعاملات" : "Recent Transactions"}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 border-b border-surface-border">
                  <th className="text-start pb-2 font-medium">
                    {isRTL ? "الوقت" : "Time"}
                  </th>
                  <th className="text-end pb-2 font-medium">
                    {isRTL ? "المبلغ" : "Amount"}
                  </th>
                  <th className="text-end pb-2 font-medium hidden sm:table-cell">
                    {isRTL ? "الطريقة" : "Method"}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {txs.slice(0, 6).map((tx, i) => (
                  <tr key={i}
                    className="hover:bg-surface-hover"
                    style={{ transition: "background-color 120ms var(--ease-out)" }}>
                    <td className="py-2 text-gray-400">
                      {tx.timestamp?.slice(11, 16) || "—"}
                    </td>
                    <td className="py-2 text-end font-medium text-white">
                      {fmtFull(tx.amount_sar)} {isRTL ? "ر.س" : "SAR"}
                    </td>
                    <td className="py-2 text-end text-gray-500
                                   hidden sm:table-cell capitalize">
                      {tx.payment_method || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Track 2: New Business ─────────────────────────────────────
function Track2({ isRTL }) {
  const [dbr, setDbr] = useState({
    salary: 15000, obligations: 2000,
    loan: 35000, term: 24,
  });
  const [dbrResult,  setDbrResult]  = useState(null);
  const [dbrLoading, setDbrLoading] = useState(false);

  const [intake, setIntake] = useState({
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
  const [intakeResult,  setIntakeResult]  = useState(null);
  const [intakeLoading, setIntakeLoading] = useState(false);

  const setD  = k => v => setDbr(p => ({ ...p, [k]: Number(v) }));
  const setI  = k => v => setIntake(p => ({ ...p, [k]: v }));
  const setIN = k => v => setIntake(p => ({ ...p, [k]: Number(v) }));

  const calcDBR = async () => {
    setDbrLoading(true);
    try {
      const res = await assessDBR({
        monthly_salary:       dbr.salary,
        existing_obligations: dbr.obligations,
        requested_loan:       dbr.loan,
        loan_term_months:     dbr.term,
      });
      setDbrResult(res.data);
    } catch (e) { console.error(e); }
    finally { setDbrLoading(false); }
  };

  const calcIntake = async () => {
    setIntakeLoading(true);
    try {
      const res = await getBusinessProfile(intake);
      setIntakeResult(res.data);
    } catch (e) { console.error(e); }
    finally { setIntakeLoading(false); }
  };

  const timeline = [
    { day: isRTL ? "اليوم 0"  : "Day 0",  conf: 40, labelEn: "Intake form only",     labelAr: "نموذج الاستبيان فقط" },
    { day: isRTL ? "اليوم 7"  : "Day 7",  conf: 55, labelEn: "7 days POS data",       labelAr: "7 أيام بيانات" },
    { day: isRTL ? "اليوم 14" : "Day 14", conf: 72, labelEn: "Real data taking over",  labelAr: "البيانات الحقيقية تتصدر" },
    { day: isRTL ? "اليوم 30" : "Day 30", conf: 95, labelEn: "Full SME pipeline",      labelAr: "مسار المنشآت الكامل" },
  ];

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-lg font-bold text-white">
          {isRTL ? "بدء مشروع جديد؟" : "Starting a New Business?"}
        </h2>
        <p className="text-gray-400 text-sm">
          {isRTL
            ? "لا تاريخ ائتماني؟ راتبك يكفي للبدء."
            : "No credit history? Your salary is enough to start."}
        </p>
      </div>

      {/* Two columns: DBR + Intake */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* DBR Calculator */}
        <div className="glass-card rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
            <Calculator size={16} className="text-brand-gold" />
            <span className="text-sm font-semibold text-white">
              {isRTL ? "حساب الأهلية" : "Loan Eligibility"}
            </span>
            <span className="text-xs text-gray-500 ms-auto">
              {isRTL ? "حد ساما 33%" : "SAMA cap 33%"}
            </span>
          </div>

          <div className="space-y-3">
            {[
              { label: isRTL ? "الراتب الشهري (SAR)"       : "Monthly Salary (SAR)",      key: "salary",      min: 3000, step: 500 },
              { label: isRTL ? "الالتزامات الحالية (SAR)"  : "Existing Obligations (SAR)", key: "obligations", min: 0,    step: 100 },
              { label: isRTL ? "مبلغ القرض (SAR)"          : "Loan Amount (SAR)",          key: "loan",        min: 5000, step: 1000 },
              { label: isRTL ? "المدة (أشهر)"              : "Term (months)",              key: "term",        min: 6, max: 60, step: 6 },
            ].map(f => (
              <div key={f.key} className="space-y-1">
                <label className="text-xs text-gray-400">{f.label}</label>
                <input
                  type="number"
                  value={dbr[f.key]}
                  onChange={e => setD(f.key)(e.target.value)}
                  min={f.min} max={f.max} step={f.step}
                  className="w-full bg-surface-dark border border-surface-border
                             rounded-lg px-3 py-2 text-sm text-white
                             focus:outline-none focus:border-brand-gold
                             placeholder-gray-600"
                  style={{ transition: "border-color 150ms var(--ease-out)" }}
                />
              </div>
            ))}
          </div>

          <button
            onClick={calcDBR}
            disabled={dbrLoading}
            className="btn-gold w-full flex items-center justify-center gap-2
                       bg-brand-gold hover:bg-brand-goldLight
                       text-brand-blueDark font-semibold text-sm
                       py-2.5 rounded-xl disabled:opacity-50"
          >
            {dbrLoading
              ? <Loader2 size={15} className="animate-spin" />
              : <Calculator size={15} />}
            {isRTL ? "احسب الأهلية" : "Check Eligibility"}
          </button>

          {/* DBR Result */}
          {dbrResult && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className={`space-y-3 p-4 rounded-xl border
                ${dbrResult.approved
                  ? "bg-status-green/5 border-status-green/30"
                  : "bg-status-red/5 border-status-red/30"}`}
            >
              <div className="flex items-center gap-2">
                {dbrResult.approved
                  ? <CheckCircle size={16} className="text-status-green" />
                  : <XCircle    size={16} className="text-status-red" />}
                <span className={`font-bold text-sm
                  ${dbrResult.approved ? "text-status-green" : "text-status-red"}`}>
                  {dbrResult.approved
                    ? (isRTL ? "موافق عليه" : "Approved")
                    : (isRTL ? "مرفوض" : "Denied")}
                </span>
                <span className="text-xs text-gray-400 ms-auto">
                  DBR: {(dbrResult.dbr_ratio * 100).toFixed(1)}%
                </span>
              </div>

              {/* DBR bar */}
              <div className="space-y-1">
                <div className="relative h-2 bg-surface-border rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full
                      ${dbrResult.approved ? "bg-status-green" : "bg-status-red"}`}
                    initial={{ width: "0%" }}
                    animate={{ width: `${Math.min(dbrResult.dbr_ratio / 0.6, 1) * 100}%` }}
                    transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
                  />
                  <div
                    className="absolute top-0 h-full w-0.5 bg-white/50"
                    style={{ left: `${(0.33 / 0.6) * 100}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-600">
                  <span>0%</span>
                  <span className="text-white/40">SAMA 33%</span>
                  <span>60%</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-gray-400">
                    {isRTL ? "القسط الشهري" : "Monthly Payment"}
                  </div>
                  <div className="text-white font-medium mt-0.5">
                    SAR {fmtFull(
                      dbrResult.monthly_payment
                      || dbrResult.requested_loan_monthly_payment
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-gray-400">
                    {dbrResult.approved
                      ? (isRTL ? "مبلغ القرض" : "Loan Amount")
                      : (isRTL ? "الحد الأقصى" : "Max Eligible")}
                  </div>
                  <div className={`font-medium mt-0.5
                    ${dbrResult.approved ? "text-status-green" : "text-status-yellow"}`}>
                    SAR {fmtFull(dbrResult.approved
                      ? (dbrResult.requested_loan_sar || dbr.loan)
                      : dbrResult.max_eligible_loan_sar)}
                  </div>
                </div>
              </div>

              {dbrResult.approved && (
                <div className="flex items-start gap-1.5 text-xs
                                text-brand-blueLight p-2 rounded-lg
                                bg-brand-blue/10 border border-brand-blue/20">
                  <ShieldCheck size={12} className="shrink-0 mt-0.5" />
                  {isRTL
                    ? "الأقساط تُخصم تلقائياً من راتبك"
                    : "Installments auto-deducted from salary"}
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Business Intake */}
        <div className="glass-card rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
            <Building2 size={16} className="text-brand-blueLight" />
            <span className="text-sm font-semibold text-white">
              {isRTL ? "تصنيف مشروعك" : "Classify Your Business"}
            </span>
          </div>

          <div className="space-y-3">
            {[
              { label: isRTL ? "متوسط الفاتورة (SAR)"  : "Avg Ticket (SAR)",      key: "typical_ticket_sar",       min: 1, step: 10 },
              { label: isRTL ? "عملاء يومياً"           : "Daily Customers",       key: "expected_daily_customers", min: 1, step: 5 },
              { label: isRTL ? "ساعات العمل"            : "Operating Hours/Day",   key: "operating_hours_per_day",  min: 1, max: 24 },
              { label: isRTL ? "أيام العمل أسبوعياً"   : "Business Days/Week",    key: "business_days_per_week",   min: 1, max: 7 },
            ].map(f => (
              <div key={f.key} className="space-y-1">
                <label className="text-xs text-gray-400">{f.label}</label>
                <input
                  type="number"
                  value={intake[f.key]}
                  onChange={e => setIN(f.key)(e.target.value)}
                  min={f.min} max={f.max} step={f.step}
                  className="w-full bg-surface-dark border border-surface-border
                             rounded-lg px-3 py-2 text-sm text-white
                             focus:outline-none focus:border-brand-gold
                             placeholder-gray-600"
                  style={{ transition: "border-color 150ms var(--ease-out)" }}
                />
              </div>
            ))}

            {/* Toggles */}
            <div className="space-y-2 pt-1 border-t border-surface-border">
              {[
                { label: isRTL ? "موجه للمستهلكين (B2C)" : "Consumer-Facing (B2C)", key: "is_consumer_facing" },
                { label: isRTL ? "منتجات عالية القيمة"   : "High-Value Items",      key: "sells_high_value_items" },
                { label: isRTL ? "يحمل مخزوناً"          : "Holds Inventory",       key: "holds_physical_inventory" },
                { label: isRTL ? "يعمل ليلاً"            : "Late Night Operations", key: "operates_late_night" },
              ].map(tog => (
                <div key={tog.key}
                  className="flex items-center justify-between py-0.5">
                  <span className="text-xs text-gray-400">{tog.label}</span>
                  <button
                    onClick={() => setI(tog.key)(!intake[tog.key])}
                    className={`w-10 h-5 rounded-full relative shrink-0
                      ${intake[tog.key] ? "bg-brand-gold" : "bg-surface-border"}`}
                    style={{ transition: "background-color 150ms var(--ease-out)" }}
                  >
                    <motion.div
                      className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow"
                      animate={{ x: intake[tog.key] ? 18 : 2 }}
                      transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={calcIntake}
            disabled={intakeLoading}
            className="btn-blue w-full flex items-center justify-center gap-2
                       bg-brand-blue hover:bg-brand-blueLight
                       text-white font-semibold text-sm
                       py-2.5 rounded-xl disabled:opacity-50"
          >
            {intakeLoading
              ? <Loader2 size={15} className="animate-spin" />
              : <Sprout size={15} />}
            {isRTL ? "حلّل مشروعي" : "Analyse My Business"}
          </button>

          {/* Intake Result */}
          {intakeResult && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className="space-y-3 p-4 rounded-xl border
                         border-brand-gold/20 bg-brand-gold/5"
            >
              <div className="text-xs text-gray-400">
                {isRTL ? "النمط المكتشف" : "Detected Pattern"}
              </div>
              <div className="text-sm font-medium text-brand-gold">
                {intakeResult.archetype_description}
              </div>

              {/* Confidence bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-gray-400">
                  <span>{isRTL ? "الثقة" : "Confidence"}</span>
                  <span>{((intakeResult.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-brand-gold rounded-full"
                    initial={{ width: "0%" }}
                    animate={{ width: `${(intakeResult.confidence || 0) * 100}%` }}
                    transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
                  />
                </div>
              </div>

              {intakeResult.expense_estimate && (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <div className="text-gray-400">
                      {isRTL ? "نسبة المصاريف" : "Expense Ratio"}
                    </div>
                    <div className="text-white font-bold text-base mt-0.5">
                      {((intakeResult.expense_estimate.total_expense_ratio || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-400">
                      {isRTL ? "هامش الربح" : "Net Margin"}
                    </div>
                    <div className="text-status-green font-bold text-base mt-0.5">
                      {((intakeResult.expense_estimate.net_margin_estimate || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              )}

              {intakeResult.preliminary_credit_profile && (
                <div className={`text-xs px-2 py-1.5 rounded-lg
                                 flex items-center gap-1.5
                  ${intakeResult.preliminary_credit_profile.risk_indication === "low"
                    ? "text-status-green bg-status-green/10 border border-status-green/20"
                    : intakeResult.preliminary_credit_profile.risk_indication === "medium"
                    ? "text-status-yellow bg-status-yellow/10 border border-status-yellow/20"
                    : "text-status-red bg-status-red/10 border border-status-red/20"}`}
                >
                  <Info size={11} />
                  {isRTL ? "مستوى المخاطر الأولي: " : "Preliminary Risk: "}
                  <span className="font-bold uppercase">
                    {intakeResult.preliminary_credit_profile.risk_indication}
                  </span>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>

      {/* Confidence timeline */}
      <div className="glass-card rounded-xl p-5 space-y-4">
        <div className="text-sm font-medium text-white">
          {isRTL
            ? "رحلة الانتقال: من الاستبيان إلى مسار المنشآت"
            : "Transition Journey: Intake Form → Full SME Pipeline"}
        </div>
        <div className="grid grid-cols-4 gap-2">
          {timeline.map((step, i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-center gap-1">
                <div className={`w-5 h-5 rounded-full shrink-0
                                 flex items-center justify-center
                                 text-xs font-bold
                  ${i === 3
                    ? "bg-brand-gold text-brand-blueDark"
                    : "bg-brand-blue/30 text-brand-gold"}`}>
                  {i + 1}
                </div>
                {i < 3 && (
                  <div className="flex-1 h-0.5 bg-gradient-to-r
                                  from-brand-blue/40 to-brand-blue/10" />
                )}
              </div>
              <div className="space-y-1">
                <div className="text-xs font-medium text-brand-gold">
                  {step.day}
                </div>
                <div className="text-xs text-white">
                  {isRTL ? step.labelAr : step.labelEn}
                </div>
                <div className="h-1 bg-surface-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-brand-gold/60 rounded-full"
                    initial={{ width: "0%" }}
                    whileInView={{ width: `${step.conf}%` }}
                    viewport={{ once: true }}
                    transition={{
                      duration: 0.6,
                      ease: [0.23, 1, 0.32, 1],
                      delay: i * 0.1,
                    }}
                  />
                </div>
                <div className="text-xs text-gray-500">{step.conf}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────
export default function Demo() {
  const { t, isRTL } = useLang();
  const [searchParams] = useSearchParams();
  const portfolioBid = searchParams.get("business") || null;
  const [track, setTrack] = useState("existing");

  return (
    <div className="space-y-6">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">
            {isRTL ? "محرك الإقراض الذكي" : "AI Lending Engine"}
          </h1>
          <p className="text-gray-400 text-xs mt-0.5">
            {isRTL
              ? "يفهم أي منشأة · يقيّم بشكل عادل · يقرر بشكل ذكي"
              : "Understands any business · Assesses fairly · Decides intelligently"}
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5
                        rounded-full border border-status-green/30
                        bg-status-green/10">
          <div className="w-2 h-2 rounded-full bg-status-green animate-pulse" />
          <span className="text-status-green text-xs font-medium">
            {isRTL ? "مباشر" : "Live"}
          </span>
        </div>
      </div>

      {/* Track toggle */}
      <div className="flex gap-1 p-1 rounded-xl bg-surface-card
                      border border-surface-border w-fit">
        {[
          { id: "existing", icon: Building2, labelEn: "Existing Business", labelAr: "منشأة قائمة" },
          { id: "new",      icon: Sprout,    labelEn: "New Business",      labelAr: "مشروع جديد" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setTrack(tab.id)}
            className={`relative flex items-center gap-2 px-5 py-2
                        rounded-lg text-sm font-medium
                        ${track === tab.id ? "text-white" : "text-gray-400 hover:text-white"}`}
            style={{ transition: "color 150ms var(--ease-out)" }}
          >
            {track === tab.id && (
              <motion.div
                layoutId="trackPill"
                className="absolute inset-0 rounded-lg bg-brand-blue"
                style={{ zIndex: -1 }}
                transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
              />
            )}
            <tab.icon size={15} />
            {isRTL ? tab.labelAr : tab.labelEn}
          </button>
        ))}
      </div>

      {/* Track content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={track}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
        >
          {track === "existing"
            ? <Track1 isRTL={isRTL} t={t} portfolioBid={portfolioBid} />
            : <Track2 isRTL={isRTL} t={t} />}
        </motion.div>
      </AnimatePresence>

    </div>
  );
}
