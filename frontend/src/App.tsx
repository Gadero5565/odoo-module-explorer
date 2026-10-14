import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle, ArrowRight, BarChart3, CheckCircle2, ChevronRight, Code2, Database,
  File, FileCode2, Folder, FolderOpen, Github, HardDrive, Layers3, LoaderCircle,
  RefreshCcw, Search, SlidersHorizontal, Sparkles, X, GitBranch,
} from 'lucide-react';
import FolderTree from './components/FolderTree';
import Treemap from './components/Treemap';
import DetailsPanel from './components/DetailsPanel';
import PythonDetails from './components/PythonDetails';
import XMLDetails from './components/XMLDetails';
import JSDetails from './components/JSDetails';
import StyleDetails from './components/StyleDetails';
import InsightsPanel from './components/InsightsPanel';
import { filterTree, formatBytes, formatNumber, metricValue, indexNodes, indexPythonSymbols, indexXMLSymbols, indexJSSymbols, indexStyleSymbols, parentId, pythonSymbolPath, xmlSymbolPath, jsSymbolPath, styleSymbolPath } from './lib/analysis';
import type { AnalysisResult, DisplayFilters, FileNode, Metric } from './types/analysis';
import type { PythonInspection, PythonSymbol } from './types/python';
import type { XMLInspection, XMLSymbol } from './types/xml';
import type { JSInspection, JSSymbol } from './types/javascript';
import type { StyleInspection, StyleSymbol } from './types/styles';
import type { InsightSymbol, InsightsResponse } from './types/insights';

const DEFAULT_FILTERS: DisplayFilters = { sourceOnly: false, excludeData: false };
const METRIC_OPTIONS: { key: Metric; label: string }[] = [
  { key: 'size_bytes', label: 'Size' },
  { key: 'file_count', label: 'Files' },
  { key: 'line_count', label: 'Lines' },
];

