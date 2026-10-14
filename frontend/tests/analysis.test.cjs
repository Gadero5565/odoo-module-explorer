/**
 * Test pure UI helpers without a browser or Vite. Transpile just this module
 * with the project's TypeScript dev dependency so node:test can load it.
 */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/lib/analysis.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
});
const runtimeModule = { exports: {} };
new Function('module', 'exports', compiled.outputText)(runtimeModule, runtimeModule.exports);
const { filterTree, indexNodes, parentId, getFileBreakdown, formatBytes } = runtimeModule.exports;

function file(id, bytes, extension, lines = 3) {
  return { id, name: id.split('/').at(-1), relative_path: id, kind: 'file', extension, size_bytes: bytes,
    file_count: 1, directory_count: 0, line_count: lines, children: [] };
}
function folder(id, children) {
  return { id, name: id === '.' ? 'demo' : id.split('/').at(-1), relative_path: id === '.' ? '' : id,
    kind: 'directory', extension: null,
    size_bytes: children.reduce((s, child) => s + child.size_bytes, 0),
    file_count: children.reduce((s, child) => s + child.file_count, 0),
    directory_count: children.reduce((s, child) => s + child.directory_count + (child.kind === 'directory' ? 1 : 0), 0),
    line_count: children.reduce((s, child) => s + child.line_count, 0), children };
}
const root = folder('.', [
  folder('models', [file('models/b.py', 50, '.py'), file('models/a.py', 80, '.py')]),
  folder('data', [file('data/records.xml', 100, '.xml')]),
  file('banner.png', 200, '.png', 0),
]);

test('Source-only filtering recalculates directory totals without changing source tree', () => {
  const result = filterTree(root, { sourceOnly: true, excludeData: false });
  assert.equal(result.size_bytes, 230);
  assert.equal(result.file_count, 3);
  assert.equal(result.directory_count, 2);
  assert.equal(root.size_bytes, 430);
  assert.equal(root.file_count, 4);
});

test('Hide data/demo/i18n excludes those directories', () => {
  const result = filterTree(root, { sourceOnly: true, excludeData: true });
  assert.equal(result.size_bytes, 130);
  assert.equal(result.file_count, 2);
  assert.equal(result.children.length, 1);
});

test('Indexed paths allow parent navigation and fast file selection', () => {
  const index = indexNodes(root);
  assert.equal(parentId('models/b.py'), 'models');
  assert.equal(parentId('models'), '.');
  assert.equal(index.get('models/a.py').size_bytes, 80);
});

test('File type breakdown counts only files without double counting directories', () => {
  const breakdown = getFileBreakdown(root);
  assert.equal(breakdown.reduce((sum, row) => sum + row.bytes, 0), 430);
  assert.equal(breakdown.find(row => row.name === 'Python').count, 2);
  assert.equal(formatBytes(1024), '1.00 KB');
});

test('Python symbols have stable indexes and breadcrumb paths', () => {
  const { indexPythonSymbols, pythonSymbolPath, metricValue, nodeColor } = runtimeModule.exports;
  const method = { id: 'foo.py::method:run@3', name: 'run', kind: 'method', size_bytes: 30,
    line_count: 3, children: [] };
  const klass = { id: 'foo.py::class:Foo@1', name: 'Foo', kind: 'class', size_bytes: 80,
    line_count: 8, children: [method] };
  const file = { id: 'foo.py', name: 'foo.py', kind: 'file', size_bytes: 100,
    line_count: 10, children: [klass] };
  assert.equal(indexPythonSymbols(file).get(method.id).name, 'run');
  assert.deepEqual(pythonSymbolPath(file, method.id).map(item => item.name), ['foo.py', 'Foo', 'run']);
  assert.equal(metricValue(method, 'size_bytes'), 30);
  assert.equal(metricValue(method, 'file_count'), 0);
  assert.ok(nodeColor(klass).startsWith('#'));
});

