import type { DisplayFilters, FileNode, Metric } from '../types/analysis';
import type { PythonSymbol } from '../types/python';

const SOURCE_EXTENSIONS = new Set(['.py', '.xml', '.js', '.jsx', '.ts', '.tsx', '.scss', '.css', '.less']);
const EXCLUDED_DIRS = new Set(['data', 'demo', 'i18n']);

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)) - 1, units.length - 1);
  const amount = bytes / 1024 ** (index + 1);
  return `${amount >= 100 ? amount.toFixed(0) : amount >= 10 ? amount.toFixed(1) : amount.toFixed(2)} ${units[index]}`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function filterTree(node: FileNode, filters: DisplayFilters): FileNode | null {
  if (node.kind === 'file') {
    if (filters.sourceOnly && !SOURCE_EXTENSIONS.has(node.extension || '')) return null;
    return node;
  }
  if (node.relative_path && filters.excludeData && EXCLUDED_DIRS.has(node.name.toLowerCase())) return null;
  const children = node.children
    .map(child => filterTree(child, filters))
    .filter((child): child is FileNode => child !== null)
    .sort((a, b) => b.size_bytes - a.size_bytes || a.name.localeCompare(b.name));
  if (node.relative_path && filters.sourceOnly && !children.length) return null;
  return {
    ...node,
    children,
    size_bytes: children.reduce((sum, child) => sum + child.size_bytes, 0),
    line_count: children.reduce((sum, child) => sum + child.line_count, 0),
    file_count: children.reduce((sum, child) => sum + child.file_count, 0),
    directory_count: children.reduce((sum, child) => sum + child.directory_count + (child.kind === 'directory' ? 1 : 0), 0),
  };
}

export function indexNodes(root: FileNode): Map<string, FileNode> {
  const index = new Map<string, FileNode>();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop()!;
    index.set(node.id, node);
    stack.push(...node.children);
  }
  return index;
}

export function parentId(id: string): string {
  if (id === '.') return '.';
  const index = id.lastIndexOf('/');
  return index < 0 ? '.' : id.slice(0, index);
}

export function metricValue(node: FileNode | PythonSymbol, metric: Metric): number {
  if (metric === 'file_count') return 'file_count' in node ? node.file_count : 0;
  return node[metric];
}

export function sizeMetric(node: FileNode | PythonSymbol, metric: Metric): number {
  // ECharts cannot display zero-area rectangles. A minimal rectangle keeps
  // files with zero LOC and empty directories selectable in other modes.
  return Math.max(metricValue(node, metric), 1);
}

export function fileCategory(ext: string | null): string {
  const type = ext?.toLowerCase() || '';
  if (type === '.py') return 'Python';
  if (type === '.xml') return 'XML';
  if (['.js', '.jsx', '.ts', '.tsx'].includes(type)) return 'JavaScript';
  if (['.css', '.scss', '.less'].includes(type)) return 'Styles';
  if (['.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.ico'].includes(type)) return 'Images';
  if (type === '.csv') return 'CSV';
  if (type === '.po' || type === '.pot') return 'Translation';
  return 'Other';
}

export function categoryColor(category: string): string {
  return ({ Python: '#4e97ee', XML: '#5ac8ad', JavaScript: '#ad88f6', Styles: '#e3a85d', Images: '#d77c92', CSV: '#8aa1b7', Translation: '#8aa1b7', Other: '#607890' } as Record<string, string>)[category] || '#4e97ee';
}

export function nodeColor(node: FileNode | PythonSymbol): string {
  if (node.kind === 'directory') return '#347dba';
  if (node.kind === 'odoo_field') return '#39b9a5';
  if (node.kind === 'class') return '#529ce7';
  if (node.kind === 'method' || node.kind === 'async_method') return '#6ab6d2';
  if (node.kind === 'function' || node.kind === 'async_function') return '#907fda';
  if (node.kind === 'code') return '#53677c';
  return categoryColor(fileCategory('extension' in node ? node.extension : '.py'));
}

export function indexPythonSymbols(root: PythonSymbol): Map<string, PythonSymbol> {
  const index = new Map<string, PythonSymbol>();
  const stack = [root];
  while (stack.length) {
    const item = stack.pop()!;
    index.set(item.id, item);
    stack.push(...item.children);
  }
  return index;
}

export function pythonSymbolPath(root: PythonSymbol, wanted: string): PythonSymbol[] {
  if (root.id === wanted) return [root];
  for (const child of root.children) {
    const path = pythonSymbolPath(child, wanted);
    if (path.length) return [root, ...path];
  }
  return [];
}

export function getFileBreakdown(root: FileNode): { name: string; count: number; bytes: number; color: string }[] {
  const stats = new Map<string, { count: number; bytes: number }>();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop()!;
    if (node.kind === 'directory') stack.push(...node.children);
    else {
      const category = fileCategory(node.extension);
      const value = stats.get(category) || { count: 0, bytes: 0 };
      stats.set(category, { count: value.count + 1, bytes: value.bytes + node.size_bytes });
    }
  }
  return [...stats].map(([name, stats]) => ({ name, ...stats, color: categoryColor(name) }))
    .sort((a, b) => b.bytes - a.bytes || a.name.localeCompare(b.name));
}