export default function App() {
  const [modulePath, setModulePath] = useState('');
  const [demoPath, setDemoPath] = useState('');
  const [versionOverride, setVersionOverride] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DisplayFilters>(DEFAULT_FILTERS);
  const [metric, setMetric] = useState<Metric>('size_bytes');
  const [currentId, setCurrentId] = useState('.');
  const [selectedId, setSelectedId] = useState('.');
  const [search, setSearch] = useState('');
  const [searchFocused, setSearchFocused] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [pythonFilePath, setPythonFilePath] = useState<string | null>(null);
  const [pythonInspection, setPythonInspection] = useState<PythonInspection | null>(null);
  const [pythonLoading, setPythonLoading] = useState(false);
  const [pythonError, setPythonError] = useState<string | null>(null);
  const [symbolDrillId, setSymbolDrillId] = useState<string | null>(null);
  const [symbolSelectedId, setSymbolSelectedId] = useState<string | null>(null);
  const [xmlFilePath, setXMLFilePath] = useState<string | null>(null);
  const [xmlInspection, setXMLInspection] = useState<XMLInspection | null>(null);
  const [xmlLoading, setXMLLoading] = useState(false);
  const [xmlError, setXMLError] = useState<string | null>(null);
  const [xmlDrillId, setXMLDrillId] = useState<string | null>(null);
  const [xmlSelectedId, setXMLSelectedId] = useState<string | null>(null);
  const [jsFilePath, setJSFilePath] = useState<string | null>(null);
  const [jsInspection, setJSInspection] = useState<JSInspection | null>(null);
  const [jsLoading, setJSLoading] = useState(false);
  const [jsError, setJSError] = useState<string | null>(null);
  const [jsDrillId, setJSDrillId] = useState<string | null>(null);
  const [jsSelectedId, setJSSelectedId] = useState<string | null>(null);
  const [styleFilePath, setStyleFilePath] = useState<string | null>(null);
  const [styleInspection, setStyleInspection] = useState<StyleInspection | null>(null);
  const [styleLoading, setStyleLoading] = useState(false);
  const [styleError, setStyleError] = useState<string | null>(null);
  const [styleDrillId, setStyleDrillId] = useState<string | null>(null);
  const [styleSelectedId, setStyleSelectedId] = useState<string | null>(null);
  const [workspaceMode, setWorkspaceMode] = useState<'explorer' | 'insights'>('explorer');
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState<string | null>(null);
  const [pendingJump, setPendingJump] = useState<InsightSymbol | null>(null);

  useEffect(() => {
    fetch('/api/config').then(response => response.ok ? response.json() : null)
      .then(data => { if (data?.demo_module_path) setDemoPath(data.demo_module_path); })
      .catch(() => { /* backend unavailable message appears on submission */ });
  }, []);

  const runAnalysis = useCallback(async (path: string) => {
    if (!path.trim()) { setError('Enter the full path to an Odoo module directory.'); return; }
    setLoading(true); setError(null);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_path: path.trim(), version_override: versionOverride || null }),
      });
      const payload = await response.json();
      if (!response.ok) {
        const detail = payload?.detail;
        throw new Error(typeof detail === 'string' ? detail : 'Analysis failed. Check the selected path and try again.');
      }
      setResult(payload as AnalysisResult);
      setCurrentId('.'); setSelectedId('.'); setSearch(''); setFilters(DEFAULT_FILTERS);
      setPythonFilePath(null); setPythonInspection(null); setPythonError(null);
      setSymbolDrillId(null); setSymbolSelectedId(null);
      setXMLFilePath(null); setXMLInspection(null); setXMLError(null);
      setXMLDrillId(null); setXMLSelectedId(null);
      setJSFilePath(null); setJSInspection(null); setJSError(null);
      setJSDrillId(null); setJSSelectedId(null);
      setStyleFilePath(null); setStyleInspection(null); setStyleError(null);
      setStyleDrillId(null); setStyleSelectedId(null);
      setInsights(null); setInsightsError(null); setPendingJump(null);
      setWorkspaceMode('explorer');
    } catch (err) {
      setError(err instanceof TypeError ? 'Could not connect to FastAPI. Start the backend on 127.0.0.1:7764.' : (err as Error).message);
    } finally { setLoading(false); }
  }, [versionOverride]);

  useEffect(() => {
    if (!result || !pythonFilePath) return;
    let cancelled = false;
    setPythonLoading(true); setPythonInspection(null); setPythonError(null);
    setSymbolDrillId(null); setSymbolSelectedId(null);
    fetch('/api/python/inspect', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module_path: result.module.absolute_path,
        relative_path: pythonFilePath, version_override: versionOverride || null }),
    }).then(async response => {
      const json = await response.json();
      if (!response.ok) throw new Error(json?.detail || 'Python inspection failed.');
      return json as PythonInspection;
    }).then(data => { if (!cancelled) setPythonInspection(data); })
      .catch(err => { if (!cancelled) setPythonError(err instanceof Error ? err.message : 'Python inspection failed.'); })
      .finally(() => { if (!cancelled) setPythonLoading(false); });
    return () => { cancelled = true; };
  }, [result, pythonFilePath, versionOverride]);

  useEffect(() => {
    if (!result || !xmlFilePath) return;
    let cancelled = false;
    setXMLLoading(true); setXMLInspection(null); setXMLError(null);
    setXMLDrillId(null); setXMLSelectedId(null);
    fetch('/api/xml/inspect', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module_path: result.module.absolute_path,
        relative_path: xmlFilePath, version_override: versionOverride || null }),
    }).then(async response => {
      const json = await response.json();
      if (!response.ok) throw new Error(json?.detail || 'XML inspection failed.');
      return json as XMLInspection;
    }).then(data => { if (!cancelled) setXMLInspection(data); })
      .catch(err => { if (!cancelled) setXMLError(err instanceof Error ? err.message : 'XML inspection failed.'); })
      .finally(() => { if (!cancelled) setXMLLoading(false); });
    return () => { cancelled = true; };
  }, [result, xmlFilePath, versionOverride]);

  useEffect(() => {
    if (!result || !jsFilePath) return;
    let cancelled = false;
    setJSLoading(true); setJSInspection(null); setJSError(null);
    setJSDrillId(null); setJSSelectedId(null);
    fetch('/api/javascript/inspect', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module_path: result.module.absolute_path,
        relative_path: jsFilePath, version_override: versionOverride || null }),
    }).then(async response => {
      const json = await response.json();
      if (!response.ok) throw new Error(json?.detail || 'JavaScript inspection failed.');
      return json as JSInspection;
    }).then(data => { if (!cancelled) setJSInspection(data); })
      .catch(err => { if (!cancelled) setJSError(err instanceof Error ? err.message : 'JavaScript inspection failed.'); })
      .finally(() => { if (!cancelled) setJSLoading(false); });
    return () => { cancelled = true; };
  }, [result, jsFilePath, versionOverride]);

  useEffect(() => {
    if (!result || !styleFilePath) return;
    let cancelled = false;
    setStyleLoading(true); setStyleInspection(null); setStyleError(null);
    setStyleDrillId(null); setStyleSelectedId(null);
    fetch('/api/styles/inspect', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module_path: result.module.absolute_path,
        relative_path: styleFilePath, version_override: versionOverride || null }),
    }).then(async response => {
      const json = await response.json();
      if (!response.ok) throw new Error(json?.detail || 'Stylesheet inspection failed.');
      return json as StyleInspection;
    }).then(data => { if (!cancelled) setStyleInspection(data); })
      .catch(err => { if (!cancelled) setStyleError(err instanceof Error ? err.message : 'Stylesheet inspection failed.'); })
      .finally(() => { if (!cancelled) setStyleLoading(false); });
    return () => { cancelled = true; };
  }, [result, styleFilePath, versionOverride]);

  const loadInsights = useCallback(async () => {
    if (!result) return;
    setInsightsLoading(true); setInsightsError(null);
    try {
      const response = await fetch('/api/insights', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_path: result.module.absolute_path, version_override: versionOverride || null }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.detail || 'Module-wide indexing failed.');
      setInsights(payload as InsightsResponse);
    } catch (err) {
      setInsightsError(err instanceof Error ? err.message : 'Could not build module index.');
    } finally { setInsightsLoading(false); }
  }, [result, versionOverride]);

  const tree = useMemo(() => result ? filterTree(result.root, filters) : null, [result, filters]);
  const index = useMemo(() => tree ? indexNodes(tree) : new Map<string, FileNode>(), [tree]);
  const currentFolder = (index.get(currentId)?.kind === 'directory' ? index.get(currentId) : null) || tree;
  const selectedNode = index.get(selectedId) || currentFolder;
  const pythonIndex = useMemo(() => pythonInspection ? indexPythonSymbols(pythonInspection.file) : new Map<string, PythonSymbol>(), [pythonInspection]);
  const currentPython = pythonInspection ? pythonIndex.get(symbolDrillId || '') || pythonInspection.file : null;
  const selectedPython = pythonInspection ? pythonIndex.get(symbolSelectedId || '') || pythonInspection.file : null;
  const xmlIndex = useMemo(() => xmlInspection ? indexXMLSymbols(xmlInspection.file) : new Map<string, XMLSymbol>(), [xmlInspection]);
  const currentXML = xmlInspection ? xmlIndex.get(xmlDrillId || '') || xmlInspection.file : null;
  const selectedXML = xmlInspection ? xmlIndex.get(xmlSelectedId || '') || xmlInspection.file : null;
  const jsIndex = useMemo(() => jsInspection ? indexJSSymbols(jsInspection.file) : new Map<string, JSSymbol>(), [jsInspection]);
  const currentJS = jsInspection ? jsIndex.get(jsDrillId || '') || jsInspection.file : null;
  const selectedJS = jsInspection ? jsIndex.get(jsSelectedId || '') || jsInspection.file : null;
  const styleIndex = useMemo(() => styleInspection ? indexStyleSymbols(styleInspection.file) : new Map<string, StyleSymbol>(), [styleInspection]);
  const currentStyle = styleInspection ? styleIndex.get(styleDrillId || '') || styleInspection.file : null;
  const selectedStyle = styleInspection ? styleIndex.get(styleSelectedId || '') || styleInspection.file : null;
  const viewingStyles = Boolean(styleFilePath);
  const viewingPython = Boolean(pythonFilePath);
  const viewingXML = Boolean(xmlFilePath);
  const viewingJS = Boolean(jsFilePath);
  const viewingStructure = viewingPython || viewingXML || viewingJS || viewingStyles;
  const displayedNode = currentStyle || currentJS || currentXML || currentPython || currentFolder;
  const displayedSelection = selectedStyle || selectedJS || selectedXML || selectedPython || selectedNode;
  const effectiveMetric: Metric = viewingStructure && metric === 'file_count' ? 'size_bytes' : metric;
  const searchResults = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query || !tree) return [];
    return [...index.values()].filter(item => item.id !== '.' && item.relative_path.toLowerCase().includes(query))
      .sort((a, b) => a.name.toLowerCase().startsWith(query) === b.name.toLowerCase().startsWith(query) ? b.size_bytes - a.size_bytes : (a.name.toLowerCase().startsWith(query) ? -1 : 1))
      .slice(0, 25);
  }, [index, search, tree]);

  const onSelect = useCallback((node: FileNode) => {
    setSelectedId(node.id);
    setCurrentId(node.kind === 'directory' ? node.id : parentId(node.id));
    const target = node.kind === 'file' && node.extension === '.py' ? node.relative_path : null;
    const xmlTarget = node.kind === 'file' && node.extension === '.xml' ? node.relative_path : null;
    const jsTarget = node.kind === 'file' && node.extension === '.js' ? node.relative_path : null;
    const styleTarget = node.kind === 'file' && ['.css', '.scss'].includes(node.extension || '') ? node.relative_path : null;
    if (target !== pythonFilePath) {
      setPythonFilePath(target);
      setPythonInspection(null); setPythonError(null);
    }
    if (xmlTarget !== xmlFilePath) {
      setXMLFilePath(xmlTarget);
      setXMLInspection(null); setXMLError(null);
    }
    if (jsTarget !== jsFilePath) {
      setJSFilePath(jsTarget);
      setJSInspection(null); setJSError(null);
    }
    if (styleTarget !== styleFilePath) {
      setStyleFilePath(styleTarget);
      setStyleInspection(null); setStyleError(null);
    }
    setJSDrillId(null); setJSSelectedId(null);
    setStyleDrillId(null); setStyleSelectedId(null);
    setXMLDrillId(null); setXMLSelectedId(null);
    setSymbolDrillId(null); setSymbolSelectedId(null);
    setSearchFocused(false);
  }, [pythonFilePath, xmlFilePath, jsFilePath, styleFilePath]);
  const jumpToInsight = useCallback((symbol: InsightSymbol) => {
    if (!result) return;
    // Insights index is independent of display filters; reveal hidden files as needed.
    const target = indexNodes(result.root).get(symbol.relative_path);
    if (!target || target.kind !== 'file') return;
    setFilters(DEFAULT_FILTERS);
    onSelect(target);
    setPendingJump(symbol);
    setWorkspaceMode('explorer');
  }, [result, onSelect]);

  useEffect(() => {
    if (!pendingJump) return;
    const file = pendingJump.relative_path;
    const select = (root: PythonSymbol | XMLSymbol | JSSymbol | StyleSymbol,
                    id: string, kind: 'python' | 'xml' | 'js' | 'style') => {
      const path = kind === 'python' ? pythonSymbolPath(root as PythonSymbol, id)
        : kind === 'xml' ? xmlSymbolPath(root as XMLSymbol, id)
        : kind === 'js' ? jsSymbolPath(root as JSSymbol, id)
        : styleSymbolPath(root as StyleSymbol, id);
      if (!path.length) { setPendingJump(null); return; }
      const focus = path[path.length - 1];
      const parent = focus.children.length ? focus : (path[path.length - 2] || root);
      if (kind === 'python') { setSymbolDrillId(parent.id); setSymbolSelectedId(focus.id); }
      if (kind === 'xml') { setXMLDrillId(parent.id); setXMLSelectedId(focus.id); }
      if (kind === 'js') { setJSDrillId(parent.id); setJSSelectedId(focus.id); }
      if (kind === 'style') { setStyleDrillId(parent.id); setStyleSelectedId(focus.id); }
      setPendingJump(null);
    };
    if (file.endsWith('.py') && pythonFilePath === file && pythonInspection) select(pythonInspection.file, pendingJump.id, 'python');
    else if (file.endsWith('.xml') && xmlFilePath === file && xmlInspection) select(xmlInspection.file, pendingJump.id, 'xml');
    else if (file.endsWith('.js') && jsFilePath === file && jsInspection) select(jsInspection.file, pendingJump.id, 'js');
    else if ((file.endsWith('.scss') || file.endsWith('.css')) && styleFilePath === file && styleInspection) select(styleInspection.file, pendingJump.id, 'style');
  }, [pendingJump, pythonFilePath, pythonInspection, xmlFilePath, xmlInspection,
      jsFilePath, jsInspection, styleFilePath, styleInspection]);

  const onSymbolSelect = (node: PythonSymbol) => {
    setSymbolSelectedId(node.id);
    if (node.children.length && node.kind !== 'code') setSymbolDrillId(node.id);
  };
  const onXMLSymbolSelect = (node: XMLSymbol) => {
    setXMLSelectedId(node.id);
    if (node.children.length && node.kind !== 'other') setXMLDrillId(node.id);
  };
  const onJSSymbolSelect = (node: JSSymbol) => {
    setJSSelectedId(node.id);
    if (node.children.length && node.kind !== 'code') setJSDrillId(node.id);
  };
  const onStyleSymbolSelect = (node: StyleSymbol) => {
    setStyleSelectedId(node.id);
    if (node.children.length && node.kind !== 'other') setStyleDrillId(node.id);
  };
  const onVisualSelect = (node: FileNode | PythonSymbol | XMLSymbol | JSSymbol | StyleSymbol) => {
    if ('file_count' in node) onSelect(node);
    else if (viewingStyles) onStyleSymbolSelect(node as StyleSymbol);
    else if ('tag' in node) onXMLSymbolSelect(node);
    else if ('metadata' in node) onJSSymbolSelect(node as JSSymbol);
    else onSymbolSelect(node);
  };
  const navigate = (id: string) => {
    if (id.startsWith('symbol:')) {
      const symbolId = id.slice('symbol:'.length);
      if (viewingStyles) { setStyleDrillId(symbolId); setStyleSelectedId(symbolId); }
      else if (viewingJS) { setJSDrillId(symbolId); setJSSelectedId(symbolId); }
      else if (viewingXML) { setXMLDrillId(symbolId); setXMLSelectedId(symbolId); }
      else { setSymbolDrillId(symbolId); setSymbolSelectedId(symbolId); }
    } else if (id.startsWith('file:')) {
      setSymbolDrillId(null); setSymbolSelectedId(null);
      setXMLDrillId(null); setXMLSelectedId(null);
      setJSDrillId(null); setJSSelectedId(null);
      setStyleDrillId(null); setStyleSelectedId(null);
    } else if (index.has(id)) {
      setCurrentId(id); setSelectedId(id);
      setPythonFilePath(null); setPythonInspection(null);
      setXMLFilePath(null); setXMLInspection(null);
      setJSFilePath(null); setJSInspection(null);
      setStyleFilePath(null); setStyleInspection(null);
    }
  };

  const crumbs = useMemo(() => {
    if (!currentFolder) return [];
    const segments = currentFolder.id === '.' ? [] : currentFolder.relative_path.split('/');
    const base = [{ id: '.', name: result?.module.name || '' }, ...segments.map((name, index) => ({ id: segments.slice(0, index + 1).join('/'), name }))];
    const selectedPath = styleFilePath || jsFilePath || xmlFilePath || pythonFilePath;
    if (!selectedPath) return base;
    base.push({ id: `file:${selectedPath}`, name: selectedPath.split('/').at(-1) || selectedPath });
    if (styleInspection && currentStyle) {
      const path = styleSymbolPath(styleInspection.file, currentStyle.id);
      base.push(...path.slice(1).map(item => ({ id: `symbol:${item.id}`, name: item.name })));
    } else if (jsInspection && currentJS) {
      const path = jsSymbolPath(jsInspection.file, currentJS.id);
      base.push(...path.slice(1).map(item => ({ id: `symbol:${item.id}`, name: item.name })));
    } else if (xmlInspection && currentXML) {
      const path = xmlSymbolPath(xmlInspection.file, currentXML.id);
      base.push(...path.slice(1).map(item => ({ id: `symbol:${item.id}`, name: item.name })));
    } else if (pythonInspection && currentPython) {
      const path = pythonSymbolPath(pythonInspection.file, currentPython.id);
      base.push(...path.slice(1).map(item => ({ id: `symbol:${item.id}`, name: item.name })));
    }
    return base;
  }, [currentFolder, result, pythonFilePath, pythonInspection, currentPython, xmlFilePath, xmlInspection, currentXML, jsFilePath, jsInspection, currentJS, styleFilePath, styleInspection, currentStyle]);

  const statCards = result ? [
    { label: 'TOTAL SIZE', value: formatBytes(result.root.size_bytes), icon: HardDrive },
    { label: 'FILES', value: formatNumber(result.root.file_count), icon: File },
    { label: 'FOLDERS', value: formatNumber(result.root.directory_count), icon: Folder },
    { label: 'SOURCE LINES', value: formatNumber(result.root.line_count), icon: Code2 },
  ] : [];

  return <div className="app-shell">
    <header className="global-header">
      <div className="brand"><div className="brand-icon"><Layers3 size={21}/></div><div><strong>Odoo Module Explorer</strong><span>CODE STRUCTURE ANALYZER</span></div></div>
      <div className="header-actions"><span className="phase-tag"><span className="live-dot"/> PHASE 07 · INSIGHTS</span><a className="github-link" href="https://github.com/Gadero5565/odoo-module-explorer" target="_blank" rel="noopener noreferrer" title="Project GitHub repository"><Github size={18}/><span>GitHub</span></a></div>
    </header>

    <section className="input-bar">
      <div className="input-container">
        <div className="path-input-wrap"><FolderOpen size={19}/><input aria-label="Odoo module directory" value={modulePath} onChange={event => setModulePath(event.target.value)} onKeyDown={event => { if (event.key === 'Enter') void runAnalysis(modulePath); }} placeholder="Enter module path, e.g. C:\\odoo19\\custom_addons\\demo_odoo_module" /></div>
        <select aria-label="Odoo version override" value={versionOverride} onChange={event => setVersionOverride(event.target.value)} title="Leave Auto to read version from manifest"><option value="">Version: Auto</option>{['16','17','18','19'].map(v => <option value={v} key={v}>Odoo {v}</option>)}</select>
        <button className="primary-button" disabled={loading} onClick={() => void runAnalysis(modulePath)}>{loading ? <LoaderCircle size={17} className="spin"/> : <BarChart3 size={17}/>} {loading ? 'Analyzing…' : 'Analyze Module'}</button>
      </div>
      {error && <div className="error-bar" role="alert"><AlertCircle size={16}/><span>{error}</span><button title="Dismiss" onClick={() => setError(null)}><X size={15}/></button></div>}
    </section>

    {!result ? <div className="welcome-container">
      <div className="welcome-glow"/>
      <div className="welcome-icon"><Layers3 size={30}/></div>
      <div className="eyebrow">UNDERSTAND YOUR ODOO ADDONS</div>
      <h1>See the bigger picture<br/><span>of your modules.</span></h1>
      <p>Explore every folder and file through an interactive treemap. Discover what takes up space, inspect source line counts, and drill into your Odoo 16–19 addons.</p>
      <div className="welcome-buttons"><button className="primary-button demo-button" disabled={!demoPath || loading} onClick={() => { setModulePath(demoPath); void runAnalysis(demoPath); }}><Sparkles size={16}/> Explore sample module <ArrowRight size={16}/></button></div>
      <div className="feature-row"><span><CheckCircle2 size={15}/> No Odoo server required</span><span><CheckCircle2 size={15}/> Works offline</span><span><CheckCircle2 size={15}/> Read-only analysis</span></div>
      <div className="welcome-hint">The path is read by FastAPI on your computer, not by the browser. {demoPath ? 'Or try the bundled sample addon.' : 'Start the backend to enable the sample addon.'}</div>
    </div> : <div className="workspace">
      <div className="summary-strip"><div className="module-identity"><span className="module-ident-icon"><Database size={21}/></span><div><h2>{result.module.name}</h2><div className="module-meta"><span>{result.module.version ? `Odoo ${result.module.version}` : 'Odoo version unspecified'}</span><span className="mid-dot">·</span><span title={result.module.absolute_path}>{result.module.absolute_path}</span></div></div></div><button className="refresh-button" onClick={() => void runAnalysis(result.module.absolute_path)} disabled={loading} title="Rescan source files"><RefreshCcw size={16} className={loading ? 'spin' : ''}/> Rescan</button></div>
      <div className="stat-strip">{statCards.map(stat => <div className="stat-item" key={stat.label}><div className="stat-icon"><stat.icon size={19}/></div><div><div className="stat-label">{stat.label}</div><div className="stat-value">{stat.value}</div></div></div>)}</div>
      <div className="workspace-mode" role="group" aria-label="Explorer view">
        <button className={workspaceMode === 'explorer' ? 'selected' : ''} onClick={() => setWorkspaceMode('explorer')}><Layers3 size={15}/> File Explorer</button>
        <button className={workspaceMode === 'insights' ? 'selected' : ''} onClick={() => { setWorkspaceMode('insights'); if (!insights && !insightsLoading) void loadInsights(); }}><GitBranch size={15}/> Advanced Insights</button>
      </div>
      {workspaceMode === 'insights' ? <InsightsPanel data={insights} loading={insightsLoading} error={insightsError} onLoad={() => void loadInsights()} onJump={jumpToInsight}/> : <div className="workbody">
        <aside className="file-sidebar">
          <div className="sidebar-header"><span>EXPLORER</span><span className="tree-count">{formatNumber(tree?.file_count || 0)} files</span></div>
          <div className="search-wrap"><Search size={15}/><input placeholder="Search files and folders…" aria-label="Search files and folders" value={search} onFocus={() => setSearchFocused(true)} onChange={event => { setSearch(event.target.value); setSearchFocused(true); }} />{search && <button title="Clear search" onClick={() => setSearch('')}><X size={13}/></button>}</div>
          {searchFocused && search.trim() && <div className="search-results"><div className="search-result-heading">{searchResults.length ? `MATCHING PATHS (TOP ${searchResults.length})` : 'NO MATCHES'}</div>{searchResults.map(node => <button key={node.id} title={node.relative_path} onClick={() => { onSelect(node); setSearch(''); }}><span>{node.kind === 'directory' ? <Folder size={14}/> : <FileCode2 size={14}/>}</span><span className="truncate">{node.relative_path}</span></button>)}</div>}
          <div className="sidebar-scroll">{tree && <FolderTree root={tree} selectedId={selectedNode?.id || '.'} currentId={currentFolder?.id || '.'} onSelect={onSelect}/>}</div>
          <div className="sidebar-foot"><span className="live-dot"/> Local analysis <span>·</span> Read-only</div>
        </aside>

        <main className="main-panel">
          <div className="explorer-toolbar"><div className="breadcrumbs">{crumbs.map((crumb, i) => <span key={crumb.id} className="crumb-wrap">{i > 0 && <ChevronRight size={15}/>}<button className={i === crumbs.length - 1 ? 'active-crumb' : ''} onClick={() => navigate(crumb.id)} title={crumb.id}>{crumb.name}</button></span>)}</div><div className="toolbar-actions"><div className="metric-group" role="group" aria-label="Treemap metric">{METRIC_OPTIONS.filter(option => !viewingStructure || option.key !== 'file_count').map(option => <button key={option.key} className={effectiveMetric === option.key ? 'metric-active' : ''} onClick={() => setMetric(option.key)}>{option.label}</button>)}</div><div className="filter-holder"><button className={`icon-button ${filters.sourceOnly || filters.excludeData ? 'filter-active' : ''}`} title="Display filters" aria-label="Display filters" onClick={() => setFilterOpen(!filterOpen)}><SlidersHorizontal size={17}/></button>{filterOpen && <div className="filter-popover"><strong>Display filters</strong><label><input type="checkbox" checked={filters.sourceOnly} onChange={e => setFilters(s => ({...s, sourceOnly: e.target.checked}))}/> Source code files only</label><label><input type="checkbox" checked={filters.excludeData} onChange={e => setFilters(s => ({...s, excludeData: e.target.checked}))}/> Hide data, demo and i18n folders</label><small>Charts and navigator reflect these filters. The top statistics always show all scanned files.</small></div>}</div></div></div>
          <div className="view-heading"><div><div className="view-title">{viewingStructure ? (displayedNode?.name || 'Source structure') : currentFolder?.id === '.' ? 'Module overview' : currentFolder?.name || 'Folder'} <span className="view-pill">{viewingStructure ? (currentStyle?.kind || currentJS?.kind || currentXML?.kind || currentPython?.kind || 'SOURCE').toUpperCase().replaceAll('_', ' ') : 'DIRECTORY'}</span></div><div className="view-sub">{viewingStructure ? 'Click any source node to drill down · Physical source spans' : 'Click any rectangle to explore'} · Ranked by {effectiveMetric === 'size_bytes' ? 'size' : effectiveMetric === 'file_count' ? 'file count' : 'line count'}</div></div><div className="view-tally">{viewingStyles ? `${styleInspection?.selector_count || 0} selectors · ${styleInspection?.declaration_count || 0} declarations · ${styleInspection?.variable_count || 0} variables · ${styleInspection?.mixin_count || 0} mixins` : viewingJS ? `${jsInspection?.symbol_count || 0} symbols · ${jsInspection?.component_count || 0} OWL components · ${jsInspection?.registration_count || 0} registries` : viewingXML ? `${xmlInspection?.element_count || 0} elements · ${xmlInspection?.view_count || 0} views · ${xmlInspection?.xpath_count || 0} XPath` : viewingPython ? `${pythonInspection?.symbol_count || 0} definitions · ${pythonInspection?.odoo_field_count || 0} fields · ${pythonInspection?.odoo_model_count || 0} models` : `${formatNumber(currentFolder?.file_count || 0)} files`} <span>·</span> {formatBytes(displayedNode?.size_bytes || 0)}</div></div>
          {pythonError && <div className="error-bar" role="alert"><AlertCircle size={15}/>{pythonError}</div>}
          {styleError && <div className="error-bar" role="alert"><AlertCircle size={15}/>{styleError}</div>}
          {styleInspection?.parse_error && <div className="error-bar" role="status"><AlertCircle size={15}/>{styleInspection.parse_error}. File totals remain available.</div>}
          {jsError && <div className="error-bar" role="alert"><AlertCircle size={15}/>{jsError}</div>}
          {jsInspection?.parse_error && <div className="error-bar" role="status"><AlertCircle size={15}/>{jsInspection.parse_error}. File totals remain available.</div>}
          {xmlError && <div className="error-bar" role="alert"><AlertCircle size={15}/>{xmlError}</div>}
          {xmlInspection?.parse_error && <div className="error-bar" role="status"><AlertCircle size={15}/>{xmlInspection.parse_error}. File totals remain available.</div>}
          {pythonInspection?.parse_error && <div className="error-bar" role="status"><AlertCircle size={15}/>{pythonInspection.parse_error}. File totals remain available.</div>}
          <div className="treemap-container">{(viewingPython && pythonLoading) || (viewingXML && xmlLoading) || (viewingJS && jsLoading) || (viewingStyles && styleLoading) ? <div className="empty-treemap"><LoaderCircle size={18} className="spin"/> Inspecting source structure…</div> : displayedNode && <Treemap folder={displayedNode} metric={effectiveMetric} selectedId={displayedSelection?.id || '.'} onSelect={onVisualSelect}/>}</div>
          <div className="rank-panel"><div className="rank-header"><strong>LARGEST ITEMS</strong><span>IN CURRENT {viewingStructure ? 'SOURCE SCOPE' : 'DIRECTORY'}</span></div>{(!viewingStructure || !!pythonInspection || !!xmlInspection || !!jsInspection || !!styleInspection) && displayedNode?.children.length ? [...displayedNode.children].sort((a, b) => metricValue(b, effectiveMetric) - metricValue(a, effectiveMetric) || a.name.localeCompare(b.name)).slice(0, 15).map((node, rowIndex) => <button className={`rank-row ${displayedSelection?.id === node.id ? 'rank-selected' : ''}`} key={node.id} onClick={() => onVisualSelect(node)}><span className="rank-index">{String(rowIndex + 1).padStart(2, '0')}</span>{node.kind === 'directory' ? <Folder size={17} className="rank-folder"/> : <FileCode2 size={16}/>}<span className="rank-name truncate">{node.name}</span><span className="rank-meta">{node.kind === 'directory' ? `${formatNumber(node.file_count)} files` : node.kind === 'file' ? ('extension' in node ? node.extension || 'FILE' : 'tag' in node ? 'XML' : 'metadata' in node ? (viewingStyles ? 'STYLES' : 'JS') : 'PYTHON') : node.kind.replaceAll('_',' ')}</span><strong>{effectiveMetric === 'size_bytes' ? formatBytes(node.size_bytes) : formatNumber(metricValue(node, effectiveMetric))}</strong><ChevronRight size={15}/></button>) : <div className="rank-empty">No definitions in this scope.</div>}</div>
        </main>

        <aside className="details-sidebar"><div className="details-top"><span>INSPECTOR</span><span className="inspector-tag">PHASE 7</span></div>{selectedStyle ? <StyleDetails node={selectedStyle} inspection={styleInspection} modulePath={result.module.absolute_path} onSelect={onStyleSymbolSelect}/> : selectedJS ? <JSDetails node={selectedJS} inspection={jsInspection} modulePath={result.module.absolute_path} onSelect={onJSSymbolSelect}/> : selectedXML ? <XMLDetails node={selectedXML} modulePath={result.module.absolute_path} onSelect={onXMLSymbolSelect}/> : selectedPython ? <PythonDetails node={selectedPython} modulePath={result.module.absolute_path} onSelect={onSymbolSelect}/> : selectedNode && <DetailsPanel node={selectedNode} modulePath={result.module.absolute_path} onSelect={onSelect}/>}</aside>
      </div>
      }
      {result.warnings.length > 0 && <div className="warnings-strip"><AlertCircle size={15}/>{result.warnings.length} scanning warning(s), e.g. {result.warnings[0].relative_path}: {result.warnings[0].reason}</div>}
      <div className="workspace-footer"><span>Odoo Module Explorer v0.7.0</span><span>Supports Odoo 16–19 · Static source and model insights</span></div>
    </div>}
  </div>;
}
