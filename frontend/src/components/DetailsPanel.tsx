import { FileCode2, Folder, Layers, FileText, Copy, Check, Info } from 'lucide-react';
import { useState } from 'react';
import type { FileNode } from '../types/analysis';
import { fileCategory, formatBytes, formatNumber, getFileBreakdown } from '../lib/analysis';

type Props = { node: FileNode; modulePath: string; onSelect: (node: FileNode) => void };

export default function DetailsPanel({ node, modulePath, onSelect }: Props) {
  const [copied, setCopied] = useState(false);
  const isDir = node.kind === 'directory';
  const breakdown = isDir ? getFileBreakdown(node).slice(0, 6) : [];
  const topChildren = isDir ? [...node.children].sort((a, b) => b.size_bytes - a.size_bytes).slice(0, 6) : [];
  const absolutePath = `${modulePath.replace(/[\\/]$/, '')}${node.relative_path ? (modulePath.includes('\\') ? '\\' : '/') + node.relative_path.replaceAll('/', modulePath.includes('\\') ? '\\' : '/') : ''}`;
  const copyPath = async () => {
    try {
      await navigator.clipboard.writeText(absolutePath);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch { setCopied(false); }
  };
  return <div className="details-scroll">
    <div className="detail-heading">
      <div className="detail-icon">{isDir ? <Folder size={22}/> : <FileCode2 size={22}/>}</div>
      <div className="detail-name-wrap"><div className="detail-name">{node.name}</div><div className="detail-sub">{isDir ? 'Directory' : `${fileCategory(node.extension)} file`}</div></div>
    </div>
    <div className="detail-section">
      <div className="section-title">OVERVIEW</div>
      <div className="detail-stat"><span>Size on disk</span><strong>{formatBytes(node.size_bytes)}</strong></div>
      <div className="detail-stat"><span>Files</span><strong>{formatNumber(node.file_count)}</strong></div>
      {isDir && <div className="detail-stat"><span>Folders</span><strong>{formatNumber(node.directory_count)}</strong></div>}
      <div className="detail-stat"><span>Source lines</span><strong>{formatNumber(node.line_count)}</strong></div>
      {!isDir && <div className="detail-stat"><span>Extension</span><strong>{node.extension || 'none'}</strong></div>}
    </div>
    <div className="detail-section">
      <div className="section-title">LOCATION</div>
      <div className="path-card"><span title={absolutePath}>{node.relative_path || '(module root)'}</span><button title="Copy absolute path" onClick={copyPath}>{copied ? <Check size={14}/> : <Copy size={14}/>}</button></div>
    </div>
    {isDir && <>
      <div className="detail-section">
        <div className="section-title"><Layers size={13}/> FILE TYPE DISTRIBUTION</div>
        {breakdown.length ? breakdown.map(row => <div className="breakdown" key={row.name}>
          <div className="breakdown-label"><span className="type-dot" style={{ background: row.color }} />{row.name}</div>
          <span>{formatBytes(row.bytes)}</span>
          <div className="breakdown-track"><div style={{ width: `${node.size_bytes ? (row.bytes / node.size_bytes) * 100 : 0}%`, background: row.color }}/></div>
        </div>) : <div className="quiet-text">No matching files in this folder.</div>}
      </div>
      <div className="detail-section">
        <div className="section-title"><FileText size={13}/> LARGEST ITEMS</div>
        {topChildren.map(child => <button className="largest-item" key={child.id} title={child.relative_path} onClick={() => onSelect(child)}><span className="truncate">{child.name}</span><span>{formatBytes(child.size_bytes)}</span></button>)}
      </div>
    </>}
    {!isDir && <div className="detail-note"><Info size={15} /><span>Click a Python file to explore classes, functions, methods, and decorators. Odoo field semantics are planned for Phase 3.</span></div>}
  </div>;
}
