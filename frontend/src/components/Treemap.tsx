import { useMemo, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { FileNode, Metric } from '../types/analysis';
import type { PythonSymbol } from '../types/python';
import type { XMLSymbol } from '../types/xml';
import type { JSSymbol } from '../types/javascript';
import type { StyleSymbol } from '../types/styles';
import { formatBytes, formatNumber, metricValue, nodeColor, sizeMetric } from '../lib/analysis';

type Props = {
  folder: FileNode | PythonSymbol | XMLSymbol | JSSymbol | StyleSymbol;
  metric: Metric;
  selectedId: string;
  onSelect: (node: FileNode | PythonSymbol | XMLSymbol | JSSymbol | StyleSymbol) => void;
};

export default function Treemap({ folder, metric, selectedId, onSelect }: Props) {
  const nodes = useRef(new Map<string, FileNode | PythonSymbol | XMLSymbol | JSSymbol | StyleSymbol>());
  nodes.current = new Map(folder.children.map(node => [node.id, node]));

  const option = useMemo<EChartsOption>(() => ({
    backgroundColor: 'transparent',
    animationDurationUpdate: 250,
    tooltip: {
      backgroundColor: '#151f30', borderColor: '#334359', borderWidth: 1,
      textStyle: { color: '#e8f0fa', fontSize: 12 },
      formatter: (params: any) => {
        const item = nodes.current.get(String(params.data?.id));
        if (!item) return '';
        return `<strong>${escapeHtml(item.name)}</strong>${"odoo_field" === item.kind ? " (Odoo field)" : "metadata" in item ? ` (${item.kind})` : ""}<br/>Size: ${formatBytes(item.size_bytes)}<br/>Files: ${"file_count" in item ? formatNumber(item.file_count) : "n/a"}<br/>Lines: ${formatNumber(item.line_count)}`;
      },
    },
    series: [{
      type: 'treemap',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      width: '100%',
      height: '100%',
      top: 0,
      left: 0,
      visibleMin: 0,
      squareRatio: 1.3,
      data: folder.children.map(node => ({
        id: node.id,
        name: node.name,
        value: sizeMetric(node, metric),
        itemStyle: {
          color: nodeColor(node),
          borderColor: node.id === selectedId ? '#f0f7ff' : '#101927',
          borderWidth: node.id === selectedId ? 3 : 2,
          gapWidth: 1,
        },
      })),
      label: {
        show: true, color: '#ffffff', fontSize: 12, fontWeight: 500,
        position: 'insideTopLeft', padding: [9, 10], overflow: 'truncate',
        formatter: (params: any) => {
          const item = nodes.current.get(String(params.data?.id));
          if (!item) return '';
          return `${item.name}\n${metric === 'size_bytes' ? formatBytes(item.size_bytes) : formatNumber(metricValue(item, metric)) + (metric === 'file_count' ? ' files' : ' lines')}`;
        },
      },
      upperLabel: { show: false },
      emphasis: { itemStyle: { borderColor: '#ffffff', borderWidth: 3 } },
      levels: [{ itemStyle: { borderWidth: 2, gapWidth: 2 } }],
    }],
  }), [folder, metric, selectedId]);

  if (!folder.children.length) {
    return <div className="empty-treemap">No files or folders match the active filters.</div>;
  }
  return <ReactECharts
    className="treemap-chart"
    option={option}
    notMerge
    style={{ width: '100%', height: '100%' }}
    onEvents={{ click: (params: any) => {
      const node = nodes.current.get(String(params.data?.id));
      if (node) onSelect(node);
    } }}
  />;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char] || char));
}
