import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const uri = code => 'data:text/javascript;base64,' + Buffer.from(code).toString('base64')
const options = { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext }
const api = uri(ts.transpileModule(readFileSync(new URL('../src/api.ts', import.meta.url), 'utf8'), { compilerOptions: options }).outputText)
const { descriptor } = parse(readFileSync(new URL('../src/LocationSelect.vue', import.meta.url), 'utf8'))
const script = compileScript(descriptor, { id: 'location-select-test', inlineTemplate: true, templateOptions: { ssr: true } })
const code = ts.transpileModule(script.content, { compilerOptions: options }).outputText
  .replace(/from ["']vue\/server-renderer["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue/server-renderer')))
  .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
  .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(api))
const { default: component } = await import(uri(code))

test('all locations are visible as options without typing and a current custom location is preserved', async () => {
  const html = await renderToString(createSSRApp(component, { modelValue: 'Tiroir de test', options: ['Placard', 'Congélateur'] }))
  assert.match(html, /<select/)
  assert.match(html, /<option[^>]*>Placard/)
  assert.match(html, /<option[^>]*>Congélateur/)
  assert.match(html, /value="Tiroir de test" selected/)
  assert.match(html, /Nouvel emplacement/)
  assert.match(html, /type="button"/)
  assert.doesNotMatch(html, /datalist|<form/)
})

test('location filtering offers all locations and does not require a stock destination', async () => {
  const html = await renderToString(createSSRApp(component, { modelValue: '', options: ['Placard'], all: true, disabled: true }))
  assert.match(html, /Tous les emplacements/)
  assert.match(html, /<select[^>]*disabled/)
  assert.doesNotMatch(html, /required/)
})
