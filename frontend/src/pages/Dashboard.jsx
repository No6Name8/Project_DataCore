import { useEffect, useState, useCallback } from "react";
import { useLang } from "../i18n/LanguageContext";
import { getDashboard, getForecast } from "../services/api";
import {
  TrendingUp, TrendingDown, Minus,
  ShieldAlert, ShieldX,
  Leaf, AlertTriangle, CheckCircle,
  XCircle, Zap, CreditCard,
  BarChart2, Activity, RefreshCw,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";

// ── Business list ─────────────────────────────────────────────
const BUSINESSES = [
  { id: "cafe",       nameEn: "Qahwa Corner Cafe",      nameAr: "مقهى قهوة كورنر" },
  { id: "minimarket", nameEn: "Baraka Minimarket",       nameAr: "مينيماركت بركة" },
  { id: "laundromat", nameEn: "Al Noor Laundromat",      nameAr: "مغسلة النور" },
  { id: "realestate", nameEn: "Majd Real Estate",        nameAr: "مجد للعقارات" },
  { id: "cardealer",  nameEn: "Rawabi Auto Gallery",     nameAr: "معرض روابي للسيارات" },
  { id: "motorbike",  nameEn: "Saqr Motorbikes",         nameAr: "صقر للدراجات النارية" },
];

// ── Helpers ───────────────────────────────────────────────────
const fmt = (n) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M`
  : n >= 1_000   ? `${(n / 1_000).toFixed(0)}K`
  : String(Math.round(n));

const fmtFull = (n) => new Intl.NumberFormat("en-SA").format(Math.round(n));

const RISK_COLOR = {
  very_low: "text-status-green",
  low:      "text-status-green",
  medium:   "text-status-yellow",
  high:     "text-status-red",
  critical: "text-status-red",
};
const RISK_BADGE = {
  very_low: "text-status-green bg-status-green/10 border border-status-green/30",
  low:      "text-status-green bg-status-green/10 border border-status-green/30",
  medium:   "text-status-yellow bg-status-yellow/10 border border-status-yellow/30",
  high:     "text-status-red bg-status-red/10 border border-status-red/30",
  critical: "text-status-red bg-status-red/10 border border-status-red/30",
};

// ── KPI Card ──────────────────────────────────────────────────
function KPICard({ icon: Icon, iconColor, iconBg, label, value, sub, badge, badgeColor }) {
  return (
    <div className="glass-card rounded-xl p-5 space-y-3 hover:border-brand-gold/20 transition-all">
      <div className="flex items-center justify-between">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconBg}`}>
          <Icon size={18} className={iconColor} />
        </div>
        {badge && (
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-xs text-gray-400 mt-0.5">{label}</div>
        {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

// ── Skeleton ──────────────────────────────────────────────────
function PanelSkeleton() {
  return (
    <div className="glass-card rounded-xl p-5 space-y-3 animate-pulse">
      <div className="h-4 bg-surface-border rounded w-1/3" />
      <div className="h-8 bg-surface-border rounded w-2/3" />
      <div className="h-3 bg-surface-border rounded w-full" />
      <div className="h-3 bg-surface-border rounded w-4/5" />
    </div>
  );
}

// ── Fraud Panel ───────────────────────────────────────────────
function FraudPanel({ fraud, t, isRTL }) {
  if (!fraud) return <PanelSkeleton />;

  const { overall_status, fraud_score, anomalies_detected, anomalies } = fraud;

  const STATUS = {
    clear:   { icon: CheckCircle, color: "text-status-green",  border: "border-status-green/30",  bg: "bg-status-green/10",  label: t.statusClear },
    flagged: { icon: ShieldAlert,  color: "text-status-yellow", border: "border-status-yellow/30", bg: "bg-status-yellow/10", label: t.statusFlagged },
    frozen:  { icon: ShieldX,      color: "text-status-red",    border: "border-status-red/30",    bg: "bg-status-red/10",    label: t.statusFrozen },
  };
  const cfg = STATUS[overall_status] ?? STATUS.clear;
  const StatusIcon = cfg.icon;

  return (
    <div className={`glass-card rounded-xl p-5 space-y-4 border ${cfg.border}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusIcon size={18} className={cfg.color} />
          <span className="font-semibold text-white text-sm">{t.fraudStatus}</span>
        </div>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border
                          ${cfg.color} ${cfg.bg} ${cfg.border}`}>
          {cfg.label}
        </span>
      </div>

      {/* Score bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-400">
          <span>{isRTL ? "درجة الاحتيال" : "Fraud Score"}</span>
          <span className={cfg.color}>{fraud_score}/100</span>
        </div>
        <div className="h-2 bg-surface-border rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700
              ${fraud_score > 55 ? "bg-status-red"
              : fraud_score > 25 ? "bg-status-yellow"
              : "bg-status-green"}`}
            style={{ width: `${fraud_score}%` }}
          />
        </div>
      </div>

      {/* Anomalies */}
      {anomalies?.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs text-gray-400">
            {anomalies_detected} {isRTL ? "شذوذ مكتشف" : "anomalies detected"}
          </div>
          {anomalies.slice(0, 3).map((a, i) => (
            <div key={i}
              className="flex items-start gap-2 p-2 rounded-lg bg-surface-dark text-xs">
              <AlertTriangle size={12} className={
                a.severity === "critical" ? "text-status-red mt-0.5"
                : a.severity === "high"   ? "text-status-yellow mt-0.5"
                : "text-gray-400 mt-0.5"
              } />
              <div>
                <div className="text-gray-300">{a.date}</div>
                <div className="text-gray-500 line-clamp-1">{a.description}</div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-gray-400 text-center py-2">
          {isRTL ? "لا توجد شذوذات" : "No anomalies detected"}
        </div>
      )}
    </div>
  );
}

// ── Energy / Sustainability Panel ─────────────────────────────
function EnergyPanel({ dscr, t, isRTL }) {
  if (!dscr) return <PanelSkeleton />;

  const eff     = dscr.avg_energy_efficiency ?? 0;
  const pct     = Math.round(eff * 100);
  const eligible = dscr.sustainability_eligible;
  const discount = dscr.sustainability_discount ?? 0;
  const gaugeColor = pct > 70 ? "#22C55E" : pct > 40 ? "#F59E0B" : "#EF4444";

  return (
    <div className="glass-card rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Leaf size={18} className="text-emerald-400" />
        <span className="font-semibold text-white text-sm">{t.sustainability}</span>
      </div>

      <div className="flex items-center gap-4">
        {/* SVG gauge */}
        <div className="relative w-16 h-16 shrink-0">
          <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
            <circle cx="18" cy="18" r="15.9"
              fill="none" stroke="#1E2D42" strokeWidth="3" />
            <circle cx="18" cy="18" r="15.9"
              fill="none"
              stroke={gaugeColor}
              strokeWidth="3"
              strokeDasharray={`${pct} 100`}
              strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold text-white">{pct}%</span>
          </div>
        </div>

        <div className="space-y-1">
          <div className="text-sm text-white font-medium">{t.energyScore}</div>
          <div className="text-xs text-gray-400">
            {dscr.green_days_count ?? 0} {isRTL ? "أيام خضراء" : "green days"}
          </div>
        </div>
      </div>

      {/* Eligibility badge */}
      <div className={`flex items-center gap-2 p-3 rounded-lg text-xs
                       ${eligible
                         ? "bg-emerald-400/10 border border-emerald-400/30"
                         : "bg-surface-dark border border-surface-border"}`}>
        <Leaf size={14} className={eligible ? "text-emerald-400" : "text-gray-500"} />
        <span className={eligible ? "text-emerald-400 font-medium" : "text-gray-400"}>
          {eligible
            ? (isRTL
                ? `خصم ${(discount * 100).toFixed(1)}% على الفائدة`
                : `${(discount * 100).toFixed(1)}% interest discount`)
            : (isRTL ? "غير مؤهل للخصم الأخضر" : "Not eligible for green discount")}
        </span>
      </div>
    </div>
  );
}

// ── Forecast Chart ────────────────────────────────────────────
function ForecastChart({ businessId, t, isRTL }) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    setLoading(true);
    getForecast(businessId)
      .then(res => {
        setChartData((res.data.series ?? []).map(d => ({
          date:  d.date.slice(5),
          value: Math.round(d.predicted_revenue),
          upper: Math.round(d.upper_bound),
          lower: Math.round(d.lower_bound),
        })));
      })
      .catch(() => setChartData([]))
      .finally(() => setLoading(false));
  }, [businessId]);

  if (loading) return (
    <div className="glass-card rounded-xl p-5 h-64 flex items-center
                    justify-center text-gray-500 text-sm animate-pulse">
      {t.loading}
    </div>
  );

  return (
    <div className="glass-card rounded-xl p-5 space-y-3">
      <div className="flex items-center gap-2">
        <BarChart2 size={18} className="text-brand-gold" />
        <span className="font-semibold text-white text-sm">{t.forecast}</span>
        <span className="text-xs text-gray-500 ms-auto">{t.nextPeriod}</span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData}
          margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#C9A84C" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#C9A84C" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#2A5298" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#2A5298" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1E2D42" />
          <XAxis dataKey="date"
            tick={{ fill: "#6B7280", fontSize: 11 }}
            tickLine={false} axisLine={false} />
          <YAxis
            tick={{ fill: "#6B7280", fontSize: 11 }}
            tickLine={false} axisLine={false}
            tickFormatter={v => `${(v / 1000).toFixed(0)}K`} />
          <Tooltip
            contentStyle={{
              background: "#162030", border: "1px solid #1E2D42",
              borderRadius: "8px", fontSize: "12px",
            }}
            labelStyle={{ color: "#9CA3AF" }}
            formatter={v => [`SAR ${fmtFull(v)}`, ""]}
          />
          {/* Confidence band */}
          <Area type="monotone" dataKey="upper"
            stroke="none" fill="url(#bandGrad)" />
          <Area type="monotone" dataKey="lower"
            stroke="none" fill="#0F1923" />
          {/* Forecast line */}
          <Area type="monotone" dataKey="value"
            stroke="#C9A84C" strokeWidth={2}
            fill="url(#goldGrad)" dot={false}
            activeDot={{ r: 4, fill: "#C9A84C" }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Recent Transactions ───────────────────────────────────────
function TransactionsTable({ transactions, t, isRTL }) {
  if (!transactions?.length) return <PanelSkeleton />;

  return (
    <div className="glass-card rounded-xl p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Activity size={18} className="text-brand-gold" />
        <span className="font-semibold text-white text-sm">{t.recentTx}</span>
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
            {transactions.slice(0, 8).map((tx, i) => (
              <tr key={i} className="hover:bg-surface-hover transition-colors">
                <td className="py-2 text-gray-400">
                  {tx.timestamp?.slice(11, 16) ?? "—"}
                </td>
                <td className="py-2 text-end font-medium text-white">
                  {fmtFull(tx.amount_sar)} {t.sar}
                </td>
                <td className="py-2 text-end text-gray-500 hidden sm:table-cell capitalize">
                  {tx.payment_method ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Expense Breakdown ─────────────────────────────────────────
function ExpenseBreakdown({ dscr, t, isRTL }) {
  if (!dscr?.expense_breakdown) return <PanelSkeleton />;

  const { cogs_ratio, labor_ratio, overhead_ratio } = dscr.expense_breakdown;
  const net = Math.max(0, 1 - (dscr.expense_ratio ?? 0));

  const bars = [
    { label: isRTL ? "تكلفة البضاعة" : "COGS",        value: cogs_ratio,     color: "bg-status-red" },
    { label: isRTL ? "العمالة"       : "Labor",         value: labor_ratio,    color: "bg-status-yellow" },
    { label: isRTL ? "التشغيل"       : "Overhead",      value: overhead_ratio, color: "bg-status-blue" },
    { label: isRTL ? "صافي الربح"    : "Net Margin",    value: net,            color: "bg-status-green" },
  ];

  return (
    <div className="glass-card rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-2">
        <CreditCard size={18} className="text-brand-gold" />
        <span className="font-semibold text-white text-sm">
          {isRTL ? "توزيع التكاليف (Model 2)" : "Expense Breakdown (Model 2)"}
        </span>
      </div>

      {/* Stacked bar */}
      <div className="h-3 rounded-full overflow-hidden flex">
        {bars.map((b, i) => (
          <div key={i}
            className={`${b.color} transition-all duration-700`}
            style={{ width: `${b.value * 100}%` }} />
        ))}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2">
        {bars.map((b, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div className={`w-2.5 h-2.5 rounded-sm ${b.color} shrink-0`} />
            <span className="text-gray-400">{b.label}</span>
            <span className="text-white font-medium ms-auto">
              {(b.value * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-500 pt-1 border-t border-surface-border">
        {isRTL ? "المصدر: " : "Source: "}
        <span className="text-brand-gold">{dscr.expense_source ?? "ai_derived"}</span>
      </div>
    </div>
  );
}

// ── MAIN ──────────────────────────────────────────────────────
export default function Dashboard() {
  const { t, isRTL } = useLang();
  const [selectedBiz, setSelectedBiz] = useState("cafe");
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const fetchData = useCallback((bizId) => {
    setLoading(true);
    setError(null);
    getDashboard(bizId)
      .then(res => setData(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(selectedBiz); }, [selectedBiz, fetchData]);

  const handleBizChange = (id) => {
    setSelectedBiz(id);
    setData(null);
  };

  const dscr         = data?.dscr;
  const fraud        = data?.fraud;
  const summary      = data?.summary;
  const transactions = data?.recent_transactions;

  /* Dynamic limit badge colour */
  const dynPct = dscr?.dynamic_credit_limit?.limit_change_pct ?? 0;
  const dynBadgeColor =
    dynPct > 0  ? "text-status-green bg-status-green/10" :
    dynPct < 0  ? "text-status-red bg-status-red/10" :
                  "text-gray-400 bg-surface-dark";

  return (
    <div className="space-y-5">

      {/* Title + refresh */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t.dashboardTitle}</h1>
        <button
          onClick={() => fetchData(selectedBiz)}
          className="flex items-center gap-1.5 text-xs text-gray-400
                     hover:text-brand-gold transition-colors"
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          {isRTL ? "تحديث" : "Refresh"}
        </button>
      </div>

      {/* Business selector */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {BUSINESSES.map(biz => (
          <button
            key={biz.id}
            onClick={() => handleBizChange(biz.id)}
            className={`shrink-0 px-4 py-2 rounded-lg text-sm font-medium
                        transition-all whitespace-nowrap
                        ${selectedBiz === biz.id
                          ? "bg-brand-blue text-white shadow-lg"
                          : "glass-card text-gray-400 hover:text-white"}`}
          >
            {isRTL ? biz.nameAr : biz.nameEn}
          </button>
        ))}
      </div>

      {/* Error banner */}
      {error && (
        <div className="glass-card rounded-xl p-4 border border-status-red/30
                        text-status-red text-sm flex items-center gap-2">
          <XCircle size={16} />
          {t.error}: {error}
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">

        <KPICard
          icon={Activity}
          iconColor="text-brand-gold"
          iconBg="bg-brand-gold/10"
          label={t.totalRevenue}
          value={summary ? `SAR ${fmt(summary.total_revenue_sar)}` : "—"}
          sub={t.period}
          badge={summary ? `${fmt(summary.avg_daily_revenue_sar)}/day` : null}
          badgeColor="text-gray-400 bg-surface-dark"
        />

        <KPICard
          icon={CreditCard}
          iconColor="text-status-green"
          iconBg="bg-status-green/10"
          label={t.dynamicLimit}
          value={dscr?.dynamic_credit_limit
            ? `SAR ${fmt(dscr.dynamic_credit_limit.dynamic_limit_sar)}`
            : dscr ? `SAR ${fmt(dscr.approved_credit_limit_sar)}` : "—"}
          sub={dscr?.dynamic_credit_limit?.trend_direction ?? null}
          badge={dscr?.dynamic_credit_limit
            ? `${dynPct > 0 ? "+" : ""}${dynPct.toFixed(1)}%`
            : null}
          badgeColor={dynBadgeColor}
        />

        <KPICard
          icon={BarChart2}
          iconColor="text-status-blue"
          iconBg="bg-status-blue/10"
          label={t.dscrScore}
          value={dscr ? dscr.dscr_score?.toFixed(2) : "—"}
          sub={dscr
            ? (isRTL
                ? `المخاطر: ${dscr.risk_tier}`
                : `Risk: ${dscr.risk_tier?.replace(/_/g, " ")}`)
            : null}
          badge={dscr?.risk_tier ?? null}
          badgeColor={`${RISK_BADGE[dscr?.risk_tier] ?? "text-gray-400 bg-surface-dark"} text-xs`}
        />

        <KPICard
          icon={Zap}
          iconColor="text-brand-gold"
          iconBg="bg-brand-gold/10"
          label={t.interestRate}
          value={dscr ? `${(dscr.final_interest_rate * 100).toFixed(2)}%` : "—"}
          sub={dscr?.sustainability_eligible
            ? (isRTL ? "يشمل خصم الاستدامة" : "Includes green discount")
            : null}
          badge={dscr?.sustainability_eligible ? (isRTL ? "أخضر 🌿" : "Green 🌿") : null}
          badgeColor="text-emerald-400 bg-emerald-400/10"
        />

      </div>

      {/* Row 2: Fraud + Energy */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <FraudPanel  fraud={fraud} t={t} isRTL={isRTL} />
        <EnergyPanel dscr={dscr}   t={t} isRTL={isRTL} />
      </div>

      {/* Row 3: Forecast chart */}
      <ForecastChart businessId={selectedBiz} t={t} isRTL={isRTL} />

      {/* Row 4: Transactions + Expense */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <TransactionsTable transactions={transactions} t={t} isRTL={isRTL} />
        <ExpenseBreakdown  dscr={dscr}                t={t} isRTL={isRTL} />
      </div>

    </div>
  );
}
