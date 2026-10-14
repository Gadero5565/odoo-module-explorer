import { ClipboardCopy, Code2, FileCode2, GitBranch, Layers3, ListTree, Tags } from 'lucide-react';
import { useState } from 'react';
import type { XMLSymbol } from '../types/xml';
import { formatBytes, formatNumber } from '../lib/analysis';

type Props = { node: XMLSymbol; modulePath: string; onSelect: (node: XMLSymbol) => void };

function Detail({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value === null || value === undefined || value === '') return null;
  return <div className="detail-stat"><span>{label}</span><strong>{value}</strong></div>;
}

export default function XMLDetails({ node, modulePath, onSelect }: Props) {
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
  return <div className="details-scroll">
    <div className="detail-heading">
      <div className="detail-icon">{node.kind === 'file' ? <FileCode2 size={22}/> : node.kind === 'xpath' ? <GitBranch size={22}/> : <Code2 size={22}/>}</div>
      <div className="detail-name-wrap"><div className="detail-name">{node.name}</div><div className="detail-sub">{node.kind.toUpperCase()} {node.tag ? `· <${node.tag}>` : '· XML source'}</div></div>
    </div>
    <div className="detail-section">
      <div className="section-title">XML STRUCTURE</div>
      <Detail label="Physical size" value={formatBytes(node.size_bytes)}/>
      <Detail label="Source lines touched" value={formatNumber(node.line_count)}/>
      <Detail label="Starts at" value={node.line_start ? `Line ${node.line_start}` : null}/>
      <Detail label="Ends at" value={node.line_end ? `Line ${node.line_end}` : null}/>
      <Detail label="Direct child elements" value={children.length}/>
      {node.kind !== 'file' && <Detail label="Element tag" value={node.tag}/>} 
    </div>
    {(meta.xml_id || meta.record_model || meta.target_model || meta.inherit_ref || meta.view_type || meta.action_res_model || meta.menu_parent || meta.menu_action) && <div className="detail-section">
      <div className="section-title"><Tags size={13}/> ODOO METADATA</div>
      <Detail label="XML ID" value={meta.xml_id}/>
      <Detail label="Record model" value={meta.record_model}/>
      <Detail label="Target model" value={meta.target_model}/>
      <Detail label="View type" value={meta.view_type}/>
      <Detail label="Inherits" value={meta.inherit_ref}/>
      <Detail label="Action target" value={meta.action_res_model}/>
      <Detail label="Menu parent" value={meta.menu_parent}/>
      <Detail label="Menu action" value={meta.menu_action}/>
    </div>}
    {(meta.xpath_expr || meta.qweb_name || meta.qweb_inherit || meta.qweb_call || meta.field_name || meta.field_ref) && <div className="detail-section">
      <div className="section-title"><GitBranch size={13}/> XML REFERENCES</div>
      <Detail label="XPath expression" value={meta.xpath_expr}/>
      <Detail label="XPath position" value={meta.xpath_position}/>
      <Detail label="QWeb name" value={meta.qweb_name}/>
      <Detail label="QWeb inherits" value={meta.qweb_inherit}/>
      <Detail label="QWeb mode" value={meta.qweb_mode}/>
      <Detail label="QWeb calls" value={meta.qweb_call}/>
      <Detail label="Field name" value={meta.field_name}/>
      <Detail label="Field ref" value={meta.field_ref}/>
    </div>}
    {Object.keys(meta.attributes).length > 0 && <div className="detail-section">
      <div className="section-title">ATTRIBUTES</div>
      {Object.entries(meta.attributes).map(([name, value]) => <div className="detail-stat" key={name}><span>{name}</span><strong title={value}>{value}</strong></div>)}
    </div>}
    <div className="detail-section"><div className="section-title">SOURCE LOCATION</div>
      <div className="path-card"><span title={location}>{node.relative_path}{node.line_start ? `:${node.line_start}` : ''}</span><button title="Copy file path and line" onClick={() => void copyLocation()}><ClipboardCopy size={14}/>{copied ? '✓' : ''}</button></div>
    </div>
    {!!children.length && <div className="detail-section">
      <div className="section-title"><ListTree size={13}/> DIRECT ELEMENTS</div>
      {children.slice(0, 100).map(child => <button className="largest-item" key={child.id} onClick={() => onSelect(child)}>
        <span className="truncate">{child.name}</span><span>{child.kind}</span>
      </button>)}
      {children.length > 100 && <p className="semantic-note">Showing the first 100 child elements. Use the treemap to browse more.</p>}
    </div>}
    <div className="detail-note"><Layers3 size={15}/><span>Static XML/QWeb structure only. Inheritance references and actions are not resolved in an Odoo registry. Element line counts can overlap on shared lines; byte-size totals remain exact.</span></div>
  </div>;
}
