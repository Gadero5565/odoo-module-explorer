import type { ModelLink } from '../types/insights';
import { relatedTo } from '../lib/insights';

type Props = {
  name: string;
  links: ModelLink[];
  onSelectModel: (name: string) => void;
};

export default function RelationshipGraph({ name, links, onSelectModel }: Props) {
  const connected = relatedTo(name, links);
  const others = [...new Set(connected.map(link => link.source === name ? link.target : link.source))].slice(0, 18);
  const points = new Map<string, { x: number; y: number }>();
  points.set(name, { x: 340, y: 195 });
  others.forEach((other, i) => {
    const angle = 2 * Math.PI * i / Math.max(others.length, 1) - Math.PI / 2;
    points.set(other, { x: 340 + 220 * Math.cos(angle), y: 195 + 132 * Math.sin(angle) });
  });
  const plottedLinks = connected.filter(link => points.has(link.source) && points.has(link.target));
  return <div className="relationship-graph" aria-label={`Model relationships for ${name}`}>
    <svg viewBox="0 0 680 390" role="img" aria-label={`Relationships: ${name} and ${others.length} connected models`}>
      <defs><marker id="edge-arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#688ead"/></marker></defs>
      {plottedLinks.map((link, i) => {
        const source = points.get(link.source)!;
        const target = points.get(link.target)!;
        return <g key={`${link.source}-${link.target}-${link.label}-${i}`}>
          <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#6384a3" strokeWidth="1.5" strokeOpacity=".8" markerEnd="url(#edge-arrow)"/>
          <title>{link.source} → {link.target}: {link.label} ({link.relation_type})</title>
        </g>;
      })}
      {[name, ...others].map(label => {
        const pt = points.get(label)!;
        const center = label === name;
        return <g key={label} role="button" tabIndex={0} className="graph-node" onClick={() => onSelectModel(label)}
          onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelectModel(label); } }}>
          <rect x={pt.x - (center ? 96 : 78)} y={pt.y - 21} width={center ? 192 : 156} height="42" rx="9" fill={center ? '#2860a0' : '#1d364c'} stroke={center ? '#8bc3ff' : '#567893'}/>
          <text x={pt.x} y={pt.y + 4} textAnchor="middle" fontSize="11" fill="#ecf5ff">{label.length > 24 ? `${label.slice(0, 22)}…` : label}</text>
          <title>{label}</title>
        </g>;
      })}
    </svg>
    {!connected.length && <div className="insight-muted">No statically detected outgoing or incoming relationships for this model.</div>}
    {others.length < new Set(connected.map(link => link.source === name ? link.target : link.source)).size && <div className="insight-muted">Graph shows 18 related models maximum; the complete relation list is below.</div>}
  </div>;
}
