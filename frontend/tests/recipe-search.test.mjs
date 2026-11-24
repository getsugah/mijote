import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { effectScope, reactive, nextTick, createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const uri = text => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64')
const api = uri('export async function api(...args) { return globalThis.recipeSearchTestApi(...args) }')
const { descriptor } = parse(readFileSync(new URL('../src/RecipeSearch.vue', import.meta.url), 'utf8'))
function compiled(inlineTemplate) {
  return ts.transpileModule(compileScript(descriptor, { id: 'recipe-search-test', inlineTemplate }).content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
    .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
    .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(api))
}
const { default: Component } = await import(uri(compiled(false)))
const item = { id: '12345', title: 'Chicken Curry', image_url: 'https://www.themealdb.com/images/media/meals/example.jpg', category: 'Chicken', area: 'India', tags: ['Curry', 'Cuisine indienne'], source_url: '', provider_url: 'https://www.themealdb.com/meal.php?c=12345', provider: 'TheMealDB', attribution: 'TheMealDB · Chicken Curry', image_origin: '' }
const photo = { data_base64: 'fictitious', source_url: item.image_url, attribution: item.attribution }
function setup(request) {
  const calls = [], events = [], scope = effectScope()
  const props = reactive({ name: 'Poulet au curry maison', ingredients: ['Poulet', 'Crème'], tags: [], photo: null, disabled: false })
  globalThis.recipeSearchTestApi = (...args) => { calls.push(args); return request(...args) }
  const state = scope.run(() => Component.setup(props, { expose() {}, emit(...args) {
    events.push(args)
    if (args[0] === 'name') props.name = args[1]
    if (args[0] === 'photo') props.photo = args[1]
    if (args[0] === 'tags') props.tags = args[1]
  } }))
  return { state, props, calls, events, stop() { scope.stop(); delete globalThis.recipeSearchTestApi } }
}

test('external search is opt-in and sends only the editable query, without changing a recipe', async () => {
  const ctx = setup(async () => ({ items: [item], query_used: 'chicken curry', adapted: true, message: 'À vérifier' }))
  try {
    assert.equal(ctx.calls.length, 0)
    await ctx.state.search()
    assert.deepEqual(ctx.calls[0], ['/recipes/search/mealdb', 'POST', { query: 'Poulet au curry maison' }])
    assert.deepEqual(ctx.events, [])
    assert.equal(ctx.state.response.value.items[0].title, 'Chicken Curry')
  } finally { ctx.stop() }
})

test('the paired title and photo require preview and a separate acceptance, with no save request', async () => {
  const ctx = setup(async () => photo)
  try {
    await ctx.state.preview(item)
    assert.deepEqual(ctx.events, [])
    assert.deepEqual(ctx.calls[0], ['/recipes/search/mealdb/photo', 'POST', { meal_id: '12345' }])
    ctx.state.adopt()
    assert.deepEqual(ctx.events.map(e => e[0]), ['name', 'photo'])
    assert.equal(ctx.props.name, item.title)
    assert.equal(ctx.props.photo.attribution, item.attribution)
    assert.equal(ctx.calls.length, 1)
  } finally { ctx.stop() }
})

test('photo-only acceptance keeps the personal title and tags are chosen independently', async () => {
  const ctx = setup(async () => photo)
  try {
    await ctx.state.preview(item); ctx.state.adopt(false)
    assert.equal(ctx.props.name, 'Poulet au curry maison')
    assert.deepEqual(ctx.events.map(e => e[0]), ['photo'])
    ctx.state.chooseTag('Cuisine indienne'); ctx.state.chooseTag('CUISINE INDIENNE')
    assert.deepEqual([...ctx.props.tags], ['Cuisine indienne'])
    assert.deepEqual([...ctx.props.ingredients], ['Poulet', 'Crème'])
  } finally { ctx.stop() }
})

test('editing the query discards late results and closing discards late photo previews', async () => {
  let resolve
  const ctx = setup(() => new Promise(done => { resolve = done }))
  try {
    const pending = ctx.state.search(); ctx.state.query.value = 'Un autre plat'; await nextTick()
    resolve({ items: [item] }); await pending
    assert.equal(ctx.state.response.value, null)
    assert.deepEqual(ctx.events, [])
  } finally { ctx.stop() }
  let finish
  const closed = setup(() => new Promise(done => { finish = done }))
  const request = closed.state.preview(item); closed.stop(); finish(photo); await request
  assert.equal(closed.state.candidate.value, null)
})

test('the search renders explicit non-submitting controls and explains the external query', async () => {
  const { default: Rendered } = await import(uri(compiled(true)))
  const content = await renderToString(createSSRApp(Rendered, { name: 'Soupe fictive' }))
  assert.match(content, /Un titre et sa photo/)
  assert.match(content, /Proposer des titres avec photo/)
  assert.match(content, /seul le texte recherché/)
  assert.doesNotMatch(content, /<form|type="submit"/)
})
