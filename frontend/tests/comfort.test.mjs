import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import vm from 'node:vm'

test('recipe preferences render actual values and escape personal notes as text', async () => {
  const { descriptor } = parse(readFileSync(new URL('../src/ComfortPanel.vue', import.meta.url), 'utf8'))
  const script = compileScript(descriptor, { id: 'comfort-test', inlineTemplate: true })
  const realApi = 'data:text/javascript;base64,' + Buffer.from(ts.transpileModule(readFileSync(new URL('../src/api.ts', import.meta.url), 'utf8'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText).toString('base64')
  const stub = 'data:text/javascript;base64,' + Buffer.from(`export async function api(){return {items:[]}}; export { photoUrl } from ${JSON.stringify(realApi)}`).toString('base64')
  const code = ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
    .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
    .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(stub))
  const { default: component } = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'))
  const html = await renderToString(createSSRApp(component, { section: 'preferences', data: { week: { start: '2026-11-09', meals: [] } }, recipe: { id: 1, name: 'Soupe témoin', favorite: 1, to_try: 1, rating: 'a_refaire', category: 'legumes', comment: '<script>exemple fictif</script>', variant: 'Avec du thym' } }))
  assert.match(html, /Soupe témoin/); assert.match(html, /Avec du thym/)
  assert.match(html, /&lt;script&gt;exemple fictif&lt;\/script&gt;/); assert.doesNotMatch(html, /<script>/)
  assert.equal((html.match(/type="checkbox" checked/g) || []).length, 2)
  // This SFC uses the client render compiler; select v-model is applied on mount.
  assert.match(html, /value="a_refaire">À refaire/)
})

test('the service worker precaches built assets and leaves all API requests outside its cache', async () => {
  const listeners = {}, cached = [], network = []
  const cache = { async addAll(urls) { cached.push(...urls) }, async put(url) { cached.push(url) } }
  const context = vm.createContext({ URL, Response, Error, self: { location: { origin: 'https://mijote.example' }, addEventListener(name, callback) { listeners[name] = callback } }, caches: { async open() { return cache } }, async fetch(url) { network.push(url); return new Response('<script src="/assets/app.js"></script><link href="/assets/app.css" rel="stylesheet">') } })
  vm.runInContext(readFileSync(new URL('../public/sw.js', import.meta.url), 'utf8'), context)
  let installed; listeners.install({ waitUntil(promise) { installed = promise } }); await installed
  assert.ok(cached.includes('/marmite.svg')); assert.ok(cached.includes('/assets/app.js')); assert.ok(cached.includes('/assets/app.css')); assert.ok(cached.includes('/'))
  let intercepted = false
  listeners.fetch({ request: { method: 'GET', url: 'https://mijote.example/api/v1/weeks/current/shopping' }, respondWith() { intercepted = true } })
  assert.equal(intercepted, false); assert.equal(network.length, 1)
  for (const method of ['GET', 'POST']) {
    listeners.fetch({ request: { method, url: 'https://mijote.example/share-recipe' }, respondWith() { intercepted = true } })
    assert.equal(intercepted, false)
  }
})
