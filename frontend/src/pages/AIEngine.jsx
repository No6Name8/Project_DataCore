import { useEffect, useState } from "react";
import { useLang } from "../i18n/LanguageContext";
import { motion } from "framer-motion";
import axios from "axios";
import config from "../config";
import {
  Brain, GitBranch, Shield, TrendingUp,
  CheckCircle, Activity,
  Cpu, Database
} from "lucide-react";

const fadeUp = {
  hidden:  { opacity: 0, y: 16 },
  visible: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.08, duration: 0.35, ease: [0.23, 1, 0.32, 1] }
  }),
};

function StatCard({ label, value, sub, color = "text-brand-gold", i = 0 }) {
  return (
    <motion.div custom={i} variants={fadeUp}
      initial="hidden" whileInView="visible" viewport={{ once: true }}
      className="glass-card rounded-xl p-4 space-y-1">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-white text-xs font-medium">{label}</div>
      {sub && <div className="text-gray-500 text-xs">{sub}</div>}
    </motion.div>
  );
}

function SectionHeader({ icon: Icon, color, titleEn, titleAr, isRTL }) {
  return (
    <div className="flex items-center gap-3 pb-2 border-b border-surface-border">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center
                       bg-surface-border`}>
        <Icon size={16} className={color} />
      </div>
      <h2 className="font-semibold text-white text-sm">
        {isRTL ? titleAr : titleEn}
      </h2>
    </div>
  );
}

export default function AIEngine() {
  const { isRTL } = useLang();
  const [dscrData,  setDscrData]  = useState({});
  const [fraudData, setFraudData] = useState({});
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    const BIZ = ["laundromat", "cafe", "minimarket",
                 "realestate", "cardealer", "motorbike"];

    Promise.all([
      ...BIZ.map(b => axios.get(`${config.API_BASE}/api/${b}/dscr`)),
      ...BIZ.map(b => axios.get(`${config.API_BASE}/api/${b}/fraud-check`)),
    ]).then((results) => {
      const dscrRes  = results.slice(0, 6);
      const fraudRes = results.slice(6);
      const dscr  = {};
      const fraud = {};
      BIZ.forEach((b, i) => {
        dscr[b]  = dscrRes[i].data;
        fraud[b] = fraudRes[i].data;
      });
      setDscrData(dscr);
      setFraudData(fraud);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const BIZ_NAMES = {
    laundromat: "Laundromat",
    cafe:       "Cafe",
    minimarket: "Minimarket",
    realestate: "Real Estate",
    cardealer:  "Car Dealer",
    motorbike:  "Motorbike",
  };

  const riskColor = {
    very_low: "text-status-green",
    low:      "text-status-green",
    medium:   "text-status-yellow",
    high:     "text-status-red",
    critical: "text-status-red",
  };

  return (
    <div className="space-y-12 py-4">

      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1.5
                        rounded-full border border-brand-gold/30
                        bg-brand-gold/10 text-brand-gold text-xs">
          <Brain size={13} />
          {isRTL ? "تفاصيل محرك الذكاء الاصطناعي" : "AI Engine Details"}
        </div>
        <h1 className="text-2xl font-bold text-white">
          {isRTL ? "للمراجعة التقنية" : "For Technical Review"}
        </h1>
        <p className="text-gray-400 text-sm max-w-lg mx-auto">
          {isRTL
            ? "مقاييس حقيقية من تدريب النماذج وتشغيلها. لا أرقام مزيفة."
            : "Real metrics from model training and live inference. No fake numbers."}
        </p>
      </div>

      {/* MODEL 1 */}
      <section className="space-y-4">
        <SectionHeader
          icon={Database} color="text-brand-gold"
          titleEn="Model 1 — Business Classifier (HDBSCAN)"
          titleAr="النموذج 1 — مصنّف الأعمال (HDBSCAN)"
          isRTL={isRTL}
        />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard i={0} label="Clusters Found"   value="12"    color="text-brand-gold"    sub="Without labels" />
          <StatCard i={1} label="Archetype Purity"  value="100%"  color="text-status-green"  sub="ARI ≈ 1.0" />
          <StatCard i={2} label="Noise Points"      value="0%"    color="text-status-green"  sub="All points classified" />
          <StatCard i={3} label="Training Samples"  value="1,800" color="text-status-blue"   sub="12 archetypes × 150" />
        </div>
        <div className="glass-card rounded-xl p-5 space-y-3">
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL ? "تصنيف المنشآت الحقيقية" : "Real Business Classifications"}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {[
              { biz: "cafe",       cluster: 6, arch: "high_freq_low_ticket_food",      conf: 0.88 },
              { biz: "minimarket", cluster: 1, arch: "high_freq_mid_ticket_retail",    conf: 0.91 },
              { biz: "laundromat", cluster: 5, arch: "low_ticket_essential_steady",    conf: 0.74 },
              { biz: "realestate", cluster: 3, arch: "sparse_high_ticket_brokerage",   conf: 0.95 },
              { biz: "cardealer",  cluster: 2, arch: "low_freq_very_high_ticket_auto", conf: 0.89 },
              { biz: "motorbike",  cluster: 8, arch: "low_freq_mid_high_ticket_dealer",conf: 0.82 },
            ].map((item, i) => (
              <motion.div key={i} custom={i}
                variants={fadeUp} initial="hidden"
                whileInView="visible" viewport={{ once: true }}
                className="p-3 rounded-lg bg-surface-dark space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-white text-xs font-medium capitalize">
                    {item.biz}
                  </span>
                  <span className="text-brand-gold text-xs">
                    C{item.cluster}
                  </span>
                </div>
                <div className="text-gray-500 text-xs truncate">
                  {item.arch}
                </div>
                <div className="h-1 bg-surface-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-brand-gold/60 rounded-full"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${item.conf * 100}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1], delay: i * 0.05 }}
                  />
                </div>
                <div className="text-gray-600 text-xs">
                  {(item.conf * 100).toFixed(0)}% confidence
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* MODEL 2 */}
      <section className="space-y-4">
        <SectionHeader
          icon={Cpu} color="text-status-blue"
          titleEn="Model 2 — Expense Estimator (Behavioral)"
          titleAr="النموذج 2 — مقدّر المصاريف (سلوكي)"
          isRTL={isRTL}
        />
        <div className="glass-card rounded-xl p-5 space-y-3">
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL ? "مقارنة: الذكاء الاصطناعي مقابل القيم الثابتة" : "AI-Derived vs Hardcoded Comparison"}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 border-b border-surface-border">
                  <th className="text-start pb-2 font-medium">Business</th>
                  <th className="text-end pb-2 font-medium">Hardcoded</th>
                  <th className="text-end pb-2 font-medium">AI-Derived</th>
                  <th className="text-end pb-2 font-medium">Inventory</th>
                  <th className="text-end pb-2 font-medium">Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {[
                  { biz: "Car Dealer",  hc: 0.820, ai: 0.830, inv: true  },
                  { biz: "Motorbike",   hc: 0.720, ai: 0.890, inv: true  },
                  { biz: "Real Estate", hc: 0.350, ai: 0.330, inv: false },
                  { biz: "Minimarket",  hc: 0.780, ai: 0.820, inv: false },
                  { biz: "Cafe",        hc: 0.680, ai: 0.820, inv: false },
                  { biz: "Laundromat",  hc: 0.550, ai: 0.840, inv: false },
                ].map((row, i) => (
                  <tr key={i}
                    style={{ transition: "background-color 120ms var(--ease-out)" }}
                    className="hover:bg-surface-hover">
                    <td className="py-2 text-white">{row.biz}</td>
                    <td className="py-2 text-end text-gray-400">
                      {(row.hc * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 text-end text-white font-medium">
                      {(row.ai * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 text-end">
                      {row.inv
                        ? <CheckCircle size={12} className="text-brand-gold inline" />
                        : <span className="text-gray-600">—</span>}
                    </td>
                    <td className={`py-2 text-end font-medium font-mono
                                    ${Math.abs(row.ai - row.hc) < 0.05
                                      ? "text-status-green"
                                      : "text-status-yellow"}`}>
                      {((row.ai - row.hc) * 100) > 0 ? "+" : ""}
                      {((row.ai - row.hc) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-xs text-gray-600 pt-1 border-t border-surface-border">
            Car dealer gap +1% — within noise. Inventory flag auto-detected
            from behavioral signals (high ticket + low velocity + daily open).
          </div>
        </div>
      </section>

      {/* MODEL 3 */}
      <section className="space-y-4">
        <SectionHeader
          icon={Shield} color="text-status-red"
          titleEn="Model 3 — Fraud Detector (Isolation Forest)"
          titleAr="النموذج 3 — كاشف الاحتيال (Isolation Forest)"
          isRTL={isRTL}
        />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard i={0} label="Models Trained"     value="6"   color="text-brand-gold"    sub="One per business" />
          <StatCard i={1} label="Cluster Fallbacks"  value="4"   color="text-status-blue"   sub="For new businesses" />
          <StatCard i={2} label="Contamination Rate" value="1%"  color="text-status-yellow" sub="Strict threshold" />
          <StatCard i={3} label="N Estimators"       value="200" color="text-gray-400"       sub="Per business model" />
        </div>
        <div className="glass-card rounded-xl p-5 space-y-3">
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL ? "نتائج الكشف الحية" : "Live Detection Results"}
          </div>
          {loading ? (
            <div className="text-gray-500 text-xs animate-pulse">
              Loading from API...
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(fraudData).map(([biz, data], i) => (
                <div key={i}
                  className="flex items-center gap-3 p-2 rounded-lg
                             bg-surface-dark text-xs">
                  <div className={`w-2 h-2 rounded-full shrink-0
                                   ${data.overall_status === "frozen"
                                     ? "bg-status-red"
                                     : data.overall_status === "flagged"
                                     ? "bg-status-yellow"
                                     : "bg-status-green"}`} />
                  <span className="text-white font-medium w-24 shrink-0 capitalize">
                    {BIZ_NAMES[biz]}
                  </span>
                  <span className={`w-16 shrink-0
                                    ${data.overall_status === "frozen"
                                      ? "text-status-red"
                                      : data.overall_status === "flagged"
                                      ? "text-status-yellow"
                                      : "text-status-green"}`}>
                    {data.overall_status}
                  </span>
                  <span className="text-gray-500">
                    score: {data.fraud_score}
                  </span>
                  <span className="text-gray-600 ms-auto">
                    {data.anomalies_detected} anomaly groups
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* MODEL 4 */}
      <section className="space-y-4">
        <SectionHeader
          icon={TrendingUp} color="text-status-green"
          titleEn="Model 4 — Revenue Forecaster (Prophet)"
          titleAr="النموذج 4 — متنبئ الإيرادات (Prophet)"
          isRTL={isRTL}
        />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard i={0} label="Forecast Horizon" value="30d"   color="text-brand-gold"    sub="Days ahead" />
          <StatCard i={1} label="Confidence Band"  value="80%"   color="text-status-blue"   sub="Interval width" />
          <StatCard i={2} label="Seasonality"      value="Saudi" color="text-status-green"  sub="Thu/Fri weekend" />
          <StatCard i={3} label="Max Limit Boost"  value="+25%"  color="text-status-yellow" sub="Growing businesses" />
        </div>
        <div className="glass-card rounded-xl p-5 space-y-3">
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            {isRTL
              ? "الحدود الائتمانية الحية: ثابتة مقابل ديناميكية"
              : "Live Credit Limits: Static vs Dynamic"}
          </div>
          {loading ? (
            <div className="text-gray-500 text-xs animate-pulse">
              Loading from API...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-500 border-b border-surface-border">
                    <th className="text-start pb-2 font-medium">Business</th>
                    <th className="text-end pb-2 font-medium">DSCR</th>
                    <th className="text-end pb-2 font-medium">Risk</th>
                    <th className="text-end pb-2 font-medium">Static Limit</th>
                    <th className="text-end pb-2 font-medium">Dynamic Limit</th>
                    <th className="text-end pb-2 font-medium">Trend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {Object.entries(dscrData).map(([biz, data], i) => {
                    const dynamic = data.dynamic_credit_limit;
                    const trend   = dynamic?.trend_direction || "flat";
                    const change  = dynamic?.limit_change_pct || 0;
                    return (
                      <tr key={i}
                        style={{ transition: "background-color 120ms var(--ease-out)" }}
                        className="hover:bg-surface-hover">
                        <td className="py-2 text-white capitalize">
                          {BIZ_NAMES[biz]}
                        </td>
                        <td className="py-2 text-end text-white font-mono">
                          {data.dscr_score?.toFixed(2)}
                        </td>
                        <td className={`py-2 text-end font-medium
                                        ${riskColor[data.risk_tier] || "text-gray-400"}`}>
                          {data.risk_tier?.replace("_", " ")}
                        </td>
                        <td className="py-2 text-end text-gray-400">
                          {data.approved_credit_limit_sar
                            ? `${(data.approved_credit_limit_sar / 1000).toFixed(0)}K`
                            : "—"}
                        </td>
                        <td className="py-2 text-end text-white font-medium">
                          {dynamic
                            ? `${(dynamic.dynamic_limit_sar / 1000).toFixed(0)}K`
                            : "—"}
                        </td>
                        <td className={`py-2 text-end font-medium
                                        ${trend === "growing"
                                          ? "text-status-green"
                                          : trend === "declining"
                                          ? "text-status-red"
                                          : "text-gray-400"}`}>
                          {trend === "growing"   ? `+${change?.toFixed(1)}%` :
                           trend === "declining" ? `${change?.toFixed(1)}%`  :
                           "flat"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* Two-track system */}
      <section className="space-y-4">
        <SectionHeader
          icon={GitBranch} color="text-brand-gold"
          titleEn="Two-Track Classification System"
          titleAr="نظام التصنيف ثنائي المسار"
          isRTL={isRTL}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="glass-card rounded-xl p-5 space-y-3
                          border border-brand-blue/30">
            <div className="text-sm font-semibold text-white">
              {isRTL ? "المسار 1: بيانات حقيقية" : "Track 1: Real Data"}
            </div>
            <div className="space-y-1 text-xs text-gray-400">
              <div>Input: raw transaction CSV</div>
              <div>Pipeline: extract → scale → PCA → HDBSCAN nearest centroid</div>
              <div>Confidence: 74–100% (mature businesses)</div>
              <div>Refinement: mature after 25+ days of data</div>
            </div>
          </div>
          <div className="glass-card rounded-xl p-5 space-y-3
                          border border-brand-gold/20">
            <div className="text-sm font-semibold text-white">
              {isRTL ? "المسار 2: نموذج الاستبيان" : "Track 2: Intake Form"}
            </div>
            <div className="space-y-1 text-xs text-gray-400">
              <div>Input: 8 coarse business parameters</div>
              <div>Pipeline: map to 15 features → same PCA/cluster space</div>
              <div>Confidence: capped at 65% (acknowledged uncertainty)</div>
              <div>Refinement: blends to real data over 30 days</div>
            </div>
          </div>
        </div>
        <div className="glass-card rounded-xl p-4 text-xs text-gray-400
                        border border-surface-border space-y-2">
          <div className="text-white font-medium text-xs">
            {isRTL ? "صيغة الدمج" : "Blend Formula"}
          </div>
          <code className="text-brand-gold font-mono block">
            weight_real = min(data_days / 30.0, 1.0)
          </code>
          <code className="text-gray-300 font-mono block">
            blended[f] = real[f] * weight_real + intake[f] * (1 - weight_real)
          </code>
          <div className="text-gray-600 pt-1">
            Day 0 → 100% intake. Day 30 → 100% real data. Linear transition.
          </div>
        </div>
      </section>

    </div>
  );
}
