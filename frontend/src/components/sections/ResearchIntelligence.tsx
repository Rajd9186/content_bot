"use client";

import { useState, memo } from "react";
import {
  Activity, AlertCircle, ArrowUpDown, BarChart3, BookOpen, ChevronDown,
  ChevronRight, Clock, Database, ExternalLink, Globe, RefreshCw, Search,
  Star, TrendingUp, TrendingDown, Users, Wifi, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Source {
  id: string;
  name: string;
  url: string;
  type: string;
  trustScore: number;
  freshnessScore: number;
  timesUsed: number;
  lastUsed: string;
  status: "active" | "stale" | "unknown";
  competitorRelated: boolean;
}

const MOCK_SOURCES: Source[] = [
  { id: "1", name: "Wikipedia", url: "https://wikipedia.org", type: "Encyclopedia", trustScore: 92, freshnessScore: 88, timesUsed: 142, lastUsed: new Date().toISOString(), status: "active", competitorRelated: false },
  { id: "2", name: "arXiv", url: "https://arxiv.org", type: "Academic", trustScore: 97, freshnessScore: 95, timesUsed: 87, lastUsed: new Date(Date.now() - 3600000).toISOString(), status: "active", competitorRelated: false },
  { id: "3", name: "PubMed", url: "https://pubmed.ncbi.nlm.nih.gov", type: "Academic", trustScore: 98, freshnessScore: 92, timesUsed: 64, lastUsed: new Date(Date.now() - 7200000).toISOString(), status: "active", competitorRelated: false },
  { id: "4", name: "TechCrunch", url: "https://techcrunch.com", type: "News", trustScore: 78, freshnessScore: 99, timesUsed: 53, lastUsed: new Date(Date.now() - 86400000).toISOString(), status: "active", competitorRelated: true },
  { id: "5", name: "The Verge", url: "https://theverge.com", type: "News", trustScore: 75, freshnessScore: 98, timesUsed: 41, lastUsed: new Date(Date.now() - 172800000).toISOString(), status: "active", competitorRelated: true },
  { id: "6", name: "Nature", url: "https://nature.com", type: "Academic", trustScore: 99, freshnessScore: 85, timesUsed: 38, lastUsed: new Date(Date.now() - 259200000).toISOString(), status: "active", competitorRelated: false },
  { id: "7", name: "Reddit", url: "https://reddit.com", type: "Community", trustScore: 45, freshnessScore: 90, timesUsed: 29, lastUsed: new Date(Date.now() - 345600000).toISOString(), status: "stale", competitorRelated: false },
  { id: "8", name: "Stack Overflow", url: "https://stackoverflow.com", type: "Community", trustScore: 72, freshnessScore: 82, timesUsed: 25, lastUsed: new Date(Date.now() - 432000000).toISOString(), status: "stale", competitorRelated: false },
];

const SOURCE_TYPE_ICONS: Record<string, React.ReactNode> = {
  Academic: <Star className="h-3.5 w-3.5 text-violet-400" />,
  Encyclopedia: <BookOpen className="h-3.5 w-3.5 text-blue-400" />,
  News: <Activity className="h-3.5 w-3.5 text-emerald-400" />,
  Community: <Users className="h-3.5 w-3.5 text-amber-400" />,
  default: <Globe className="h-3.5 w-3.5 text-muted-foreground" />,
};

function getScoreColor(score: number) {
  if (score >= 85) return "text-emerald-400";
  if (score >= 65) return "text-amber-400";
  return "text-red-400";
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const color = getScoreColor(score);
  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-[10px]">
        <span className="text-muted-foreground">{label}</span>
        <span className={color + " font-medium"}>{score}%</span>
      </div>
      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color.replace("text-", "bg-"))}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

type SortField = "trust" | "freshness" | "usage" | "name" | "status";
type SortDir = "asc" | "desc";

const SourceCard = memo(function SourceCard({ source, onClick }: { source: Source; onClick?: () => void }) {
  const Icon = SOURCE_TYPE_ICONS[source.type] || SOURCE_TYPE_ICONS.default;
  const scoreColor = getScoreColor(source.trustScore);

  return (
    <div
      onClick={onClick}
      className={cn(
        "group relative rounded-2xl border bg-card/40 p-4 cursor-pointer",
        "hover:bg-card/60 hover:border-border transition-all duration-200",
        source.status === "active" && "border-emerald-500/10",
        source.status === "stale" && "border-amber-500/10 opacity-75",
        source.status === "unknown" && "border-border",
      )}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary">
            {Icon}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h4 className="text-xs font-semibold text-foreground">{source.name}</h4>
              {source.competitorRelated && (
                <span className="text-[9px] px-1 py-0.5 rounded bg-red-500/10 text-red-400 font-medium">Competitor</span>
              )}
            </div>
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-[10px] text-muted-foreground hover:text-violet-400 transition-colors flex items-center gap-0.5"
            >
              <ExternalLink className="h-2.5 w-2.5" />
              {source.type}
            </a>
          </div>
        </div>
        <div className={cn("text-xs font-bold", scoreColor)}>{source.trustScore}%</div>
      </div>

      <div className="space-y-1.5">
        <ScoreBar score={source.trustScore} label="Trust" />
        <ScoreBar score={source.freshnessScore} label="Freshness" />
      </div>

      <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-border/50">
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-0.5">
            <Activity className="h-2.5 w-2.5" />
            {source.timesUsed} uses
          </span>
          <span className="flex items-center gap-0.5">
            <Clock className="h-2.5 w-2.5" />
            {new Date(source.lastUsed).toLocaleDateString()}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              source.status === "active" && "bg-emerald-400",
              source.status === "stale" && "bg-amber-400",
              source.status === "unknown" && "bg-slate-400",
            )}
          />
          <span className="text-[10px] text-muted-foreground capitalize">{source.status}</span>
        </div>
      </div>
    </div>
  );
});

