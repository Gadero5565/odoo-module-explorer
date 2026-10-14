export type FileNode = {
  id: string;
  name: string;
  relative_path: string;
  kind: 'directory' | 'file';
  extension: string | null;
  size_bytes: number;
  file_count: number;
  directory_count: number;
  line_count: number;
  children: FileNode[];
};

export type ModuleDetails = {
  name: string;
  absolute_path: string;
  version: string | null;
  detected_version: string | null;
  manifest_version: string | null;
  summary: string | null;
  application: boolean | null;
};

export type AnalysisResult = {
  module: ModuleDetails;
  root: FileNode;
  warnings: { relative_path: string; reason: string }[];
  ignored_entries: number;
};

export type Metric = 'size_bytes' | 'file_count' | 'line_count';
export type DisplayFilters = { sourceOnly: boolean; excludeData: boolean };
