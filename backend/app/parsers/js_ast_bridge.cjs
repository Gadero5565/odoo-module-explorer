/**
 * JavaScript/OWL syntax explorer. Uses the TypeScript compiler's JS grammar,
 * not eval/require/import of user source. stdin = UTF-8 addon source.
 * Installed by frontend/npm install (TypeScript is already a dev dependency).
 */
'use strict';
const path = require('node:path');
const fs = require('node:fs');

function loadTypeScript() {
  const projectFrontend = path.resolve(__dirname, '../../../frontend');
  const candidates = [];
  if (process.env.ODOO_EXPLORER_TYPESCRIPT_PATH) candidates.push(process.env.ODOO_EXPLORER_TYPESCRIPT_PATH);
  // Built release wheels include the TypeScript grammar, so end users do not
  // need node_modules/npm. Node.js itself is still required for inspection.
  candidates.push(path.resolve(__dirname, '../vendor/typescript.js'));
  try { candidates.push(require.resolve('typescript', { paths: [projectFrontend] })); } catch (_) { /* fallback below */ }
  for (const item of candidates) {
    try { return require(item); } catch (_) { /* next candidate */ }
  }
  throw new Error('TypeScript parser missing. For source use npm ci in frontend, or install a built release wheel.');
}

function inspect(ts, relativePath, source) {
  const sf = ts.createSourceFile(relativePath, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
  const fullBytes = Buffer.byteLength(source, 'utf8');
  const location = pos => sf.getLineAndCharacterOfPosition(pos).line + 1;
  const short = (node, limit = 220) => node ? node.getText(sf).replace(/\s+/g, ' ').slice(0, limit) : null;
  const stringValue = node => node && (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) ? node.text : null;
  const nameOf = node => node && (ts.isIdentifier(node) || ts.isPrivateIdentifier(node)) ? node.text : short(node, 90);
  const imports = [];
  const registrations = [];
  const serviceNames = new Set();
  const componentAliases = new Set(['Component']);
  const registryAliases = new Set(['registry']);
  const MAX_NODES = 18000;
  let nodeCount = 0;
  const newNode = (name, kind, start, end, metadata = {}) => {
    if (++nodeCount > MAX_NODES) throw new Error('JavaScript source exceeds the 18,000 symbol limit.');
    return { name, kind, start, end, metadata, children: [] };
  };
  function registryInfo(node) {
    if (!ts.isCallExpression(node) || !ts.isPropertyAccessExpression(node.expression) || node.expression.name.text !== 'add') return null;
    const categoryCall = node.expression.expression;
    if (!ts.isCallExpression(categoryCall) || !ts.isPropertyAccessExpression(categoryCall.expression) || categoryCall.expression.name.text !== 'category') return null;
    const registryExpr = categoryCall.expression.expression;
    if (!registryAliases.has(nameOf(registryExpr))) return null;
    return { category: stringValue(categoryCall.arguments[0]) || short(categoryCall.arguments[0], 100),
      key: stringValue(node.arguments[0]) || short(node.arguments[0], 100),
      target: nameOf(node.arguments[1]) || null };
  }
  function walkAll(node, visitor) { visitor(node); ts.forEachChild(node, ch => walkAll(ch, visitor)); }
  walkAll(sf, node => {
    if (ts.isImportDeclaration(node)) {
      const origin = stringValue(node.moduleSpecifier);
      const named = node.importClause?.namedBindings;
      if (named && ts.isNamedImports(named)) {
        for (const spec of named.elements) {
          const imported = spec.propertyName?.text || spec.name.text;
          if (origin === '@odoo/owl' && imported === 'Component') componentAliases.add(spec.name.text);
          if (origin === '@web/core/registry' && imported === 'registry') registryAliases.add(spec.name.text);
        }
      }
      imports.push({ source: stringValue(node.moduleSpecifier) || short(node.moduleSpecifier),
        names: node.importClause ? short(node.importClause, 250) : null });
    }
    if (ts.isCallExpression(node)) {
      const data = registryInfo(node);
      if (data) {
        registrations.push({ ...data, line: location(node.getStart(sf)) });
        if (data.category === 'services' && data.target) serviceNames.add(data.target);
      }
    }
  });
  const hooks = new Set(['useState', 'useRef', 'useService', 'useBus', 'useEnv', 'useSubEnv', 'useExternalListener',
    'onMounted', 'onWillStart', 'onWillUnmount', 'onPatched', 'onWillPatch', 'onRendered', 'onError']);
  function collectHooks(node) {
    const found = new Set();
    walkAll(node, ch => {
      if (ts.isCallExpression(ch)) {
        const expr = ch.expression;
        const name = ts.isIdentifier(expr) ? expr.text : ts.isPropertyAccessExpression(expr) ? expr.name.text : null;
        if (name && hooks.has(name)) found.add(name);
      }
    });
    return [...found].sort();
  }
  function objectItems(obj) {
    const items = [];
    if (!obj || !ts.isObjectLiteralExpression(obj)) return items;
    for (const property of obj.properties) {
      if (ts.isPropertyAssignment(property)) items.push(nameOf(property.name));
      else if (ts.isShorthandPropertyAssignment(property) || ts.isMethodDeclaration(property)) items.push(nameOf(property.name));
    }
    return items.filter(Boolean);
  }
  function classMetadata(node) {
    const parents = (node.heritageClauses || []).flatMap(clause => clause.types.map(t => short(t.expression, 120)));
    const properties = node.members.filter(m => ts.isPropertyDeclaration(m));
    const named = key => properties.find(m => nameOf(m.name) === key);
    const template = named('template');
    const components = named('components');
    const props = named('props');
    const component = parents.some(p => componentAliases.has(p) || p?.endsWith('.Component'));
    return { extends: parents, is_owl_component: component,
      template: template ? stringValue(template.initializer) || short(template.initializer, 120) : null,
      components: components ? objectItems(components.initializer) : [],
      props: props ? short(props.initializer, 160) : null,
      hooks: collectHooks(node) };
  }
  function functionMetadata(node) {
    return { async: Boolean(node.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword)),
      parameters: node.parameters ? node.parameters.map(p => short(p, 100)).join(', ') : null,
      hooks: collectHooks(node),
      exported: Boolean(node.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword)) };
  }
  function declarationChildren(body) {
    const entries = [];
    if (!body) return entries;
    function visit(statement) {
      if (ts.isBlock(statement) || ts.isModuleBlock(statement)) { statement.statements.forEach(visit); return; }
      const symbols = extract(statement, false);
      if (symbols.length) { entries.push(...symbols); return; }
      ts.forEachChild(statement, ch => {
        if (ts.isBlock(ch) || ts.isIfStatement(ch) || ts.isForStatement(ch) || ts.isWhileStatement(ch) || ts.isTryStatement(ch)) visit(ch);
      });
    }
    ts.forEachChild(body, ch => { if (ts.isStatement(ch)) visit(ch); });
    return entries;
  }
  function classSymbol(node, explicitName) {
    const symbol = newNode(explicitName || nameOf(node.name) || '(anonymous class)', 'class', node.getStart(sf), node.end, classMetadata(node));
    symbol.children = node.members.flatMap(m => {
      if (ts.isMethodDeclaration(m) || ts.isConstructorDeclaration(m) || ts.isGetAccessorDeclaration(m) || ts.isSetAccessorDeclaration(m)) {
        const child = newNode(ts.isConstructorDeclaration(m) ? 'constructor' : nameOf(m.name), 'method', m.getStart(sf), m.end, functionMetadata(m));
        child.children = declarationChildren(m.body);
        return [child];
      }
      if (ts.isPropertyDeclaration(m)) {
        const propertyName = nameOf(m.name) || 'property';
        const isFn = m.initializer && (ts.isArrowFunction(m.initializer) || ts.isFunctionExpression(m.initializer));
        const child = newNode(propertyName, isFn ? 'method' : 'property', m.getStart(sf), m.end, isFn ? functionMetadata(m.initializer) : { expression: short(m.initializer) });
        if (isFn) child.children = declarationChildren(m.initializer.body);
        return [child];
      }
      return [];
    });
    return symbol;
  }
  function functionSymbol(node, label, kind) {
    const sym = newNode(label || nameOf(node.name) || '(anonymous)', kind,
      node.getStart(sf), node.end, functionMetadata(node));
    sym.children = declarationChildren(node.body);
    return sym;
  }
  function objectService(node, name, spanStart, spanEnd) {
    const dependencies = node.properties.find(p => ts.isPropertyAssignment(p) && nameOf(p.name) === 'dependencies');
    const sym = newNode(name, 'service', spanStart, spanEnd, {
      dependencies: dependencies && ts.isArrayLiteralExpression(dependencies.initializer)
        ? dependencies.initializer.elements.map(v => stringValue(v) || short(v, 60)) : [],
      properties: objectItems(node),
    });
    sym.children = node.properties.flatMap(p => {
      if (ts.isMethodDeclaration(p)) {
        const child = newNode(nameOf(p.name), 'method', p.getStart(sf), p.end, functionMetadata(p));
        child.children = declarationChildren(p.body);
        return [child];
      }
      if (ts.isPropertyAssignment(p) && (ts.isFunctionExpression(p.initializer) || ts.isArrowFunction(p.initializer))) {
        const child = newNode(nameOf(p.name), 'method', p.getStart(sf), p.end, functionMetadata(p.initializer));
        child.children = declarationChildren(p.initializer.body);
        return [child];
      }
      return [];
    });
    return sym;
  }
  function extract(statement, topLevel) {
    if (ts.isClassDeclaration(statement)) return [classSymbol(statement)];
    if (ts.isFunctionDeclaration(statement)) return [functionSymbol(statement, null, 'function')];
    if (ts.isVariableStatement(statement)) {
      const decls = statement.declarationList.declarations;
      if (decls.length === 1) {
        const decl = decls[0], name = nameOf(decl.name), value = decl.initializer;
        if (value && ts.isClassExpression(value)) return [classSymbol(value, name)];
        if (value && (ts.isArrowFunction(value) || ts.isFunctionExpression(value))) {
          const item = newNode(name, 'function', statement.getStart(sf), statement.end, functionMetadata(value));
          item.children = declarationChildren(value.body);
          return [item];
        }
        if (topLevel && value && ts.isObjectLiteralExpression(value) && serviceNames.has(name)) {
          return [objectService(value, name, statement.getStart(sf), statement.end)];
        }
      }
      return [];
    }
    if (topLevel && ts.isExpressionStatement(statement) && ts.isCallExpression(statement.expression)) {
      const r = registryInfo(statement.expression);
      if (r) return [newNode(`${r.category || 'registry'}: ${r.key || '?'}`, 'registration',
        statement.getStart(sf), statement.end, { registry_category: r.category, registry_key: r.key, registry_target: r.target })];
      const expr = statement.expression.expression;
      if (ts.isPropertyAccessExpression(expr) && nameOf(expr.expression) === 'odoo' && expr.name.text === 'define') {
        const wrapper = newNode(stringValue(statement.expression.arguments[0]) || 'odoo.define', 'module',
          statement.getStart(sf), statement.end, { module_name: stringValue(statement.expression.arguments[0]) });
        const factory = statement.expression.arguments[1];
        if (factory && (ts.isFunctionExpression(factory) || ts.isArrowFunction(factory))) {
          wrapper.children = declarationChildren(factory.body);
        }
        return [wrapper];
      }
    }
    return [];
  }
  // A source file with parser errors is represented as a single raw source block.
  // Do not claim semantic metadata from partially recovered syntax trees.
  const diag = sf.parseDiagnostics || [];
  if (diag.length) {
    const d = diag[0];
    const message = ts.flattenDiagnosticMessageText(d.messageText, ' ');
    return { file: { id: relativePath, name: path.posix.basename(relativePath), kind: 'file',
      relative_path: relativePath, size_bytes: fullBytes,
      line_count: source ? source.split('\n').length : 0, line_start: source ? 1 : null,
      line_end: source ? location(source.length) : null, metadata: {}, children: [] },
      symbol_count: 0, component_count: 0, service_count: 0, registration_count: 0,
      imports, registrations: [], parse_error: `JavaScript syntax error (line ${location(d.start || 0)}): ${message}` };
  }
  const symbols = sf.statements.flatMap(st => extract(st, true));
  const bytePoints = new Map([[0, 0], [source.length, fullBytes]]);
  function collectPoints(item) {
    bytePoints.set(item.start, 0); bytePoints.set(item.end, 0);
    item.children.forEach(collectPoints);
  }
  symbols.forEach(collectPoints);
  // Resolve all UTF-16 offsets in one linear pass, important for large OWL modules.
  const sortedPoints = [...bytePoints.keys()].sort((a, b) => a - b);
  let previous = 0, byteOffset = 0;
  for (const point of sortedPoints) {
    byteOffset += Buffer.byteLength(source.slice(previous, point), 'utf8');
    bytePoints.set(point, byteOffset); previous = point;
  }
  function resolveChildren(parentId, start, end, entries) {
    let cursor = start, counter = 0;
    const children = [];
    const sorted = [...entries].sort((a, b) => a.start - b.start || b.end - a.end);
    for (const item of sorted) {
      if (item.start < cursor || item.end > end || item.end <= item.start) continue;
      if (item.start > cursor) children.push(toResidual(parentId, cursor, item.start, ++counter));
      children.push(toPublic(item, parentId)); cursor = item.end;
    }
    if (cursor < end) children.push(toResidual(parentId, cursor, end, ++counter));
    return children;
  }
  function toResidual(parentId, start, end, index) {
    const a = bytePoints.has(start) ? bytePoints.get(start) : Buffer.byteLength(source.slice(0, start),'utf8');
    const b = bytePoints.has(end) ? bytePoints.get(end) : Buffer.byteLength(source.slice(0, end),'utf8');
    return { id: `${parentId}::residual:${index}@${a}`, name: 'Other code / declarations',
      kind: 'code', relative_path: relativePath, size_bytes: b - a,
      line_count: location(Math.max(start,end-1)) - location(start) + 1,
      line_start: location(start), line_end: location(Math.max(start,end-1)), metadata: {}, children: [] };
  }
  function toPublic(item, parentId) {
    const left = bytePoints.get(item.start), right = bytePoints.get(item.end);
    const id = `${parentId}::${item.kind}:${item.name}@${left}`;
    return { id, name: item.name, kind: item.kind, relative_path: relativePath,
      size_bytes: right - left,
      line_count: location(item.end - 1) - location(item.start) + 1,
      line_start: location(item.start), line_end: location(item.end - 1),
      metadata: item.metadata, children: resolveChildren(id, item.start, item.end, item.children) };
  }
  const file = { id: relativePath, name: path.posix.basename(relativePath), kind: 'file', relative_path: relativePath,
    size_bytes: fullBytes, line_count: source ? source.split('\n').length : 0,
    line_start: source ? 1 : null, line_end: source ? location(source.length) : null,
    metadata: { module_format: /@odoo-module/.test(source.slice(0, 500)) ? 'odoo-module' : 'javascript' },
    children: resolveChildren(relativePath, 0, source.length, symbols) };
  function countKind(kind) { let total = 0; function visit(n){ if(n.kind === kind) total++; n.children.forEach(visit); } visit(file); return total; }
  return { file, symbol_count: nodeCount, component_count: (() => { let count=0;
    function walk(n){ if(n.metadata.is_owl_component) count++; n.children.forEach(walk); } walk(file); return count; })(),
    service_count: countKind('service'), registration_count: registrations.length,
    imports, registrations, parse_error: null };
}

function main() {
  try {
    const ts = loadTypeScript();
    const source = fs.readFileSync(0, 'utf8');
    const relativePath = process.argv[2] || 'source.js';
    process.stdout.write(JSON.stringify(inspect(ts, relativePath, source)));
  } catch (e) {
    process.stderr.write((e instanceof Error ? e.message : String(e)).slice(0, 500));
    process.exitCode = 2;
  }
}
main();
