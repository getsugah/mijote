import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { effectScope } from 'vue'

const moduleUrl = code => 'data:text/javascript;base64,' + Buffer.from(code).toString('base64')
const realApi = moduleUrl(ts.transpileModule(readFileSync(new URL('../src/api.ts', import.meta.url), 'utf8'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText)
const stub = moduleUrl(`export async function api(...args) { return globalThis.webIdeaTestApi(...args) }; export { photoUrl } from ${JSON.stringify(realApi)}`)
const { descriptor } = parse(readFileSync(new URL('../src/ComfortPanel.vue', import.meta.url), 'utf8'))
const script = compileScript(descriptor, { id: 'web-ideas-unit' })
const code = ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
  .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(stub))
const { default: component } = await import(moduleUrl(code))
const idea = { name: 'Plat fictif', url: 'https://cuisine.journaldesfemmes.fr/recette/1000001-plat-temoin', source: 'Source de test' }
const flush = () => new Promise(resolve => setImmediate(resolve))

async function setup(api) {
  globalThis.webIdeaTestApi = api
  const events = [], scope = effectScope()
  const state = scope.run(() => component.setup({ section: 'ideas', data: { week: { start: '2026-11-09', meals: [] }, settings: { portions: 4 } } }, { expose() {}, emit(...event) { events.push(event) } }))
  await flush()
  return { state, events, stop() { scope.stop(); delete globalThis.webIdeaTestApi } }
}

test('web discovery is opt-in; exclusions avoid repeats; importing only opens existing preview', async () => {
  const calls = []
  const ctx = await setup(async (path, method, body) => {
    calls.push({ path, method, body })
    return path === '/suggestions/web' ? { item: idea, message: '' } : { items: [] }
  })
  try {
    assert.equal(calls.filter(c => c.path === '/suggestions/web').length, 0)
    await ctx.state.discoverWeb()
    assert.equal(ctx.state.webIdea.value.url, idea.url)
    assert.deepEqual(calls.at(-1).body, { exclude: [], source_id: 0 })
    ctx.state.importWeb()
    assert.deepEqual(ctx.events, [['importWeb', idea.url]])
    assert.equal(calls.filter(c => c.path.includes('confirm')).length, 0)
    await ctx.state.discoverWeb()
    assert.deepEqual(calls.at(-1).body, { exclude: [idea.url], source_id: 0 })
    await ctx.state.discoverWeb(true)
    assert.deepEqual(calls.at(-1).body, { exclude: [], source_id: 0 })
  } finally { ctx.stop() }
})

test('exhaustion stays explicit and source errors leave local suggestions usable', async () => {
  let failure = false
  const ctx = await setup(async path => {
    if (path !== '/suggestions/web') return { items: [{ recipe_id: 7, name: 'Recette locale' }] }
    if (failure) throw new Error('Source indisponible')
    return { item: null, message: 'Toutes les idées ont été vues.' }
  })
  try {
    await ctx.state.discoverWeb()
    assert.equal(ctx.state.webIdea.value, null)
    assert.match(ctx.state.webMessage.value, /vues/)
    failure = true
    await ctx.state.discoverWeb(true)
    assert.match(ctx.state.error.value, /Source indisponible/)
    assert.equal(ctx.state.busy.value, false)
    assert.equal(ctx.state.webBusy.value, false)
    await ctx.state.suggestions()
    assert.equal(ctx.state.ideas.value[0].recipe_id, 7)
  } finally { ctx.stop() }
})

test('unauthorized discoveries request login and never emit an import', async () => {
  const ctx = await setup(async path => {
    if (path === '/suggestions/web') throw Object.assign(new Error('Connexion nécessaire'), { status: 401 })
    return { items: [] }
  })
  try {
    await ctx.state.discoverWeb()
    ctx.state.importWeb()
    assert.deepEqual(ctx.events, [['unauthorized']])
  } finally { ctx.stop() }
})

test('adding a verified link selects it, clears seen ideas and sends its identifier', async () => {
  const source = { id: 3, name: 'recettes.example', url: 'https://recettes.example/idees', count: 2 }
  const calls = []
  const ctx = await setup(async (path, method, body) => {
    calls.push({ path, method, body })
    if (path === '/suggestions/web/sources' && method === 'POST') return source
    if (path === '/suggestions/web') return { item: idea, message: '' }
    return { items: [] }
  })
  try {
    ctx.state.webSourceUrl.value = source.url
    ctx.state.webSeen.value = [idea.url]
    await ctx.state.addWebSource()
    assert.equal(ctx.state.webSourceId.value, 3)
    assert.equal(ctx.state.webSources.value[0].url, source.url)
    assert.deepEqual(ctx.state.webSeen.value, [])
    assert.equal(ctx.state.webSourceUrl.value, '')
    await ctx.state.discoverWeb()
    assert.deepEqual(calls.at(-1).body, { exclude: [], source_id: 3 })
  } finally { ctx.stop() }
})

test('link verification failures preserve input and removal requires confirmation', async () => {
  const source = { id: 3, name: 'recettes.example', url: 'https://recettes.example/idees' }
  const calls = []
  const ctx = await setup(async (path, method) => {
    calls.push({ path, method })
    if (method === 'POST') throw new Error('Aucune recette reconnue')
    return { items: [] }
  })
  const oldWindow = globalThis.window
  try {
    ctx.state.webSourceUrl.value = source.url
    await ctx.state.addWebSource()
    assert.match(ctx.state.error.value, /Aucune recette/)
    assert.equal(ctx.state.webSourceUrl.value, source.url)
    ctx.state.webSources.value = [source]
    ctx.state.webSourceId.value = source.id
    globalThis.window = { confirm() { return false } }
    await ctx.state.removeWebSource(source)
    assert.equal(calls.filter(c => c.method === 'DELETE').length, 0)
    globalThis.window.confirm = () => true
    await ctx.state.removeWebSource(source)
    assert.equal(calls.at(-1).path, '/suggestions/web/sources/3')
    assert.deepEqual(ctx.state.webSources.value, [])
    assert.equal(ctx.state.webSourceId.value, 0)
    assert.match(ctx.state.notice.value, /recettes sont conservées/)
  } finally { globalThis.window = oldWindow; ctx.stop() }
})
