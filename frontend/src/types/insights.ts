export type InsightSymbol = {
  id: string;
  name: string;
  kind: string;
  relative_path: string;
  line_start: number | null;
  line_end: number | null;
  size_bytes: number;
  line_count: number;
  complexity: number | null;
  owner_model: string | null;
  detail: string | null;
};

export type ModelLink = {
  source: string;
  target: string;
  label: string;
  relation_type: string;
  relative_path: string;
  line_start: number | null;
  local_target: boolean;
};

export type OdooModelSummary = {
  name: string;
  defined_here: boolean;
  source_classes: InsightSymbol[];
  fields: InsightSymbol[];
  methods: InsightSymbol[];
  views: InsightSymbol[];
  actions: InsightSymbol[];
  relations: ModelLink[];
  inherits: string[];
  delegates: string[];
};

export type InsightsResponse = {
  symbols: InsightSymbol[];
  models: OdooModelSummary[];
  relationships: ModelLink[];
  inspected_files: number;
  skipped_files: number;
  warnings: string[];
  truncated: boolean;
};

export type InsightMetric = 'size_bytes' | 'line_count' | 'complexity';