export function ResearchIntelligence() {
  const [sources] = useState<Source[]>(MOCK_SOURCES);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("usage");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [hideCompetitor, setHideCompetitor] = useState(false);

  const filtered = sources
    .filter((s) => {
      if (hideCompetitor && s.competitorRelated) return false;
      if (typeFilter !== "all" && s.type !== typeFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return s.name.toLowerCase().includes(q) || s.type.toLowerCase().includes(q);
      }
      return true;
    })
    .sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "trust": cmp = a.trustScore - b.trustScore; break;
        case "freshness": cmp = a.freshnessScore - b.freshnessScore; break;
        case "usage": cmp = a.timesUsed - b.timesUsed; break;
        case "name": cmp = a.name.localeCompare(b.name); break;
        case "status": cmp = a.status.localeCompare(b.status); break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

  const avgTrust = Math.round(sources.reduce((s, x) => s + x.trustScore, 0) / sources.length);
  const avgFreshness = Math.round(sources.reduce((s, x) => s + x.freshnessScore, 0) / sources.length);
  const activeCount = sources.filter((s) => s.status === "active").length;
  const competitorCount = sources.filter((s) => s.competitorRelated).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/20 to-violet-600/10 border border-violet-500/20 shadow-lg shadow-violet-500/10">
            <Database className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">Research Sources</h2>
            <p className="text-[10px] text-muted-foreground">{sources.length} sources · Trust {avgTrust}% · Freshness {avgFreshness}%</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <Star className="h-3 w-3 text-violet-400" />
            <span className="text-[10px] text-muted-foreground">Avg Trust</span>
          </div>
          <div className={cn("text-lg font-bold", getScoreColor(avgTrust))}>{avgTrust}%</div>
        </div>
        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="h-3 w-3 text-emerald-400" />
            <span className="text-[10px] text-muted-foreground">Avg Freshness</span>
          </div>
          <div className={cn("text-lg font-bold", getScoreColor(avgFreshness))}>{avgFreshness}%</div>
        </div>
        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <Wifi className="h-3 w-3 text-emerald-400" />
            <span className="text-[10px] text-muted-foreground">Active</span>
          </div>
          <div className="text-lg font-bold text-emerald-400">{activeCount}/{sources.length}</div>
        </div>
        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="h-3 w-3 text-red-400" />
            <span className="text-[10px] text-muted-foreground">Competitor</span>
          </div>
          <div className="text-lg font-bold text-red-400">{competitorCount}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-2 rounded-xl bg-secondary/60 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-xl bg-secondary/60 border border-border text-xs text-foreground focus:outline-none focus:border-violet-500"
        >
          <option value="all">All Types</option>
          <option value="Academic">Academic</option>
          <option value="Encyclopedia">Encyclopedia</option>
          <option value="News">News</option>
          <option value="Community">Community</option>
        </select>
        <button
          onClick={() => setHideCompetitor(!hideCompetitor)}
          className={cn(
            "flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-medium transition-colors",
            hideCompetitor ? "bg-red-500/10 border-red-500/20 text-red-400" : "bg-secondary/60 border-border text-muted-foreground hover:text-foreground"
          )}
        >
          <AlertCircle className="h-3 w-3" />
          Hide Competitor
        </button>
        <button
          onClick={() => setSortField(sortField === "usage" ? "trust" : sortField === "trust" ? "freshness" : "usage")}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border bg-secondary/60 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowUpDown className="h-3 w-3" />
          Sort: {sortField}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {filtered.length === 0 ? (
          <div className="col-span-2 text-center py-12 border border-dashed border-border rounded-2xl">
            <p className="text-xs text-muted-foreground">No sources match your filters</p>
          </div>
        ) : (
          filtered.map((source) => (
            <SourceCard key={source.id} source={source} />
          ))
        )}
      </div>

      <div className="rounded-2xl border border-border bg-card/40 p-4">
        <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-violet-400" />
          Source Distribution by Type
        </h3>
        <div className="flex h-3 rounded-full overflow-hidden bg-secondary gap-0.5">
          {(["Academic", "Encyclopedia", "News", "Community"] as const).map((type) => {
            const count = sources.filter((s) => s.type === type).length;
            const pct = (count / sources.length) * 100;
            const colors: Record<string, string> = {
              Academic: "bg-violet-500",
              Encyclopedia: "bg-blue-500",
              News: "bg-emerald-500",
              Community: "bg-amber-500",
            };
            return (
              <div
                key={type}
                className={cn("h-full rounded-full transition-all", colors[type])}
                style={{ width: `${pct}%` }}
                title={`${type}: ${count} (${pct.toFixed(0)}%)`}
              />
            );
          })}
        </div>
        <div className="flex flex-wrap gap-4 mt-3 text-[10px] text-muted-foreground">
          {(["Academic", "Encyclopedia", "News", "Community"] as const).map((type) => {
            const count = sources.filter((s) => s.type === type).length;
            const colors: Record<string, string> = {
              Academic: "bg-violet-500",
              Encyclopedia: "bg-blue-500",
              News: "bg-emerald-500",
              Community: "bg-amber-500",
            };
            return (
              <div key={type} className="flex items-center gap-1.5">
                <div className={cn("w-2 h-2 rounded-full", colors[type])} />
                <span>{type}: {count}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}