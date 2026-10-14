import { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, FileCode2, File, Folder, FolderOpen } from 'lucide-react';
import type { FileNode } from '../types/analysis';
import { formatBytes } from '../lib/analysis';

type Props = {
  root: FileNode;
  selectedId: string;
  currentId: string;
  onSelect: (node: FileNode) => void;
};

export default function FolderTree({ root, selectedId, currentId, onSelect }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['.']));
  useEffect(() => {
    const path = currentId.split('/');
    const all = ['.'];
    path.reduce((prefix, segment) => {
      if (segment !== '.') {
        const next = prefix ? `${prefix}/${segment}` : segment;
        all.push(next);
        return next;
      }
      return prefix;
    }, '');
    setExpanded(prev => new Set([...prev, ...all]));
  }, [currentId]);

  const toggle = (id: string) => setExpanded(prev => {
    const copy = new Set(prev);
    if (copy.has(id)) copy.delete(id);
    else copy.add(id);
    return copy;
  });

  const renderNode = (node: FileNode, depth: number): React.ReactNode => {
    const isDir = node.kind === 'directory';
    const isOpen = expanded.has(node.id);
    return <div key={node.id}>
      <div
        className={`tree-line ${node.id === selectedId ? 'tree-selected' : ''} ${node.id === currentId ? 'tree-current' : ''}`}
        style={{ paddingLeft: 9 + depth * 15 }}
      >
        <button className="tree-twist" title={isDir ? (isOpen ? 'Collapse folder' : 'Expand folder') : ''} onClick={() => isDir && toggle(node.id)}>
          {isDir ? (isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />) : <span />}
        </button>
        <button className="tree-main" title={node.relative_path || node.name} onClick={() => onSelect(node)}>
          {isDir ? (isOpen ? <FolderOpen size={15} className="folder-icon"/> : <Folder size={15} className="folder-icon"/>) : (['.py', '.xml', '.js', '.scss', '.css'].includes(node.extension || '') ? <FileCode2 size={14}/> : <File size={14}/>)}
          <span className="truncate">{node.name}</span>
          <span className="file-size-mini">{formatBytes(node.size_bytes)}</span>
        </button>
      </div>
      {isDir && isOpen && node.children.map(child => renderNode(child, depth + 1))}
    </div>;
  };
  return <div className="folder-tree">{renderNode(root, 0)}</div>;
}
