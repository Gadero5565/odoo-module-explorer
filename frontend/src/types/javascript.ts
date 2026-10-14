/** Normalized static JS/OWL exploration response. */
export type JSSymbolKind = 'file' | 'class' | 'function' | 'method' | 'property' | 'service' | 'registration' | 'module' | 'code';
export type JSMetadata = {
  extends?: string[];
  is_owl_component?: boolean;
  template?: string | null;
  components?: string[];
  props?: string | null;
  hooks?: string[];
  async?: boolean;
  parameters?: string | null;
  exported?: boolean;
  dependencies?: string[];
  properties?: string[];
  registry_category?: string | null;
  registry_key?: string | null;
  registry_target?: string | null;
  module_name?: string | null;
  module_format?: string;
  expression?: string | null;
};
export type JSSymbol = {
  id: string;
  name: string;
  kind: JSSymbolKind;
  relative_path: string;
  size_bytes: number;
  line_count: number;
  line_start: number | null;
  line_end: number | null;
  metadata: JSMetadata;
  children: JSSymbol[];
};
export type JSInspection = {
  file: JSSymbol;
  symbol_count: number;
  component_count: number;
  service_count: number;
  registration_count: number;
  imports: { source: string | null; names: string | null }[];
  registrations: { category: string | null; key: string | null; target: string | null; line: number }[];
  parse_error: string | null;
};
