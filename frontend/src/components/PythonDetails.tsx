import { Braces, ClipboardCopy, FileCode2, Layers3, ListTree } from 'lucide-react';
import { useState } from 'react';
import type { PythonSymbol } from '../types/python';
import { formatBytes, formatNumber } from '../lib/analysis';

type Props = {
  node: PythonSymbol;
  modulePath: string;
  onSelect: (node: PythonSymbol) => void;
};

export default function PythonDetails({ node, modulePath, onSelect }: Props) {
  const [copied, setCopied] = useState(false);
  const symbols = node.children.filter(child => child.kind !== 'code');
  const absolute = `${modulePath.replace(/[\\/]$/, '')}${modulePath.includes('\\') ? '\\' : '/'}${node.relative_path.replaceAll('/', modulePath.includes('\\') ? '\\' : '/')}`;
  const location = node.line_start ? `${absolute}:${node.line_start}` : absolute;
  const copyLocation = async () => {
    try {
      await navigator.clipboard.writeText(location);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch { setCopied(false); }
  };

  return <div className="details-scroll">
    <div className="detail-heading">
      <div className="detail-icon">{node.kind === 'file' ? <FileCode2 size={22}/> : <Braces size={22}/>}</div>
      <div className="detail-name-wrap"><div className="detail-name">{node.name}</div><div className="detail-sub">{node.kind.replaceAll('_', ' ')} {node.parameters || ''}</div></div>
    </div>
    <div className="detail-section">
      <div className="section-title">PYTHON STRUCTURE</div>
      <div className="detail-stat"><span>Physical size</span><strong>{formatBytes(node.size_bytes)}</strong></div>
      <div className="detail-stat"><span>Physical lines</span><strong>{formatNumber(node.line_count)}</strong></div>
      {node.line_start !== null && <div className="detail-stat"><span>Starts at</span><strong>Line {node.line_start}</strong></div>}
      {node.line_end !== null && <div className="detail-stat"><span>Ends at</span><strong>Line {node.line_end}</strong></div>}
      {node.kind !== 'code' && <div className="detail-stat"><span>Direct definitions</span><strong>{formatNumber(symbols.length)}</strong></div>}
    </div>
    {!!node.decorators.length && <div className="detail-section">
      <div className="section-title">DECORATORS</div>
      {node.decorators.map((value, index) => <div key={index} className="symbol-decorator">@{value}</div>)}
    </div>}
    <div className="detail-section">
      <div className="section-title">SOURCE LOCATION</div>
      <div className="path-card"><span title={location}>{node.relative_path}{node.line_start ? `:${node.line_start}` : ''}</span><button title="Copy file path and line" onClick={() => void copyLocation()}><ClipboardCopy size={14}/>{copied ? '✓' : ''}</button></div>
    </div>
    {!!symbols.length && <div className="detail-section">
      <div className="section-title"><ListTree size={13}/> NESTED DEFINITIONS</div>
      {symbols.map(child => <button key={child.id} className="largest-item" onClick={() => onSelect(child)}>
        <span className="truncate">{child.name}</span><span>{formatBytes(child.size_bytes)}</span>
      </button>)}
    </div>}
    <div className="detail-note"><Layers3 size={15}/><span>Metrics use inclusive physical line spans. “Other code” accounts for source not inside nested definitions. Fields and Odoo model semantics arrive in Phase 3.</span></div>
  </div>;
}
