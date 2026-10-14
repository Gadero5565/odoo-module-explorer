const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/lib/insights.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
});
const mod = { exports: {} };
new Function('module', 'exports', compiled.outputText)(mod, mod.exports);
const { searchSymbols, rankSymbols, relatedTo } = mod.exports;

const symbols = [
  { id: '1', name: 'action_publish', kind: 'method', relative_path: 'models/a.py',
    owner_model: 'demo.a', size_bytes: 90, line_count: 8, complexity: 4 },
  { id: '2', name: 'day_ids', kind: 'odoo_field', relative_path: 'models/a.py',
    owner_model: 'demo.a', size_bytes: 40, line_count: 2, complexity: null },
  { id: '3', name: 'CalendarComponent', kind: 'class', relative_path: 'static/calendar.js',
    owner_model: null, size_bytes: 190, line_count: 12, complexity: null },
];

test('Global search filters by name, file path, type and owner model', () => {
  assert.deepEqual(searchSymbols(symbols, 'publish', 'all').map(s => s.id), ['1']);
  assert.deepEqual(searchSymbols(symbols, 'STATIC/', 'all').map(s => s.id), ['3']);
  assert.deepEqual(searchSymbols(symbols, '', 'odoo_field', 'demo.a').map(s => s.id), ['2']);
  assert.deepEqual(searchSymbols(symbols, 'missing', 'all'), []);
});

test('Rankings do not mutate the index and treat missing complexity as zero', () => {
  assert.deepEqual(rankSymbols(symbols, 'size_bytes').map(s => s.id), ['3', '1', '2']);
  assert.equal(rankSymbols(symbols, 'complexity')[0].id, '1');
  assert.equal(symbols[0].id, '1');
});

test('Both incoming and outgoing model edges can be inspected', () => {
  const edges = [{ source: 'demo.a', target: 'demo.b' }, { source: 'demo.c', target: 'demo.a' },
    { source: 'elsewhere', target: 'demo.b' }];
  assert.equal(relatedTo('demo.a', edges).length, 2);
  assert.equal(relatedTo('demo.c', edges).length, 1);
  assert.equal(relatedTo('missing', edges).length, 0);
});
