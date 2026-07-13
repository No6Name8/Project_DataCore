import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Briefcase, TrendingUp, TrendingDown, Minus,
  Shield, AlertTriangle, XCircle,
  ChevronUp, ChevronDown, ChevronsLeft, ChevronsRight,
  ChevronLeft, ChevronRight, Search, RefreshCw,
} from "lucide-react";
import { getPortfolioSummary, getPortfolioStats } from "../services/api";

const PAGE_SIZE = 50;

// ── Archetype letter → human name (from models/business_classifier.py labels) ─
const ARCH_NAMES = {
  A: "Food & Beverage",
  B: "Retail",
  C: "Automotive (High-Value)",
  D: "Real Estate / Brokerage",
  E: "Services",
  F: "Essential Services",
  G: "Supermarket",
  H: "Electronics",
  I: "Vehicle Dealer",
  J: "Personal Services",
  K: "Medical / Dental",
  L: "Fashion & Boutique",
};

// ── Archetype badge colours ───────────────────────────────────────────────────
const ARCH_COLORS = {
  A: "bg-orange-500/20 text-orange-300 border-orange-500/40",
  B: "bg-blue-500/20  text-blue-300  border-blue-500/40",
  C: "bg-red-500/20   text-red-300   border-red-500/40",
  D: "bg-purple-500/20 text-purple-300 border-purple-500/40",
  E: "bg-teal-500/20  text-teal-300  border-teal-500/40",
  F: "bg-cyan-500/20  text-cyan-300  border-cyan-500/40",
  G: "bg-green-500/20 text-green-300 border-green-500/40",
  H: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
  I: "bg-pink-500/20  text-pink-300  border-pink-500/40",
  J: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
  K: "bg-rose-500/20  text-rose-300  border-rose-500/40",
  L: "bg-violet-500/20 text-violet-300 border-violet-500/40",
};

// ── Risk tier colours ─────────────────────────────────────────────────────────
const RISK_COLORS = {
  very_low: "text-emerald-400",
  low:      "text-green-400",
  medium:   "text-yellow-400",
  high:     "text-orange-400",
  critical: "text-red-400",
};

// ── Trend icons ───────────────────────────────────────────────────────────────
function TrendIcon({ dir }) {
  if (dir === "growing")   return <TrendingUp  size={14} className="text-emerald-400" />;
  if (dir === "declining") return <TrendingDown size={14} className="text-red-400" />;
  return <Minus size={14} className="text-gray-500" />;
}

// ── Fraud dot ─────────────────────────────────────────────────────────────────
function FraudDot({ status }) {
  if (status === "clean")   return <Shield       size={14} className="text-emerald-400" />;
  if (status === "flagged") return <AlertTriangle size={14} className="text-yellow-400" />;
  return <XCircle size={14} className="text-red-400" />;
}

// ── Animated counter ──────────────────────────────────────────────────────────
function Counter({ target, prefix = "", suffix = "", decimals = 0, duration = 800 }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!target) { setVal(target); return; }
    let rafId;
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      setVal(target * progress);
      if (progress < 1) { rafId = requestAnimationFrame(step); }
      else setVal(target);
    };
    rafId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId);
  }, [target, duration]);

  const formatted = decimals > 0
    ? val.toFixed(decimals)
    : Math.round(val).toLocaleString();
  return <>{prefix}{formatted}{suffix}</>;
}

// ── Sort header ───────────────────────────────────────────────────────────────
function SortTh({ label, field, sortField, sortDir, onSort }) {
  const active = sortField === field;
  return (
    <th
      className="px-3 py-3 text-left text-xs font-semibold text-gray-400
                 uppercase tracking-wide cursor-pointer select-none
                 hover:text-white whitespace-nowrap"
      onClick={() => onSort(field)}
    >
      <span className="flex items-center gap-1">
        {label}
        {active
          ? sortDir === "asc"
            ? <ChevronUp size={12} />
            : <ChevronDown size={12} />
          : <span className="opacity-30"><ChevronDown size={12} /></span>}
      </span>
    </th>
  );
}