test('XML symbols are indexed with correct ancestor breadcrumbs and metrics', () => {
  const { indexXMLSymbols, xmlSymbolPath, metricValue, nodeColor } = runtimeModule.exports;
  const xpath = { id: 'x.xml::xml:3@42', name: "//field[@name='year']", kind: 'xpath',
    tag: 'xpath', metadata: { xpath_expr: "//field[@name='year']" },
    size_bytes: 51, line_count: 4, children: [] };
  const view = { id: 'x.xml::xml:1@10', name: 'my_view', kind: 'view', tag: 'record',
    metadata: { xml_id: 'my_view' }, size_bytes: 90, line_count: 8, children: [xpath] };
  const file = { id: 'x.xml', name: 'x.xml', kind: 'file', tag: '', metadata: {},
    size_bytes: 110, line_count: 10, children: [view] };
  assert.equal(indexXMLSymbols(file).get(xpath.id).metadata.xpath_expr, "//field[@name='year']");
  assert.deepEqual(xmlSymbolPath(file, xpath.id).map(item => item.name), ['x.xml', 'my_view', "//field[@name='year']"]);
  assert.equal(metricValue(xpath, 'size_bytes'), 51);
  assert.equal(metricValue(xpath, 'file_count'), 0);
  assert.equal(nodeColor(xpath), '#e59588');
  assert.equal(nodeColor(file), '#5ac8ad');
});


test('JavaScript/OWL symbols support breadcrumb paths, colors and physical metrics', () => {
  const { indexJSSymbols, jsSymbolPath, metricValue, nodeColor } = runtimeModule.exports;
  const setup = { id: 'widget.js::class:C@1::method:setup@20', name: 'setup', kind: 'method',
    size_bytes: 75, line_count: 5, metadata: { hooks: ['useState'] }, children: [] };
  const component = { id: 'widget.js::class:C@1', name: 'C', kind: 'class', size_bytes: 240,
    line_count: 20, metadata: { is_owl_component: true, template: 'demo.C' }, children: [setup] };
  const file = { id: 'widget.js', name: 'widget.js', kind: 'file', size_bytes: 300,
    line_count: 25, metadata: {}, children: [component] };
  assert.equal(indexJSSymbols(file).get(setup.id).name, 'setup');
  assert.deepEqual(jsSymbolPath(file, setup.id).map(node => node.name), ['widget.js', 'C', 'setup']);
  assert.equal(metricValue(setup, 'size_bytes'), 75);
  assert.equal(metricValue(setup, 'file_count'), 0);
  assert.equal(nodeColor(component), '#af8bea');
  assert.equal(nodeColor({ ...component, kind: 'service' }), '#e9aa62');
});


test('Stylesheet nodes have stable index, breadcrumbs, colors and size metrics', () => {
  const { indexStyleSymbols, styleSymbolPath, metricValue, nodeColor } = runtimeModule.exports;
  const declaration = { id: 'a.scss::style:50:70', name: 'color', kind: 'declaration',
    relative_path: 'a.scss', size_bytes: 20, line_count: 1, metadata: { prelude: 'color: red' }, children: [] };
  const selector = { id: 'a.scss::style:20:80', name: '.item', kind: 'selector',
    relative_path: 'a.scss', size_bytes: 60, line_count: 3,
    metadata: { prelude: '.item', selector: '.item' }, children: [declaration] };
  const root = { id: 'a.scss', name: 'a.scss', kind: 'file', relative_path: 'a.scss',
    size_bytes: 100, line_count: 5, metadata: { prelude: null }, children: [selector] };
  assert.equal(indexStyleSymbols(root).get(declaration.id).name, 'color');
  assert.deepEqual(styleSymbolPath(root, declaration.id).map(node => node.name), ['a.scss', '.item', 'color']);
  assert.equal(metricValue(selector, 'size_bytes'), 60);
  assert.equal(metricValue(selector, 'file_count'), 0);
  assert.equal(nodeColor(selector), '#e7a64f');
  assert.equal(nodeColor({ ...selector, kind: 'variable' }), '#ce88da');
  assert.equal(nodeColor(root), '#e3a85d');
});

test('Refresh navigation retains existing nodes and falls back after deletion', () => {
  const { nearestExistingId } = runtimeModule.exports;
  const index = indexNodes(root);
  assert.equal(nearestExistingId('models/a.py', index), 'models/a.py');
  assert.equal(nearestExistingId('models/deleted.py', index), 'models');
  assert.equal(nearestExistingId('gone/nested/missing.py', index), '.');
});
