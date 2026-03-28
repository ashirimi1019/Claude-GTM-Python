"use client";
import React, { useEffect, useState, useRef } from "react";
import {
  Building2, Search, Globe, Users, Briefcase, Calendar, Loader2,
  ExternalLink, Download, FileSpreadsheet, ChevronDown, ChevronUp,
  Zap, Database,
} from "lucide-react";
import { createClient } from "@/lib/supabase";
import { cn } from "@/lib/utils";
import { exportToXlsx } from "@/lib/export-xlsx";
import { formatIndustry } from "@/lib/industry-labels";

type Company = {
  id: string;
  domain: string;
  name: string;
  employee_count: number | null;
  company_size: string | null;
  funding_stage: string | null;
  industry: string | null;
  country: string;
  fit_score: number;
  created_at: string;
  evidence: { title: string; type: string; source: string }[];
  // Signal quality fields (migration 008)
  signal_confidence: number | null;
  freshness_bucket: string | null;
  final_tier: string | null;
  signal_quality_reasons: string[] | null;
  signal_data_source: string | null;
  latest_posted_at: string | null;
  // ICP Builder fields (migration 012)
  icp_score: number | null;
  icp_tier: string | null;
  icp_confidence: number | null;
  icp_stage: string | null;
};

function SignalBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    job_post: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    funding: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    tech_signal: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    news: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs border",
        styles[type] ?? "bg-neutral-800 text-neutral-400 border-neutral-700",
      )}
    >
      {type.replace("_", " ")}
    </span>
  );
}

const FRESHNESS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  fresh:   { bg: "bg-emerald-500/15", text: "text-emerald-400", label: "Fresh" },
  recent:  { bg: "bg-sky-500/15",     text: "text-sky-400",     label: "Recent" },
  aging:   { bg: "bg-amber-500/15",   text: "text-amber-400",   label: "Aging" },
  stale:   { bg: "bg-red-500/15",     text: "text-red-400",     label: "Stale" },
  unknown: { bg: "bg-neutral-700/40", text: "text-neutral-500", label: "Unknown" },
};

const TIER_STYLES: Record<string, { ring: string; text: string }> = {
  hot:    { ring: "border-orange-500/40", text: "text-orange-400" },
  strong: { ring: "border-emerald-500/40", text: "text-emerald-400" },
  warm:   { ring: "border-sky-500/40", text: "text-sky-400" },
  low:    { ring: "border-neutral-600", text: "text-neutral-500" },
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "bg-emerald-500" :
    pct >= 45 ? "bg-sky-500" :
    pct >= 25 ? "bg-amber-500" :
    "bg-red-500";
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-14 h-1.5 rounded-full bg-neutral-800 overflow-hidden">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums text-neutral-400">{pct}%</span>
    </div>
  );
}

