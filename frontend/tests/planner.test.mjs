import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

// Render real components with fictional data; no browser or household connection.
const uri = code => 'data:text/javascript;base64,' + Buffer.from(code).toString('base64')
const cache = new Map()
async function moduleUrl(file) {
  if (cache.has(file)) return cache.get(file)
  let source = readFileSync(new URL('../src/' + file, import.meta.url), 'utf8')
  if (file.endsWith('.vue')) {
    const { descriptor } = parse(source)
    source = compileScript(descriptor, { id: file.replace(/\W/g, ''), inlineTemplate: true, templateOptions: { ssr: true } }).content
  }
  let code = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
  for (const specifier of new Set([...code.matchAll(/from ["']([^"']+)["']/g)].map(m => m[1]))) {
    const resolved = specifier.startsWith('./') ? await moduleUrl(specifier.slice(2) + (specifier.endsWith('.vue') ? '' : '.ts')) : import.meta.resolve(specifier)
    code = code.replaceAll(`from '${specifier}'`, `from ${JSON.stringify(resolved)}`).replaceAll(`from "${specifier}"`, `from ${JSON.stringify(resolved)}`)
  }
  const result = uri(code); cache.set(file, result); return result
}
const { default: Planner } = await import(await moduleUrl('WeekPlanner.vue'))
const { primaryMealRecipe, photographedMealRecipe } = await import(await moduleUrl('mealPresentation.ts'))
const dates = Array.from({ length: 7 }, (_, i) => `2026-11-${String(9 + i).padStart(2, '0')}`)
const recipes = [
  { id: 1, name: 'Plat fictif', photo_version: 'photo-plat', favorite: 1 },
  { id: 2, name: 'Entrée fictive', photo_version: 'photo-entree' },
  { id: 3, name: 'Accompagnement fictif', photo_version: 'photo-side' },
]
function meals() { return dates.flatMap((day, d) => ['midi', 'soir'].map((slot, s) => ({ id: d * 2 + s + 1, day, slot, status: 'maison', title: '', recipe_id: null, recipe_name: null, side_id: null, side_name: null, portions: 4, dishes: [], prepared: 0 }))) }
async function render(values, extra = {}) {
  return renderToString(createSSRApp(Planner, { dates, meals: values, recipes, selectedId: 1, busy: false, online: true, ...extra }))
}

test('planning renders fourteen real slots, holidays, all courses and a selected detail without changing data', async () => {
  const values = meals()
  Object.assign(values[0], { recipe_id: 1, recipe_name: 'Plat fictif', side_id: 3, side_name: 'Riz fictif · 200 g',
    dishes: [{ recipe_id: 2, course: 'entree', name: 'Entrée fictive' }, { course: 'dessert', title: 'Dessert fictif' }] })
  const original = JSON.stringify(values)
  const content = await render(values)
  assert.equal((content.match(/<button class="[^"]*\bmenu-meal\b/g) || []).length, 14)
  assert.equal((content.match(/<article class="[^"]*\bmenu-day\b/g) || []).length, 7)
  assert.match(content, /Armistice 1918/)
  for (const text of ['Entrée fictive', 'Plat fictif', 'Dessert fictif', 'Riz fictif · 200 g']) assert.ok(content.includes(text))
  assert.match(content, /\/api\/v1\/recipes\/1\/photo\?v=photo-plat/)
  assert.match(content, /Repas sélectionné/)
  assert.match(content, /Retirer des favoris/)
  assert.equal(JSON.stringify(values), original)
})

test('away slots keep saved meals untouched and hide their recipes and photos from planning', async () => {
  const values = meals()
  Object.assign(values[0], { status: 'travail', title: 'Titre conservé hors menu', recipe_id: 1, recipe_name: 'Plat conservé hors menu', side_name: 'Accompagnement caché', dishes: [{ title: 'Dessert caché', course: 'dessert' }] })
  const original = JSON.stringify(values)
  const content = await render(values)
  assert.match(content, /Au travail/)
  assert.doesNotMatch(content, /Titre conservé hors menu|Plat conservé hors menu|Accompagnement caché|Dessert caché|\/recipes\/1\/photo/)
  assert.equal(JSON.stringify(values), original)
})

test('prepared and offline meals expose no second preparation or enabled editing action', async () => {
  const values = meals()
  Object.assign(values[0], { title: 'Soupe fictive', prepared: 1 })
  const content = await render(values)
  assert.match(content, /menu-prepared/)
  assert.match(content, /Voir le repas \/ annuler la préparation/)
  assert.doesNotMatch(content, />Repas préparé<\/button>/)
  const offline = await render(values, { online: false })
  assert.match(offline, /disabled[^>]*>[^<]*<svg[\s\S]*?Voir le repas/)
})

test('selection follows the displayed week and photos fall back from main to another saved course', async () => {
  const values = meals()
  const content = await render(values, { selectedId: 999 })
  assert.match(content, /lundi 9 novembre/)
  assert.equal(primaryMealRecipe({ ...values[0], recipe_id: 1, side_id: 3 }, recipes).id, 1)
  const withoutPhoto = recipes.map(r => r.id === 1 ? { ...r, photo_version: null } : r)
  const meal = { ...values[0], recipe_id: 1, dishes: [{ recipe_id: 2, course: 'entree' }], side_id: 3 }
  assert.equal(photographedMealRecipe(meal, withoutPhoto).id, 2)
  assert.equal(photographedMealRecipe({ ...meal, status: 'exterieur' }, recipes), undefined)
})
