import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { reactive, createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const url = text => 'data:text/javascript;base64,' + Buffer.from(text).toString('base64')
const api = url('export async function api(...args) { return globalThis.ingredientTestApi(...args) }')
const { descriptor } = parse(readFileSync(new URL('../src/IngredientSuggestions.vue', import.meta.url), 'utf8'))
const script = compileScript(descriptor, { id: 'ingredient-suggestions-test' })
const code = ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
  .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(api))
const { default: component } = await import(url(code))
async function setup(request) {
  globalThis.ingredientTestApi = request
  const props = reactive({ name: 'Tomates', dimension: 'masse' }), events = []
  let state
  await renderToString(createSSRApp({ setup(_, ctx) { state = component.setup(props, { ...ctx, emit(...args) { events.push(args) } }); return () => null } }))
  clearTimeout(state.timer)
  return { state, props, events, stop() { clearTimeout(state.timer); delete globalThis.ingredientTestApi } }
}

test('plural matching shows suggestions without silently choosing an ingredient', async () => {
  const ctx = await setup(async path => { assert.match(path, /name=Tomates&dimension=masse/); return { exact: [], suggestions: [{ id: 7, name: 'Tomate', dimension: 'masse' }] } })
  try {
    await ctx.state.check()
    assert.equal(ctx.state.exact.value, false)
    assert.equal(ctx.state.candidates.value[0].id, 7)
    assert.deepEqual(ctx.events, [])
  } finally { ctx.stop() }
})

test('an older match response cannot overwrite a newer response', async () => {
  let finish, count = 0
  const ctx = await setup(async () => {
    if (!count++) return new Promise(resolve => { finish = resolve })
    return { exact: [{ id: 8, name: 'Tomates', dimension: 'masse' }], suggestions: [] }
  })
  try {
    const old = ctx.state.check()
    await ctx.state.check()
    finish({ exact: [], suggestions: [{ id: 7, name: 'Tomate', dimension: 'masse' }] })
    await old
    assert.equal(ctx.state.exact.value, true)
    assert.equal(ctx.state.candidates.value[0].id, 8)
  } finally { ctx.stop() }
})
