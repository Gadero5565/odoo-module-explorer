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
