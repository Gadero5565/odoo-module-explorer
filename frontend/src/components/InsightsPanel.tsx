import { useMemo, useState } from 'react';
import { AlertCircle, ArrowRight, BarChart3, Boxes, ChevronRight, Code2, GitBranch, LoaderCircle, Search, SortDesc } from 'lucide-react';
import type { InsightMetric, InsightSymbol, InsightsResponse } from '../types/insights';
import { rankSymbols, relatedTo, searchSymbols } from '../lib/insights';
import { formatBytes } from '../lib/analysis';
import RelationshipGraph from './RelationshipGraph';

type Props = {
  data: InsightsResponse | null;
  loading: boolean;
  error: string | null;
  onLoad: () => void;
  onJump: (symbol: InsightSymbol) => void;
};
type Tab = 'search' | 'models' | 'relationships' | 'rankings';

const RANK_METRICS: { key: InsightMetric; label: string }[] = [
  { key: 'size_bytes', label: 'Bytes' },
  { key: 'line_count', label: 'Lines' },
  { key: 'complexity', label: 'Complexity' },
];
const tabNames: { key: Tab; title: string }[] = [
  { key: 'search', title: 'Global symbols' },
  { key: 'models', title: 'Odoo models' },
  { key: 'relationships', title: 'Relationships' },
  { key: 'rankings', title: 'Rankings' },
];

function ResultRow({ symbol, onJump, metric }: { symbol: InsightSymbol; onJump: (symbol: InsightSymbol) => void; metric?: InsightMetric }) {
  return <button className="insight-result" onClick={() => onJump(symbol)} title="Jump to this source symbol">
    <span className="insight-symbol-kind">{symbol.kind.replaceAll('_', ' ')}</span>
    <span className="insight-result-body"><strong>{symbol.name}</strong><small>{symbol.relative_path}{symbol.line_start ? `:${symbol.line_start}` : ''}{symbol.owner_model ? ` · ${symbol.owner_model}` : ''}</small></span>
    <span className="insight-metric">{metric === 'complexity' ? (symbol.complexity === null ? '—' : `C ${symbol.complexity}`) : metric === 'line_count' ? `${symbol.line_count} lines` : formatBytes(symbol.size_bytes)}</span>
    <ArrowRight size={14}/>
  </button>;
}