// ── Stats card ────────────────────────────────────────────────────────────────
function StatsCard({ icon: Icon, label, value, sub, color = "text-brand-gold" }) {
  return (
    <div className="glass-card rounded-xl p-4 flex items-start gap-3">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${color} bg-white/5`}>
        <Icon size={20} />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-xs text-gray-400 mt-0.5">{label}</div>
        {sub && <div className="text-xs text-gray-600 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Portfolio() {
  const navigate = useNavigate();

  const [summary, setSummary]   = useState(null);
  const [stats, setStats]       = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  // Filters
  const [search, setSearch]         = useState("");
  const [filterArch, setFilterArch] = useState("all");
  const [filterRisk, setFilterRisk] = useState("all");
  const [filterFraud, setFilterFraud] = useState("all");
  const [filterTrend, setFilterTrend] = useState("all");

  // Sort
  const [sortField, setSortField] = useState("dscr_score");
  const [sortDir, setSortDir]     = useState("desc");

  // Pagination
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, statRes] = await Promise.all([
        getPortfolioSummary(),
        getPortfolioStats(),
      ]);
      setSummary(sumRes.data);
      setStats(statRes.data);
    } catch (e) {
      setError(
        e?.response?.data?.error ||
        "Could not load portfolio. Run: python data/generate_portfolio.py"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Derived filtered + sorted list
  const filtered = useMemo(() => {
    if (!summary) return [];
    let rows = summary;

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      rows = rows.filter(
        (r) => r.name.toLowerCase().includes(q) || r.business_id.includes(q)
      );
    }
    if (filterArch !== "all") rows = rows.filter((r) => r.archetype_key === filterArch);
    if (filterRisk !== "all") rows = rows.filter((r) => r.risk_tier === filterRisk);
    if (filterFraud !== "all") rows = rows.filter((r) => r.fraud_status === filterFraud);
    if (filterTrend !== "all") rows = rows.filter((r) => r.revenue_trend === filterTrend);

    rows = [...rows].sort((a, b) => {
      const av = a[sortField] ?? 0;
      const bv = b[sortField] ?? 0;
      if (typeof av === "string") return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === "asc" ? av - bv : bv - av;
    });

    return rows;
  }, [summary, search, filterArch, filterRisk, filterFraud, filterTrend, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows   = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleSort = (field) => {
    if (sortField === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortField(field); setSortDir("desc"); }
    setPage(1);
  };

  const handleFilterChange = (setter) => (e) => { setter(e.target.value); setPage(1); };
  const handleSearch = (e) => { setSearch(e.target.value); setPage(1); };

  // ── Render ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-gray-400 gap-4">
        <RefreshCw size={32} className="animate-spin text-brand-gold" />
        <p>Loading 500-business portfolio…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <XCircle size={40} className="text-red-400" />
        <p className="text-red-300 text-center max-w-md">{error}</p>
        <button
          onClick={load}
          className="px-4 py-2 rounded-lg bg-brand-gold text-brand-blueDark
                     font-semibold text-sm hover:opacity-90"
        >
          Retry
        </button>
      </div>
    );
  }

  const selectCls =
    "bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm " +
    "text-gray-300 focus:outline-none focus:border-brand-gold";

  return (
    <div className="space-y-6">

      {/* Page header */}
      <div className="flex items-center gap-3">
        <Briefcase size={24} className="text-brand-gold" />
        <div>
          <h1 className="text-xl font-bold text-white">SME Portfolio</h1>
          <p className="text-sm text-gray-400">
            507 businesses · 12 behavioral archetypes
          </p>
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatsCard
            icon={Briefcase}
            label="Total Businesses"
            value={<Counter target={stats.total_businesses} />}
            color="text-brand-gold"
          />
          <StatsCard
            icon={TrendingUp}
            label="SME Transition Ready"
            value={<Counter target={stats.sme_transition_ready} />}
            sub={`${((stats.sme_transition_ready / stats.total_businesses) * 100).toFixed(1)}% of portfolio`}
            color="text-emerald-400"
          />
          <StatsCard
            icon={Shield}
            label="Avg DSCR Score"
            value={<Counter target={stats.avg_dscr_score} decimals={2} />}
            sub="Debt Service Coverage"
            color="text-blue-400"
          />
          <StatsCard
            icon={Briefcase}
            label="Avg Daily Revenue"
            value={<Counter target={stats.avg_daily_revenue_sar} prefix="SAR " />}
            sub="Per business"
            color="text-purple-400"
          />
        </div>
      )}

      {/* Filter row */}
      <div className="flex flex-wrap gap-2 items-center">
        {/* Search */}
        <div className="relative flex-1 min-w-[160px] max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search name or ID…"
            value={search}
            onChange={handleSearch}
            className="w-full bg-surface-card border border-surface-border rounded-lg
                       pl-8 pr-3 py-2 text-sm text-gray-300 focus:outline-none
                       focus:border-brand-gold placeholder:text-gray-600"
          />
        </div>

        <select className={selectCls} value={filterArch} onChange={handleFilterChange(setFilterArch)}>
          <option value="all">All Archetypes</option>
          {Object.entries(ARCH_NAMES).map(([k, name]) => (
            <option key={k} value={k}>{k} · {name}</option>
          ))}
        </select>

        <select className={selectCls} value={filterRisk} onChange={handleFilterChange(setFilterRisk)}>
          <option value="all">All Risk Tiers</option>
          {["very_low","low","medium","high","critical"].map((t) => (
            <option key={t} value={t}>{t.replace("_"," ")}</option>
          ))}
        </select>

        <select className={selectCls} value={filterFraud} onChange={handleFilterChange(setFilterFraud)}>
          <option value="all">All Fraud Status</option>
          {["clean","flagged","frozen"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select className={selectCls} value={filterTrend} onChange={handleFilterChange(setFilterTrend)}>
          <option value="all">All Trends</option>
          {["growing","steady","declining"].map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <span className="text-xs text-gray-500 ml-auto">
          {filtered.length} results
        </span>
      </div>

      {/* Table */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border bg-surface-card/50">
                <SortTh label="Business"     field="name"              {...{sortField, sortDir, onSort: handleSort}} />
                <SortTh label="Archetype"    field="archetype_key"     {...{sortField, sortDir, onSort: handleSort}} />
                <SortTh label="DSCR"         field="dscr_score"        {...{sortField, sortDir, onSort: handleSort}} />
                <SortTh label="Risk"         field="risk_tier"         {...{sortField, sortDir, onSort: handleSort}} />
                <SortTh label="Fraud"        field="fraud_status"      {...{sortField, sortDir, onSort: handleSort}} />
                <SortTh label="Credit Limit" field="credit_limit_sar"  {...{sortField, sortDir, onSort: handleSort}} />
                <SortTh label="Daily Rev"    field="avg_daily_revenue_sar" {...{sortField, sortDir, onSort: handleSort}} />
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  Trend
                </th>
                <th className="px-3 py-3" />
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, i) => (
                <tr
                  key={row.business_id}
                  className={`border-b border-surface-border/50 hover:bg-white/5 cursor-pointer
                              ${i % 2 === 0 ? "" : "bg-white/[0.02]"}`}
                  onClick={() => navigate(`/demo?business=${row.business_id}`)}
                >
                  <td className="px-3 py-3">
                    <div className="font-medium text-white truncate max-w-[180px]">{row.name}</div>
                    <div className="text-xs text-gray-500">{row.business_id}</div>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-semibold
                                     ${ARCH_COLORS[row.archetype_key] ?? "bg-gray-500/20 text-gray-300 border-gray-500/40"}`}>
                      {row.archetype_key}
                    </span>
                  </td>
                  <td className={`px-3 py-3 font-mono font-semibold ${RISK_COLORS[row.risk_tier] ?? ""}`}>
                    {row.dscr_score?.toFixed(2) ?? "—"}
                  </td>
                  <td className={`px-3 py-3 text-xs capitalize ${RISK_COLORS[row.risk_tier] ?? ""}`}>
                    {row.risk_tier?.replace("_"," ")}
                  </td>
                  <td className="px-3 py-3">
                    <span className="flex items-center gap-1.5">
                      <FraudDot status={row.fraud_status} />
                      <span className="text-xs text-gray-400 capitalize">{row.fraud_status}</span>
                    </span>
                  </td>
                  <td className="px-3 py-3 text-gray-300 text-xs whitespace-nowrap">
                    {row.credit_limit_sar > 0
                      ? `SAR ${Math.round(row.credit_limit_sar).toLocaleString()}`
                      : <span className="text-red-400">Ineligible</span>}
                  </td>
                  <td className="px-3 py-3 text-gray-300 text-xs whitespace-nowrap">
                    SAR {Math.round(row.avg_daily_revenue_sar).toLocaleString()}
                  </td>
                  <td className="px-3 py-3">
                    <TrendIcon dir={row.revenue_trend} />
                  </td>
                  <td className="px-3 py-3">
                    <button
                      className="px-3 py-1 rounded-md text-xs font-semibold
                                 bg-brand-gold/10 text-brand-gold border border-brand-gold/30
                                 hover:bg-brand-gold hover:text-brand-blueDark"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/demo?business=${row.business_id}`);
                      }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
              {pageRows.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-3 py-12 text-center text-gray-500">
                    No businesses match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-surface-border">
            <span className="text-xs text-gray-500">
              Page {page} of {totalPages} · {filtered.length} businesses
            </span>
            <div className="flex items-center gap-1">
              <PagBtn onClick={() => setPage(1)} disabled={page === 1}>
                <ChevronsLeft size={14} />
              </PagBtn>
              <PagBtn onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                <ChevronLeft size={14} />
              </PagBtn>

              {/* Page number buttons */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pg;
                if (totalPages <= 5) pg = i + 1;
                else if (page <= 3)  pg = i + 1;
                else if (page >= totalPages - 2) pg = totalPages - 4 + i;
                else pg = page - 2 + i;
                return (
                  <PagBtn key={pg} onClick={() => setPage(pg)} active={pg === page}>
                    {pg}
                  </PagBtn>
                );
              })}

              <PagBtn onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                <ChevronRight size={14} />
              </PagBtn>
              <PagBtn onClick={() => setPage(totalPages)} disabled={page === totalPages}>
                <ChevronsRight size={14} />
              </PagBtn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PagBtn({ children, onClick, disabled, active }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-8 h-8 flex items-center justify-center rounded-md text-xs font-medium
                  ${active
                    ? "bg-brand-gold text-brand-blueDark"
                    : "text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-default"
                  }`}
    >
      {children}
    </button>
  );
}
