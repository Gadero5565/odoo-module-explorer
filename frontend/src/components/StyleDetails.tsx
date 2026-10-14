import { ClipboardCopy, FileCode2, Layers3, ListTree, Paintbrush, Variable, Braces } from 'lucide-react';
import { useState } from 'react';
import type { StyleInspection, StyleSymbol } from '../types/styles';
import { formatBytes, formatNumber } from '../lib/analysis';

type Props = {
  node: StyleSymbol;
  inspection: StyleInspection | null;
  modulePath: string;
  onSelect: (node: StyleSymbol) => void;
};

function Detail({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  if (value === null || value === undefined || value === '') return null;
  return <div className="detail-stat"><span>{label}</span><strong title={String(value)}>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</strong></div>;
}

export default function StyleDetails({ node, inspection, modulePath, onSelect }: Props) {
  const [copied, setCopied] = useState(false);
  const meta = node.metadata;
  const absolute = `${modulePath.replace(/[\\/]$/, '')}${modulePath.includes('\\') ? '\\' : '/'}${node.relative_path.replaceAll('/', modulePath.includes('\\') ? '\\' : '/')}`;
  const location = node.line_start ? `${absolute}:${node.line_start}` : absolute;
  const copyLocation = async () => {
    try {
      await navigator.clipboard.writeText(location);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch { setCopied(false); }
  };
  const children = node.children.filter(child => child.kind !== 'other');
  const isFile = node.kind === 'file';
  return <div className="details-scroll">
    <div className="detail-heading">
      <div className="detail-icon">{node.kind === 'variable' ? <Variable size={22}/> : node.kind === 'mixin' || node.kind === 'function' ? <Braces size={22}/> : isFile ? <FileCode2 size={22}/> : <Paintbrush size={22}/>}</div>
      <div className="detail-name-wrap"><div className="detail-name">{node.name}</div><div className="detail-sub">{node.kind.replaceAll('_', ' ')} · {inspection?.syntax.toUpperCase() || 'Stylesheet'}</div></div>
    </div>
    <div className="detail-section">
      <div className="section-title">STYLESHEET STRUCTURE</div>
      <Detail label="Physical size" value={formatBytes(node.size_bytes)}/>
      <Detail label="Physical lines" value={formatNumber(node.line_count)}/>
      <Detail label="Starts at" value={node.line_start ? `Line ${node.line_start}` : null}/>
      <Detail label="Ends at" value={node.line_end ? `Line ${node.line_end}` : null}/>
      <Detail label="Direct child rules" value={formatNumber(children.length)}/>
    </div>
    {isFile && inspection && <div className="detail-section">
      <div className="section-title"><Layers3 size={13}/> FILE STATISTICS</div>
      <Detail label="Selectors" value={inspection.selector_count}/>
      <Detail label="Declarations" value={inspection.declaration_count}/>
      <Detail label="Variables" value={inspection.variable_count}/>
      <Detail label="Mixins" value={inspection.mixin_count}/>
      <Detail label="Functions" value={inspection.function_count}/>
      <Detail label="Includes" value={inspection.include_count}/>
      <Detail label="At-rules" value={inspection.at_rule_count}/>
      <Detail label="Keyframes" value={inspection.keyframes_count}/>
      {!!inspection.imports.length && <>
        <div className="section-title">IMPORT / USE / FORWARD REFERENCES</div>
        {inspection.imports.map((value, index) => <div className="detail-stat" key={index}><span title={value}>{value}</span></div>)}
      </>}
    </div>}
    {(meta.prelude || meta.selector || meta.property || meta.at_rule) && <div className="detail-section">
      <div className="section-title"><Paintbrush size={13}/> DECLARATION / RULE</div>
      <Detail label="Selector" value={meta.selector}/>
      <Detail label="Property" value={meta.property}/>
      <Detail label="Value" value={meta.value}/>
      <Detail label="At-rule" value={meta.at_rule}/>
      <Detail label="Parameters" value={meta.parameters}/>
      <Detail label="Import target" value={meta.import_target}/>
      {meta.important && <Detail label="Important" value="!important"/>}
      <div className="semantic-note" title={meta.prelude || ''}>{meta.prelude}</div>
    </div>}
    <div className="detail-section">
      <div className="section-title">SOURCE LOCATION</div>
      <div className="path-card"><span title={location}>{node.relative_path}{node.line_start ? `:${node.line_start}` : ''}</span><button title="Copy file path and line" onClick={() => void copyLocation()}><ClipboardCopy size={14}/>{copied ? '✓' : ''}</button></div>
    </div>
    {!!children.length && <div className="detail-section">
      <div className="section-title"><ListTree size={13}/> CHILD DEFINITIONS</div>
      {children.slice(0, 100).map(child => <button key={child.id} className="largest-item" onClick={() => onSelect(child)}><span className="truncate">{child.name}</span><span>{child.kind}</span></button>)}
      {children.length > 100 && <p className="semantic-note">Showing the first 100 child definitions.</p>}
    </div>}
    <div className="detail-note"><Layers3 size={15}/><span>Read-only structural inspection, not a Sass compiler. Imported files, Sass expressions, selector specificity and Odoo asset bundles are not resolved here. Other source/comments nodes preserve physical bytes.</span></div>
  </div>;
}