export default function InsightsPanel({ data, loading, error, onLoad, onJump }: Props) {
  const [tab, setTab] = useState<Tab>('search');
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('all');
  const [ownerFilter, setOwnerFilter] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [metric, setMetric] = useState<InsightMetric>('size_bytes');
  const [rankKind, setRankKind] = useState('all');
  const models = data?.models || [];
  const modelName = models.some(model => model.name === selectedModel) ? selectedModel : models[0]?.name || '';
  const model = models.find(item => item.name === modelName);
  const kinds = useMemo(() => [...new Set((data?.symbols || []).map(item => item.kind))].sort(), [data]);
  const filtered = useMemo(() => searchSymbols(data?.symbols || [], query, kind, ownerFilter), [data, query, kind, ownerFilter]);
  const ranked = useMemo(() => rankSymbols((data?.symbols || []).filter(node =>
    (rankKind === 'all' || node.kind === rankKind) && (metric !== 'complexity' || node.complexity !== null)), metric).slice(0, 40), [data, rankKind, metric]);

  return <section className="insights-panel">
    <div className="insight-heading"><div><h2>Advanced Explorer</h2><p>Search symbols across files, inspect Odoo models, and explore declared relationships without starting Odoo.</p></div><button className="refresh-button" disabled={loading} onClick={onLoad}>{loading ? <LoaderCircle size={16} className="spin"/> : <Search size={16}/>} {data ? 'Rebuild index' : 'Build index'}</button></div>
    {error && <div className="error-bar" role="alert"><AlertCircle size={16}/>{error}</div>}
    {loading && <div className="insight-message"><LoaderCircle size={19} className="spin"/> Reading static source files. This may take a moment for large addons…</div>}
    {!data && !loading && <div className="insight-empty"><Search size={26}/><h3>Build a module-wide index</h3><p>Generate searchable symbols, logical model summaries, relation edges, and method rankings. The index is built on demand and kept in browser memory only.</p><button className="primary-button" onClick={onLoad}>Build insights index</button></div>}
    {data && <>
      <div className="insight-stats"><span><Code2 size={15}/> {data.symbols.length.toLocaleString()} indexed symbols</span><span><Boxes size={15}/> {data.models.length} referenced models</span><span><GitBranch size={15}/> {data.relationships.length} relations</span><span>{data.inspected_files} scanned · {data.skipped_files} skipped</span></div>
      {(data.truncated || data.warnings.length > 0) && <details className="insight-warnings"><summary><AlertCircle size={15}/> {data.truncated ? 'Partial index' : 'Parser notes'} — {data.warnings.length} notice(s)</summary>{data.warnings.map((warning, i) => <p key={i}>{warning}</p>)}</details>}
      <nav className="insight-tabs" aria-label="Advanced explorer views">{tabNames.map(item => <button key={item.key} className={tab === item.key ? 'active' : ''} onClick={() => setTab(item.key)}>{item.title}</button>)}</nav>
      {tab === 'search' && <section className="insight-section">
        <div className="insight-controls"><label className="insight-search"><Search size={15}/><input aria-label="Search all symbols" placeholder="Search methods, fields, templates, paths…" value={query} onChange={e => setQuery(e.target.value)}/></label>
          <select aria-label="Symbol type" value={kind} onChange={e => setKind(e.target.value)}><option value="all">All symbol types</option>{kinds.map(k => <option key={k} value={k}>{k.replaceAll('_', ' ')}</option>)}</select>
          <select aria-label="Odoo model" value={ownerFilter} onChange={e => setOwnerFilter(e.target.value)}><option value="">All models / no model</option>{models.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}</select></div>
        <p className="insight-muted">{filtered.length.toLocaleString()} match(es) · Showing first 150 · Click to inspect source</p>
        <div className="insight-results">{filtered.slice(0, 150).map(s => <ResultRow key={s.id} symbol={s} onJump={onJump}/>)}{!filtered.length && <p className="insight-muted">No symbols match the current filters.</p>}</div>
      </section>}
      {(tab === 'models' || tab === 'relationships') && <section className="insight-section">
        <div className="insight-controls"><label className="insight-model-select">Model <select aria-label="Select Odoo model" value={modelName} onChange={e => setSelectedModel(e.target.value)}>{models.map(m => <option key={m.name} value={m.name}>{m.name}{m.defined_here ? '' : ' (referenced)'}</option>)}</select></label></div>
        {!model && <p className="insight-muted">No Odoo model definitions or view references found in this addon.</p>}
        {model && <><div className="insight-model-summary"><h3>{model.name}</h3><span>{model.defined_here ? 'Defined in this addon' : 'Extended or referenced only'}</span><div className="insight-model-counts"><b>{model.source_classes.length} classes</b><b>{model.fields.length} fields</b><b>{model.methods.length} methods</b><b>{model.views.length} views</b><b>{model.relations.length} outgoing links</b></div></div>
          {tab === 'relationships' ? <><RelationshipGraph name={model.name} links={data.relationships} onSelectModel={setSelectedModel}/><h3 className="insight-subtitle">Declared incoming and outgoing relationships</h3><div className="insight-results">{relatedTo(model.name, data.relationships).map((link, i) => <div className="insight-link" key={`${link.relative_path}:${link.line_start}:${i}`}><GitBranch size={15}/><div><strong>{link.source} → {link.target}</strong><small>{link.relation_type} · {link.label} · {link.local_target ? 'Local model definition' : 'Target definition not found in this addon'}</small><small>{link.relative_path}:{link.line_start ?? '?'}</small></div><button onClick={() => { const symbol = data.symbols.find(s => s.relative_path === link.relative_path && s.line_start === link.line_start); if (symbol) onJump(symbol); }} disabled={!data.symbols.some(s => s.relative_path === link.relative_path && s.line_start === link.line_start)}>Source <ChevronRight size={13}/></button></div>)}{!relatedTo(model.name, data.relationships).length && <p className="insight-muted">No literal relationships detected.</p>}</div></>
            : <div className="insight-model-groups">{([
                ['Source classes', model.source_classes], ['Fields', model.fields], ['Methods', model.methods],
                ['XML views', model.views], ['Actions', model.actions],
              ] as [string, InsightSymbol[]][]).map(([title, list]) => <div key={title} className="insight-model-group"><h3>{title} <small>{list.length}</small></h3><div className="insight-results">{rankSymbols(list, 'size_bytes').slice(0, 60).map(s => <ResultRow symbol={s} key={s.id} onJump={onJump}/>)}{list.length === 0 && <p className="insight-muted">None found in this addon.</p>}</div></div>)}</div>}
        </>}
      </section>}
      {tab === 'rankings' && <section className="insight-section"><div className="insight-controls"><span className="insight-control-title"><SortDesc size={16}/> Rank symbols by</span><div className="metric-group" role="group" aria-label="Insight ranking metric">{RANK_METRICS.map(item => <button key={item.key} onClick={() => setMetric(item.key)} className={metric === item.key ? 'metric-active' : ''}>{item.label}</button>)}</div><select aria-label="Ranking symbol type" value={rankKind} onChange={e => setRankKind(e.target.value)}><option value="all">All types</option>{kinds.map(k => <option key={k} value={k}>{k.replaceAll('_', ' ')}</option>)}</select></div>
        <p className="insight-muted"><BarChart3 size={14}/> {metric === 'complexity' ? 'Approximate Python method cyclomatic complexity (not measured runtime cost)' : 'Source spans, not compiled or compressed asset sizes'} · Top 40</p>
        <div className="insight-results">{ranked.map(s => <ResultRow key={s.id} symbol={s} metric={metric} onJump={onJump}/>)}{!ranked.length && <p className="insight-muted">No matching symbols for this metric.</p>}</div>
      </section>}
    </>}
  </section>;
}
