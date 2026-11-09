import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const { descriptor } = parse(readFileSync(new URL('../src/ShoppingPrint.vue', import.meta.url), 'utf8'))
const script = compileScript(descriptor, { id: 'shopping-print-test', inlineTemplate: true })
const code = ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
const { default: component } = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'))

test('the printable shopping list includes quantities and basket states without changing the list', async () => {
  const items = [
    { key: 'auto-1', name: 'Riz fictif', quantity: 500, unit: 'g', checked: false, manual_id: null, ingredient_id: 1 },
    { key: 'manual-2', name: '<script>article fictif</script>', quantity: 2, unit: 'piece', checked: true, manual_id: 2, ingredient_id: 2 },
  ]
  const before = structuredClone(items)
  const html = await renderToString(createSSRApp(component, { start: '2026-11-09', items }))
  assert.match(html, /Ma liste de courses/)
  assert.match(html, /9 novembre 2026/)
  assert.match(html, /15 novembre 2026/)
  assert.match(html, /Riz fictif/)
  assert.match(html, /500 g/)
  assert.match(html, /2 pièce\(s\)/)
  assert.match(html, /☐/); assert.match(html, /☑/)
  assert.match(html, /Ajout personnel/)
  assert.match(html, /&lt;script&gt;article fictif&lt;\/script&gt;/)
  assert.doesNotMatch(html, /<script>|<button|<input/)
  assert.deepEqual(items, before)
})

test('printing an empty shopping list shows a clear message', async () => {
  const html = await renderToString(createSSRApp(component, { start: '2026-11-09', items: [] }))
  assert.match(html, /Rien à acheter/)
  assert.doesNotMatch(html, /<table/)
})
