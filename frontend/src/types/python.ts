import type { OdooClassInfo, OdooFieldInfo, OdooMethodInfo } from './odoo';

export type PythonSymbolKind = 'file' | 'class' | 'method' | 'function' | 'async_method' | 'async_function' | 'code' | 'odoo_field';

export type PythonSymbol = {
  id: string;
  name: string;
  kind: PythonSymbolKind;
  relative_path: string;
  size_bytes: number;
  line_count: number;
  line_start: number | null;
  line_end: number | null;
  column_start: number | null;
  decorators: string[];
  parameters: string | null;
  odoo_class: OdooClassInfo | null;
  odoo_field: OdooFieldInfo | null;
  odoo_method: OdooMethodInfo | null;
  children: PythonSymbol[];
};

export type PythonInspection = {
  file: PythonSymbol;
  symbol_count: number;
  odoo_model_count: number;
  odoo_field_count: number;
  odoo_route_count: number;
  parse_error: string | null;
};
