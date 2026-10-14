import type { InsightMetric, InsightSymbol, ModelLink } from '../types/insights';

export function searchSymbols(symbols: InsightSymbol[], query: string, kind: string, model = ''): InsightSymbol[] {
  const q = query.trim().toLocaleLowerCase();
  return symbols.filter(symbol => {
    if (kind !== 'all' && symbol.kind !== kind) return false;
    if (model && symbol.owner_model !== model) return false;
    if (!q) return true;
    return [symbol.name, symbol.relative_path, symbol.kind, symbol.owner_model || '', symbol.detail || '']
      .some(value => value.toLocaleLowerCase().includes(q));
  });
}

export function rankSymbols(symbols: InsightSymbol[], metric: InsightMetric): InsightSymbol[] {
  return [...symbols].sort((a, b) => (b[metric] || 0) - (a[metric] || 0) ||
    a.relative_path.localeCompare(b.relative_path) || (a.line_start || 0) - (b.line_start || 0));
}

export function relatedTo(model: string, links: ModelLink[]): ModelLink[] {
  return links.filter(link => link.source === model || link.target === model);
}
