/** Read-only CSS/SCSS source structure. All byte sizes are physical UTF-8. */
export type StyleKind = 'file' | 'selector' | 'declaration' | 'variable' | 'mixin' |
  'function' | 'include' | 'at_rule' | 'keyframes' | 'other';
export type StyleMetadata = {
  prelude?: string | null;
  property?: string | null;
  value?: string | null;
  selector?: string | null;
  at_rule?: string | null;
  parameters?: string | null;
  import_target?: string | null;
  important?: boolean;
  nested?: boolean;
};
export type StyleSymbol = {
  id: string;
  name: string;
  kind: StyleKind;
  relative_path: string;
  size_bytes: number;
  line_count: number;
  line_start: number | null;
  line_end: number | null;
  metadata: StyleMetadata;
  children: StyleSymbol[];
};
export type StyleInspection = {
  file: StyleSymbol;
  syntax: 'css' | 'scss';
  selector_count: number;
  declaration_count: number;
  variable_count: number;
  mixin_count: number;
  function_count: number;
  include_count: number;
  at_rule_count: number;
  keyframes_count: number;
  imports: string[];
  parse_error: string | null;
};
