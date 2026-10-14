/** XML/Odoo/QWeb normalized source inspection from /api/xml/inspect. */
export type XMLSymbolKind = 'file' | 'root' | 'record' | 'view' | 'action' | 'menu' | 'template' | 'xpath' | 'field' | 'element' | 'other';

export type XMLMetadata = {
  xml_id: string | null;
  record_model: string | null;
  target_model: string | null;
  inherit_ref: string | null;
  view_type: string | null;
  xpath_expr: string | null;
  xpath_position: string | null;
  qweb_name: string | null;
  qweb_inherit: string | null;
  qweb_mode: string | null;
  qweb_call: string | null;
  field_name: string | null;
  field_ref: string | null;
  menu_parent: string | null;
  menu_action: string | null;
  action_res_model: string | null;
  attributes: Record<string, string>;
  directive_count: number;
};

export type XMLSymbol = {
  id: string;
  name: string;
  kind: XMLSymbolKind;
  tag: string;
  relative_path: string;
  size_bytes: number;
  line_count: number;
  line_start: number | null;
  line_end: number | null;
  metadata: XMLMetadata;
  children: XMLSymbol[];
};

export type XMLInspection = {
  file: XMLSymbol;
  element_count: number;
  record_count: number;
  view_count: number;
  action_count: number;
  menu_count: number;
  template_count: number;
  xpath_count: number;
  field_count: number;
  parse_error: string | null;
};
