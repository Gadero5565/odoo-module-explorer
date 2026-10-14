import { Box, ClipboardCopy, Code2, FileCode2, GitBranch, Layers3, ListTree, Package, Tags } from 'lucide-react';
import { useState } from 'react';
import type { JSInspection, JSSymbol } from '../types/javascript';
import { formatBytes, formatNumber } from '../lib/analysis';

type Props = { node: JSSymbol; inspection: JSInspection | null; modulePath: string; onSelect: (node: JSSymbol) => void };

function Detail({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  if (value === null || value === undefined || value === '') return null;
  return <div className="detail-stat"><span>{label}</span><strong title={String(value)}>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</strong></div>;
}
export default function JSDetails({ node, inspection, modulePath, onSelect }: Props) {
  const [copied, setCopied] = useState(false);
  const meta = node.metadata;
  const isFile = node.kind === 'file';
  const absolute = `${modulePath.replace(/[\\/]$/, '')}${modulePath.includes('\\') ? '\\' : '/'}${node.relative_path.replaceAll('/', modulePath.includes('\\') ? '\\' : '/')}`;
  const location = node.line_start ? `${absolute}:${node.line_start}` : absolute;
  const copyLocation = async () => {
    try {
      await navigator.clipboard.writeText(location);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch { setCopied(false); }
  };
  const definitions = node.children.filter(child => child.kind !== 'code');
  return <div className="details-scroll">
    <div className="detail-heading">
      <div className="detail-icon">{meta.is_owl_component ? <Box size={22}/> : node.kind === 'registration' ? <GitBranch size={22}/> : isFile ? <FileCode2 size={22}/> : <Code2 size={22}/>}</div>
      <div className="detail-name-wrap"><div className="detail-name">{node.name}</div><div className="detail-sub">{meta.is_owl_component ? 'OWL component' : node.kind.replaceAll('_', ' ')} {meta.parameters ? `(${meta.parameters})` : ''}</div></div>
    </div>
    <div className="detail-section">
      <div className="section-title">JAVASCRIPT STRUCTURE</div>
      <Detail label="Physical size" value={formatBytes(node.size_bytes)}/>
      <Detail label="Physical lines" value={formatNumber(node.line_count)}/>
      <Detail label="Starts at" value={node.line_start ? `Line ${node.line_start}` : null}/>
      <Detail label="Ends at" value={node.line_end ? `Line ${node.line_end}` : null}/>
      <Detail label="Direct symbols" value={formatNumber(definitions.length)}/>
      <Detail label="Module style" value={meta.module_format}/>
    </div>
    {(meta.is_owl_component || meta.template || meta.extends?.length || meta.hooks?.length || meta.props) && <div className="detail-section">
      <div className="section-title"><Box size={13}/> OWL / CLASS</div>
      <Detail label="Component" value={meta.is_owl_component}/>
      <Detail label="Extends" value={meta.extends?.join(', ')}/>
      <Detail label="QWeb template" value={meta.template}/>
      <Detail label="Props" value={meta.props}/>
      <Detail label="Components" value={meta.components?.join(', ')}/>
      <Detail label="OWL hooks" value={meta.hooks?.join(', ')}/>
    </div>}
    {(node.kind === 'service' || meta.registry_category || meta.dependencies?.length) && <div className="detail-section">
      <div className="section-title"><GitBranch size={13}/> ODOO SERVICES / REGISTRIES</div>
      <Detail label="Registry category" value={meta.registry_category}/>
      <Detail label="Registry key" value={meta.registry_key}/>
      <Detail label="Registered symbol" value={meta.registry_target}/>
      <Detail label="Dependencies" value={meta.dependencies?.join(', ')}/>
      <Detail label="Service properties" value={meta.properties?.join(', ')}/>
    </div>}
    {node.kind === 'function' || node.kind === 'method' ? <div className="detail-section">
      <div className="section-title">FUNCTION</div>
      <Detail label="Parameters" value={meta.parameters}/>
      <Detail label="Async" value={meta.async}/>
      <Detail label="Exported" value={meta.exported}/>
      <Detail label="Hooks" value={meta.hooks?.join(', ')}/>
    </div> : null}
    {isFile && inspection && <>
      <div className="detail-section">
        <div className="section-title"><Package size={13}/> MODULE IMPORTS ({inspection.imports.length})</div>
        {inspection.imports.slice(0, 80).map((item, i) => <div className="detail-stat" key={i}><span title={item.names || ''}>{item.source}</span><strong title={item.names || ''}>{item.names || 'side effect'}</strong></div>)}
      </div>
      {!!inspection.registrations.length && <div className="detail-section">
        <div className="section-title"><GitBranch size={13}/> REGISTRY ENTRIES ({inspection.registrations.length})</div>
        {inspection.registrations.slice(0, 80).map((item, i) => <div className="detail-stat" key={i}><span>{item.category || 'registry'} · {item.key || '(dynamic)'}</span><strong>{item.target || 'inline'}</strong></div>)}
      </div>}
    </>}
    <div className="detail-section">
      <div className="section-title">SOURCE LOCATION</div>
      <div className="path-card"><span title={location}>{node.relative_path}{node.line_start ? `:${node.line_start}` : ''}</span><button title="Copy file path and line" onClick={() => void copyLocation()}><ClipboardCopy size={14}/>{copied ? '✓' : ''}</button></div>
    </div>
    {!!definitions.length && <div className="detail-section">
      <div className="section-title"><ListTree size={13}/> CHILD DEFINITIONS</div>
      {definitions.slice(0, 100).map(child => <button key={child.id} className="largest-item" onClick={() => onSelect(child)}><span className="truncate">{child.name}</span><span>{child.kind === 'property' ? <Tags size={12}/> : child.kind}</span></button>)}
      {definitions.length > 100 && <p className="semantic-note">Showing the first 100 child definitions.</p>}
    </div>}
    <div className="detail-note"><Layers3 size={15}/><span>Static Odoo 16–19 JavaScript analysis. It never executes source files. OWL template names, imported modules and registry references are not resolved across files in Phase 5. Residual source rectangles preserve physical byte totals.</span></div>
  </div>;
}
