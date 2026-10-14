/** Metadata from the conservative AST-based Odoo 16–19 extractor. */
export type OdooClassInfo = {
  category: 'model' | 'transient' | 'abstract' | 'controller';
  model_name: string | null;
  inherits: string[];
  delegates: Record<string, string>;
  description: string | null;
  field_count: number;
  method_count: number;
  field_types: Record<string, number>;
};

export type OdooFieldInfo = {
  field_type: string;
  relation: string | null;
  string: string | null;
  compute: string | null;
  inverse: string | null;
  search: string | null;
  related: string | null;
  required: boolean | null;
  readonly: boolean | null;
  store: boolean | null;
  default: string | null;
  comodel_expression: string | null;
};

export type OdooRouteInfo = {
  paths: string[];
  auth: string | null;
  route_type: string | null;
  methods: string[];
  csrf: boolean | null;
};

export type OdooMethodInfo = {
  role: 'compute' | 'inverse' | 'search' | 'constraint' | 'onchange' |
    'orm_override' | 'controller_route' | 'cron' | 'business_action' | 'default' | 'other';
  api_decorators: string[];
  depends: string[];
  onchange_fields: string[];
  constraint_fields: string[];
  routes: OdooRouteInfo[];
};