function SignalQualityCell({ company }: { company: Company }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const { signal_confidence, freshness_bucket, final_tier, signal_quality_reasons, signal_data_source, latest_posted_at } = company;

  // No signal quality data yet (pre-migration 008 rows)
  if (signal_confidence == null) {
    return <span className="text-neutral-600 text-xs">—</span>;
  }

  const freshness = FRESHNESS_STYLES[freshness_bucket ?? "unknown"] ?? FRESHNESS_STYLES.unknown;
  const tier = TIER_STYLES[final_tier ?? "low"] ?? TIER_STYLES.low;
  const reasons = signal_quality_reasons ?? [];

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex flex-col gap-1.5 text-left group"
        aria-expanded={open}
      >
        {/* Row 1: freshness bucket + final tier */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className={cn("inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium", freshness.bg, freshness.text)}>
            {freshness.label}
          </span>
          <span className={cn("inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wide", tier.ring, tier.text)}>
            {final_tier ?? "—"}
          </span>
          {signal_data_source === "apollo_job_postings" && (
            <span title="Enriched via Apollo job postings API">
              <Zap className="h-3 w-3 text-orange-400/70" />
            </span>
          )}
        </div>
        {/* Row 2: confidence bar */}
        <div className="flex items-center gap-1">
          <ConfidenceBar value={signal_confidence} />
          {reasons.length > 0 && (
            open
              ? <ChevronUp className="h-3 w-3 text-neutral-600 group-hover:text-neutral-400 transition-colors" />
              : <ChevronDown className="h-3 w-3 text-neutral-600 group-hover:text-neutral-400 transition-colors" />
          )}
        </div>
      </button>

      {/* Expandable reasoning panel */}
      {open && reasons.length > 0 && (
        <div className="absolute left-0 top-full mt-1.5 z-50 w-72 rounded-lg bg-neutral-950 border border-neutral-700 shadow-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-neutral-500">Signal Reasoning</span>
            {signal_data_source && (
              <span className="flex items-center gap-1 text-[10px] text-neutral-600">
                <Database className="h-2.5 w-2.5" />
                {signal_data_source === "apollo_job_postings" ? "Apollo job postings" : "Bulk search"}
              </span>
            )}
          </div>
          {latest_posted_at && (
            <div className="text-[10px] text-neutral-500 mb-2">
              Latest posting: <span className="text-neutral-300">{new Date(latest_posted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
            </div>
          )}
          <ul className="space-y-1.5">
            {reasons.map((r, i) => (
              <li key={i} className="text-xs text-neutral-300 leading-snug flex gap-2">
                <span className="text-neutral-600 mt-0.5 shrink-0">›</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const supabase = createClient();
    supabase
      .from("companies")
      .select(`id, domain, name, employee_count, company_size, funding_stage, industry, country,
               fit_score, created_at,
               signal_confidence, freshness_bucket, final_tier, signal_quality_reasons, signal_data_source, latest_posted_at,
               icp_score, icp_tier, icp_confidence, icp_stage,
               evidence(title, type, source)`)
      .order("fit_score", { ascending: false })
      .order("created_at", { ascending: false })
      .limit(500)
      .then(({ data }: { data: Company[] | null }) => {
        if (data) setCompanies(data);
        setLoading(false);
      });
  }, []);

  const filtered = companies.filter(
    (c) =>
      !search ||
      c.name?.toLowerCase().includes(search.toLowerCase()) ||
      c.domain?.toLowerCase().includes(search.toLowerCase()) ||
      c.industry?.toLowerCase().includes(search.toLowerCase()),
  );

  const handleCsvExport = () => {
    const csvEscape = (val: string | number | null | undefined): string => {
      const s = String(val ?? "");
      if (s.includes(",") || s.includes('"') || s.includes("\n")) {
        return `"${s.replace(/"/g, '""')}"`;
      }
      return s;
    };
    const csv = [
      "Company,Domain,Industry,Employees,Funding Stage,Country,ICP Score,Signal Confidence,Freshness,Final Tier,Signal Source,Signal Reasons,Signals",
      ...filtered.map((c) =>
        [
          csvEscape(c.name),
          csvEscape(c.domain),
          csvEscape(c.industry),
          csvEscape(c.employee_count ?? c.company_size),
          csvEscape(c.funding_stage),
          csvEscape(c.country ?? "US"),
          csvEscape(c.fit_score),
          csvEscape(c.signal_confidence != null ? Math.round(c.signal_confidence * 100) + "%" : ""),
          csvEscape(c.freshness_bucket),
          csvEscape(c.final_tier),
          csvEscape(c.signal_data_source),
          csvEscape(c.signal_quality_reasons?.join(" | ")),
          csvEscape(c.evidence?.map((e) => e.type).join("; ")),
        ].join(","),
      ),
    ].join("\n");
    const bom = "\uFEFF";
    const url = URL.createObjectURL(new Blob([bom + csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "companies.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleXlsxExport = () => {
    exportToXlsx(
      filtered.map((c) => ({
        Company: c.name ?? "",
        Domain: c.domain,
        Industry: c.industry ?? "",
        Employees: c.employee_count ?? c.company_size ?? "",
        "Funding Stage": c.funding_stage ?? "",
        Country: c.country ?? "US",
        "ICP Score": c.fit_score,
        "Signal Confidence": c.signal_confidence != null ? Math.round(c.signal_confidence * 100) + "%" : "",
        "Freshness": c.freshness_bucket ?? "",
        "Final Tier": c.final_tier ?? "",
        "Signal Source": c.signal_data_source ?? "",
        "Signal Reasons": c.signal_quality_reasons?.join(" | ") ?? "",
        Signals: c.evidence?.map((e) => e.type).join("; ") ?? "",
        Added: new Date(c.created_at).toLocaleDateString(),
      })),
      "companies",
      "Companies",
    );
  };

  return (
    <div className="p-6 md:p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-bold text-white">Companies</h1>
          <p className="text-sm text-neutral-500 mt-0.5">
            {loading ? "Loading…" : `${companies.length.toLocaleString()} discovered`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCsvExport}
            disabled={filtered.length === 0}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="h-3.5 w-3.5" />
            {filtered.length > 0 ? `Export ${filtered.length.toLocaleString()} (CSV)` : "Export CSV"}
          </button>
          <button
            onClick={handleXlsxExport}
            disabled={filtered.length === 0}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-700/30 hover:bg-emerald-700/50 border border-emerald-700/50 text-emerald-300 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <FileSpreadsheet className="h-3.5 w-3.5" />
            {filtered.length > 0 ? `Export ${filtered.length.toLocaleString()} (XLSX)` : "Export XLSX"}
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          {
            label: "Total Companies",
            value: loading ? "—" : companies.length.toLocaleString(),
            icon: Building2,
            color: "bg-indigo-500/20",
          },
          {
            label: "With Hiring Signal",
            value: loading ? "—" : companies
              .filter((c) => c.evidence?.some((e) => e.type === "job_post"))
              .length.toLocaleString(),
            icon: Briefcase,
            color: "bg-violet-500/20",
          },
          {
            label: "ICP Qualified",
            value: loading ? "—" : (() => {
              const withIcp = companies.filter((c) => c.icp_tier != null);
              if (withIcp.length > 0) return withIcp.length.toLocaleString();
              return companies.filter((c) => c.fit_score >= 170).length.toLocaleString();
            })(),
            icon: Globe,
            color: "bg-emerald-500/20",
          },
          {
            label: "Tier A + B",
            value: loading ? "—" : (() => {
              const ab = companies.filter((c) => c.icp_tier === 'A' || c.icp_tier === 'B');
              return ab.length > 0 ? ab.length.toLocaleString() : '—';
            })(),
            icon: Users,
            color: "bg-rose-500/20",
          },
        ].map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="rounded-xl bg-neutral-900 border border-neutral-800 p-5 flex flex-col gap-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-500 uppercase tracking-wider">{label}</span>
              <div className={cn("p-1.5 rounded-lg", color)}>
                <Icon className="h-3.5 w-3.5 text-white/80" />
              </div>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
        <input
          type="text"
          placeholder="Search by name, domain, or industry…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-neutral-900 border border-neutral-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-neutral-600 transition-colors"
        />
        {search && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-neutral-500">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="rounded-xl bg-neutral-900 border border-neutral-800 overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-neutral-500">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading companies…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center">
            <Building2 className="h-8 w-8 text-neutral-700 mx-auto mb-3" />
            <p className="text-neutral-400 text-sm font-medium">
              {search ? "No companies match your search" : "No companies discovered yet"}
            </p>
            <p className="text-neutral-600 text-xs mt-1">
              {search ? (
                <button
                  onClick={() => setSearch("")}
                  className="text-indigo-400 hover:underline"
                >
                  Clear search
                </button>
              ) : (
                "Open a campaign and run Skill 4 to discover ICP-matched companies."
              )}
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                {["Company", "Domain", "Industry", "Employees", "ICP Score", "Signal Quality", "Country", "Signals", "Added"].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-5 py-3 text-left text-xs text-neutral-500 font-medium"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-neutral-800/60 last:border-0 hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-5 py-4">
                    <div className="font-medium text-white text-sm">{c.name || "—"}</div>
                    {c.funding_stage && (
                      <div className="text-xs text-neutral-500 mt-0.5">{c.funding_stage}</div>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <a
                      href={`https://${c.domain}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-xs font-mono"
                    >
                      {c.domain}
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  </td>
                  <td className="px-5 py-4 text-neutral-400 text-xs max-w-[140px] truncate">
                    {formatIndustry(c.industry)}
                  </td>
                  <td className="px-5 py-4 text-neutral-400 text-xs tabular-nums">
                    {c.employee_count ? c.employee_count.toLocaleString() : '—'}
                  </td>
                  <td className="px-5 py-4">
                    {c.icp_score != null ? (
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-xs font-semibold ${
                            c.icp_tier === 'A' ? 'text-emerald-400'
                            : c.icp_tier === 'B' ? 'text-yellow-400'
                            : c.icp_tier === 'C' ? 'text-orange-400'
                            : 'text-neutral-400'
                          }`}
                        >
                          {c.icp_score}
                        </span>
                        {c.icp_tier && (
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                              c.icp_tier === 'A' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : c.icp_tier === 'B' ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30'
                              : 'bg-orange-500/15 text-orange-400 border border-orange-500/30'
                            }`}
                          >
                            {c.icp_tier}
                          </span>
                        )}
                        {c.icp_stage === 'stage2' && (
                          <span className="text-[8px] text-blue-400/60">✦</span>
                        )}
                      </div>
                    ) : (
                      <span
                        className={`text-xs font-semibold ${
                          c.fit_score >= 170 ? "text-emerald-400"
                          : c.fit_score >= 120 ? "text-yellow-400"
                          : c.fit_score > 0 ? "text-neutral-400"
                          : "text-neutral-600"
                        }`}
                      >
                        {c.fit_score > 0 ? c.fit_score : "—"}
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <SignalQualityCell company={c} />
                  </td>
                  <td className="px-5 py-4 text-neutral-400 text-xs">{c.country && c.country !== 'Unknown' ? c.country : '—'}</td>
                  <td className="px-5 py-4">
                    <div className="flex flex-wrap gap-1">
                      {c.evidence?.slice(0, 2).map((e, i) => (
                        <SignalBadge key={i} type={e.type} />
                      ))}
                      {(c.evidence?.length ?? 0) > 2 && (
                        <span className="text-xs text-neutral-600">
                          +{c.evidence.length - 2}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-neutral-500 text-xs">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
