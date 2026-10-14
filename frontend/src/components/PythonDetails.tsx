import { Braces, ClipboardCopy, FileCode2, Layers3, ListTree, Route, Database, Tags } from 'lucide-react';
import { useState } from 'react';
import type { PythonSymbol } from '../types/python';
import { formatBytes, formatNumber } from '../lib/analysis';

type Props = {
  node: PythonSymbol;
  modulePath: string;
  onSelect: (node: PythonSymbol) => void;
};

function Detail({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  if (value === null || value === undefined) return null;
  return <div className="detail-stat"><span>{label}</span><strong>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</strong></div>;
}

export default function PythonDetails({ node, modulePath, onSelect }: Props) {
  const [copied, setCopied] = useState(false);
  const symbols = node.children.filter(child => child.kind !== 'code');
  const fields = symbols.filter(child => child.kind === 'odoo_field');
  const definitions = symbols.filter(child => child.kind !== 'odoo_field');
  const absolute = `${modulePath.replace(/[\\/]$/, '')}${modulePath.includes('\\') ? '\\' : '/'}${node.relative_path.replaceAll('/', modulePath.includes('\\') ? '\\' : '/')}`;
  const location = node.line_start ? `${absolute}:${node.line_start}` : absolute;
  const copyLocation = async () => {
    try {
      await navigator.clipboard.writeText(location);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch { setCopied(false); }
  };
  const klass = node.odoo_class;
  const field = node.odoo_field;
  const method = node.odoo_method;

  return <div className="details-scroll">
    <div className="detail-heading">
      <div className="detail-icon">{klass ? <Database size={22}/> : field ? <Tags size={22}/> : node.kind === 'file' ? <FileCode2 size={22}/> : <Braces size={22}/>}</div>
      <div className="detail-name-wrap"><div className="detail-name">{node.name}</div><div className="detail-sub">{field ? `Odoo ${field.field_type} field` : klass ? `Odoo ${klass.category}` : node.kind.replaceAll('_', ' ')} {node.parameters || ''}</div></div>
    </div>
    <div className="detail-section">
      <div className="section-title">PYTHON STRUCTURE</div>
      <Detail label="Physical size" value={formatBytes(node.size_bytes)}/>
      <Detail label="Physical lines" value={formatNumber(node.line_count)}/>
      {node.line_start !== null && <Detail label="Starts at" value={`Line ${node.line_start}`}/>}
      {node.line_end !== null && <Detail label="Ends at" value={`Line ${node.line_end}`}/>}
      {node.kind !== 'code' && <Detail label="Direct symbols" value={formatNumber(symbols.length)}/>}
    </div>
    {klass && <div className="detail-section">
      <div className="section-title"><Database size={13}/> ODOO {klass.category.toUpperCase()}</div>
      <Detail label="_name" value={klass.model_name}/>
      <Detail label="_description" value={klass.description}/>
      <Detail label="_inherit" value={klass.inherits.join(', ') || null}/>
      <Detail label="_inherits" value={Object.entries(klass.delegates).map(([model, key]) => `${model}: ${key}`).join(', ') || null}/>
      {klass.category !== 'controller' && <>
        <Detail label="Fields shown" value={fields.length}/>
        <Detail label="Fields in source" value={klass.field_count}/>
        <Detail label="Direct methods" value={klass.method_count}/>
        {!!fields.length && !!Object.keys(klass.field_types).length && <div className="odoo-type-summary">{Object.entries(klass.field_types).sort((a, b) => b[1] - a[1]).map(([name, count]) => <span className="odoo-chip" key={name}>{name} × {count}</span>)}</div>}
      </>}
      {!klass.model_name && klass.inherits.length > 0 && <p className="semantic-note">Extension-only class: the Odoo registry may combine it with other classes.</p>}
    </div>}
    {field && <div className="detail-section">
      <div className="section-title"><Tags size={13}/> ODOO FIELD</div>
      <Detail label="Type" value={field.field_type}/>
      <Detail label="Label" value={field.string}/>
      <Detail label="Comodel" value={field.relation || field.comodel_expression}/>
      <Detail label="Compute" value={field.compute}/>
      <Detail label="Inverse" value={field.inverse}/>
      <Detail label="Search" value={field.search}/>
      <Detail label="Related" value={field.related}/>
      <Detail label="Required" value={field.required}/>
      <Detail label="Readonly" value={field.readonly}/>
      <Detail label="Stored" value={field.store}/>
      <Detail label="Default expression" value={field.default}/>
    </div>}
    {method && (method.role !== 'other' || method.api_decorators.length > 0) && <div className="detail-section">
      <div className="section-title"><Braces size={13}/> ODOO METHOD</div>
      <Detail label="Role" value={method.role.replaceAll('_', ' ')}/>
      {!!method.api_decorators.length && <Detail label="API decorators" value={method.api_decorators.join(', ')}/>}
      {!!method.depends.length && <Detail label="Depends on" value={method.depends.join(', ')}/>}
      {!!method.onchange_fields.length && <Detail label="Onchange fields" value={method.onchange_fields.join(', ')}/>}
      {!!method.constraint_fields.length && <Detail label="Constraint fields" value={method.constraint_fields.join(', ')}/>}
      {method.routes.map((route, i) => <div className="odoo-route" key={i}>
        <div className="section-title"><Route size={13}/> ROUTE {i + 1}</div>
        <Detail label="Paths" value={route.paths.join(', ') || '(dynamic)'}/>
        <Detail label="Auth" value={route.auth}/>
        <Detail label="Type" value={route.route_type}/>
        <Detail label="Methods" value={route.methods.join(', ') || null}/>
        <Detail label="CSRF" value={route.csrf}/>
      </div>)}
    </div>}
    {!!node.decorators.length && <div className="detail-section">
      <div className="section-title">DECORATORS</div>
      {node.decorators.map((value, index) => <div key={index} className="symbol-decorator">@{value}</div>)}
    </div>}
    <div className="detail-section">
      <div className="section-title">SOURCE LOCATION</div>
      <div className="path-card"><span title={location}>{node.relative_path}{node.line_start ? `:${node.line_start}` : ''}</span><button title="Copy file path and line" onClick={() => void copyLocation()}><ClipboardCopy size={14}/>{copied ? '✓' : ''}</button></div>
    </div>
    {!!fields.length && <div className="detail-section">
      <div className="section-title"><Tags size={13}/> ODOO FIELDS</div>
      {fields.map(child => <button key={child.id} className="largest-item" onClick={() => onSelect(child)}>
        <span className="truncate">{child.name}</span><span>{child.odoo_field?.field_type}</span>
      </button>)}
    </div>}
    {!!definitions.length && <div className="detail-section">
      <div className="section-title"><ListTree size={13}/> NESTED DEFINITIONS</div>
      {definitions.map(child => <button key={child.id} className="largest-item" onClick={() => onSelect(child)}>
        <span className="truncate">{child.name}</span><span>{child.odoo_method?.role !== 'other' && child.odoo_method ? child.odoo_method.role.replaceAll('_', ' ') : formatBytes(child.size_bytes)}</span>
      </button>)}
    </div>}
    <div className="detail-note"><Layers3 size={15}/><span>Static Odoo 16–19 analysis; no source is executed. Missing or dynamically generated metadata is unknown. “Other code” includes source outside named definitions and recognized field declarations.</span></div>
  </div>;
}
