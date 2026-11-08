import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const source = readFileSync(new URL('../src/recipeShare.ts', import.meta.url), 'utf8')
const code = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
const { sharedRecipe, takeSharedRecipe } = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'))

test('an explicit HTTP link is preferred and preserves recipe text for fallback', () => {
  const value = sharedRecipe({ title:'Soupe témoin', text:'Pour 4 personnes', url:'https://recettes.example/soupe?q=1&lang=fr' })
  assert.equal(value.url, 'https://recettes.example/soupe?q=1&lang=fr')
  assert.equal(value.text, 'Soupe témoin\nPour 4 personnes')
})
test('Android links in text or title are recognized with surrounding prose', () => {
  assert.equal(sharedRecipe({ text:'Ma recette (https://recettes.example/soupe).' }).url, 'https://recettes.example/soupe')
  assert.equal(sharedRecipe({ title:'https://recettes.example/soupe' }).url, 'https://recettes.example/soupe')
  assert.equal(sharedRecipe({ text:'https://recettes.example/plat_(test)' }).url, 'https://recettes.example/plat_(test)')
})
test('multiple links are left for review and duplicates do not create ambiguity', () => {
  const result = sharedRecipe({ text:'https://recettes.example/a https://recettes.example/b' })
  assert.equal(result.url, ''); assert.match(result.message, /Plusieurs liens/)
  assert.equal(sharedRecipe({ title:'https://recettes.example/a', text:'https://recettes.example/a' }).url, 'https://recettes.example/a')
})
test('manual recipe text stays available and unsafe explicit URL schemes never pass', () => {
  const text = 'Pour 4 personnes\nIngrédients\n200 g de riz\nPréparation\nCuire.'
  assert.equal(sharedRecipe({ text }).text, text)
  for (const url of ['javascript:alert(1)','file:///etc/passwd','https://user:password@recettes.example/a']) assert.throws(() => sharedRecipe({ url }), /HTTP ou HTTPS/)
})
test('empty and excessive input is rejected without truncation', () => {
  for (const value of [null, [], {}, { text:3 }, { title:'x'.repeat(301) }, { text:'x'.repeat(60001) }, { text:'x'.repeat(60000), title:'Soupe' }]) assert.throws(() => sharedRecipe(value))
})
test('the inert share payload is consumed once and removed even when malformed', () => {
  let removed = false
  const element = { textContent:JSON.stringify({ text:'Recette témoin' }), remove(){removed=true} }
  const doc = { getElementById(){return removed ? null : element} }
  assert.equal(takeSharedRecipe(doc).text, 'Recette témoin'); assert.equal(removed, true); assert.equal(takeSharedRecipe(doc), null)
  removed = false; element.textContent = '{invalid'; assert.throws(() => takeSharedRecipe(doc)); assert.equal(removed,true)
})
test('the manifest receives links and text via POST and never declares shared files', () => {
  const manifest = JSON.parse(readFileSync(new URL('../public/manifest.webmanifest', import.meta.url), 'utf8'))
  assert.deepEqual(manifest.share_target, { action:'/share-recipe', method:'POST', enctype:'application/x-www-form-urlencoded', params:{title:'title',text:'text',url:'url'} })
})

async function importComponent() {
  const { descriptor } = parse(readFileSync(new URL('../src/RecipeImport.vue', import.meta.url), 'utf8'))
  const script = compileScript(descriptor, { id:'shared-import-test', inlineTemplate:true })
  const api = 'data:text/javascript;base64,' + Buffer.from('export async function api(){throw new Error("No automatic import")}; export class ApiError extends Error{}; export function baseUnit(){return "g"}; export function units(){return ["g"]}').toString('base64')
  const icon = 'data:text/javascript;base64,' + Buffer.from('export default {render(){return null}}').toString('base64')
  const output = ts.transpileModule(script.content, { compilerOptions: { target:ts.ScriptTarget.ES2022, module:ts.ModuleKind.ESNext } }).outputText
    .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
    .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(api))
    .replace(/from ["']\.\/Icon.vue["']/g, 'from ' + JSON.stringify(icon))
  return (await import('data:text/javascript;base64,' + Buffer.from(output).toString('base64'))).default
}
test('a received link prepopulates the existing import and still requires preview', async () => {
  const component = await importComponent()
  const html = await renderToString(createSSRApp(component, {ingredients:[],initial:sharedRecipe({url:'https://recettes.example/soupe'})}))
  assert.match(html, /value="https:\/\/recettes.example\/soupe"/)
  assert.match(html, /Prévisualiser/); assert.doesNotMatch(html, /Confirmer la vérification/)
})
test('a received recipe text prepopulates the manual fallback as escaped text', async () => {
  const component = await importComponent()
  const html = await renderToString(createSSRApp(component, {ingredients:[],initial:sharedRecipe({text:'Soupe témoin\n200 g de riz\n<img src=x onerror=alert(1)>'})}))
  assert.match(html, /200 g de riz/); assert.match(html, /&lt;img/); assert.doesNotMatch(html, /<img/)
  assert.match(html, /textarea/); assert.match(html, /Prévisualiser/)
})
