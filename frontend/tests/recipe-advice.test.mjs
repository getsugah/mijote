import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { effectScope, reactive, nextTick, createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const uri = text => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64')
const api = uri('export async function api(...args) { return globalThis.adviceTestApi(...args) }')
const { descriptor } = parse(readFileSync(new URL('../src/RecipeSuggestions.vue', import.meta.url), 'utf8'))
function compiled(inlineTemplate) {
  const script = compileScript(descriptor, { id: 'recipe-advice-test', inlineTemplate })
  return ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
    .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
    .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(api))
}
const { default: Component } = await import(uri(compiled(false)))
const suggestion = { title: 'Soupe aux tomates', title_reason: 'Titre à vérifier', tags: [{ name: 'Soupe', reason: 'Titre' }, { name: 'Tomates', reason: 'Ingrédient' }], message: 'Propositions à vérifier.' }
function setup(request) {
  globalThis.adviceTestApi = request
  const props = reactive({ name: 'SOUPE AUX TOMATES', ingredients: ['Tomates'], minutes: 20, sourceUrl: 'https://recettes.example/soupe', modelValue: [], photo: null, disabled: false })
  const scope = effectScope(), events = []
  const state = scope.run(() => Component.setup(props, { expose() {}, emit(...args) {
    events.push(args)
    if (args[0] === 'update:modelValue') props.modelValue = args[1]
    if (args[0] === 'name') props.name = args[1]
    if (args[0] === 'photo') props.photo = args[1]
  } }))
  return { state, props, events, stop() { scope.stop(); delete globalThis.adviceTestApi } }
}

test('advice is opt-in, and title and tags emit changes only after separate choices', async () => {
  const calls = []
  const ctx = setup(async (...args) => { calls.push(args); return suggestion })
  try {
    assert.equal(calls.length, 0)
    await ctx.state.propose()
    assert.equal(calls[0][0], '/recipes/advice')
    assert.deepEqual(ctx.events, [])
    await ctx.state.adoptTitle()
    assert.equal(ctx.props.name, 'Soupe aux tomates')
    ctx.state.addTag('Soupe')
    assert.deepEqual([...ctx.props.modelValue], ['Soupe'])
    ctx.state.addTag(' SOUPE ')
    assert.equal(ctx.props.modelValue.length, 1)
    ctx.state.removeTag('Soupe')
    assert.equal(ctx.props.modelValue.length, 0)
    assert.equal(calls.length, 1)
  } finally { ctx.stop() }
})

test('stale advice cannot replace a draft edited during the request', async () => {
  let resolve
  const ctx = setup(() => new Promise(done => { resolve = done }))
  try {
    const request = ctx.state.propose()
    ctx.props.name = 'Un autre plat'; await nextTick()
    resolve(suggestion); await request
    assert.equal(ctx.state.result.value, null)
    assert.deepEqual(ctx.events, [])
  } finally { ctx.stop() }
})

test('photo retrieval only previews, with source and attribution; choosing emits no save request', async () => {
  const calls = []
  const draft = { data_base64: 'fictitious-preview', source_url: 'https://recettes.example/photo.jpg', attribution: 'Auteur fictif' }
  const ctx = setup(async (path, ...args) => { calls.push([path, ...args]); return path.endsWith('/photo/preview') ? draft : { image_url: draft.source_url, image_author: draft.attribution } })
  try {
    await ctx.state.proposePhoto()
    assert.equal(calls.length, 2)
    assert.deepEqual(ctx.events, [])
    ctx.state.adoptPhoto()
    assert.deepEqual({ ...ctx.props.photo }, draft)
    assert.equal(calls.length, 2)
    assert.equal(ctx.state.candidate.value, null)
  } finally { ctx.stop() }
})

test('leaving the editor discards late proposals and errors preserve selected tags', async () => {
  let resolve
  const ctx = setup(() => new Promise(done => { resolve = done }))
  const request = ctx.state.propose(); ctx.stop(); resolve(suggestion); await request
  assert.deepEqual(ctx.events, [])
  const failure = setup(async () => { throw new Error('Source indisponible') })
  try {
    failure.props.modelValue = ['Maison']
    await failure.state.proposePhoto()
    assert.match(failure.state.error.value, /Source indisponible/)
    assert.deepEqual([...failure.props.modelValue], ['Maison'])
    assert.deepEqual(failure.events, [])
  } finally { failure.stop() }
})

test('the editor renders non-submitting controls and allows removing individual tags', async () => {
  const { default: Rendered } = await import(uri(compiled(true)))
  const content = await renderToString(createSSRApp(Rendered, { name: 'Soupe fictive', ingredients: [], minutes: 0, modelValue: ['Famille'], allowPhoto: false }))
  assert.match(content, /Retirer le tag Famille/)
  assert.match(content, /Proposer un titre et des tags/)
  assert.doesNotMatch(content, /<form|type="submit"|<img/)
})
