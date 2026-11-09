import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { compileTemplate, compileScript, parse } from '@vue/compiler-sfc'
import ts from 'typescript'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

// Render the real application dialog without a browser or interactive automation.
const source = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const start = source.indexOf('<dialog ref="dialog"')
const dialog = source.slice(start, source.indexOf('</dialog>', start) + '</dialog>'.length)
const template = compileTemplate({ source: dialog, filename: 'App.vue', id: 'meal-preparation-test' })
assert.deepEqual(template.errors, [])
const code = template.code.replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
const { render } = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'))
const moduleUrl = code => 'data:text/javascript;base64,' + Buffer.from(code).toString('base64')
const transpile = code => ts.transpileModule(code, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
const apiModule = moduleUrl(transpile(readFileSync(new URL('../src/api.ts', import.meta.url), 'utf8')))
const mealModule = moduleUrl(transpile(readFileSync(new URL('../src/mealItems.ts', import.meta.url), 'utf8')))
const { descriptor: editorDescriptor } = parse(readFileSync(new URL('../src/MealDishesEditor.vue', import.meta.url), 'utf8'))
const editorScript = compileScript(editorDescriptor, { id: 'meal-editor', inlineTemplate: true })
const editorCode = transpile(editorScript.content)
  .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
  .replace(/from ["']\.\/api["']/g, 'from ' + JSON.stringify(apiModule))
  .replace(/from ["']\.\/mealItems["']/g, 'from ' + JSON.stringify(mealModule))
const { default: MealDishesEditor } = await import(moduleUrl(editorCode))
const { mealPayload, chooseDish, hasMealFood } = await import(mealModule)
async function html(modal, prepared = 0, extraDraft = {}) {
  return renderToString(createSSRApp({
    components: { Icon: { render: () => null }, MealDishesEditor }, render,
    setup() { return {
      modal, draft: { id: 7, day: '2026-11-09', slot: 'soir', prepared, status: 'maison', title: 'Plat fictif', recipe_id: null, side_id: null, side_choice: '', side_ingredient: null, dishes: [], portions: 4, ...extraDraft },
      modalTitle: 'Repas de test', busy: false, online: true, error: '', data: { recipes: [], ingredients: [{ id: 7, name: 'Tomates', dimension: 'masse' }, { id: 8, name: 'Tomate', dimension: 'masse' }] },
      statuses: [{ id: 'maison', label: 'À la maison' }], dateLabel: () => '9 novembre',
      close() {}, save() {}, openUnpreparation() {}, openPreparation() {}, changeSide() {}, hasMealFood: meal => !!(meal.recipe_id || meal.title || meal.side_id || meal.side_ingredient || meal.dishes?.length), previewIngredientMerge() {}, ingredient: () => ({ dimension: 'masse' }), units: () => ['g', 'kg'], unitLabel: value => value,
    } },
  }))
}

test('a prepared meal exposes a separate cancellation action and keeps its fields locked', async () => {
  const content = await html('meal', 1)
  assert.match(content, /Annuler « Repas préparé »/)
  assert.match(content, /<fieldset disabled/)
  assert.doesNotMatch(content, /Ce repas est préparé<\/button>/)
  assert.doesNotMatch(content, />Enregistrer<\/button>/)
})

test('a pending meal offers preparation and no cancellation', async () => {
  const content = await html('meal')
  assert.match(content, /Ce repas est préparé<\/button>/)
  assert.doesNotMatch(content, /Annuler « Repas préparé »/)
})

test('cancellation explains stock restoration and requires explicit confirmation', async () => {
  const content = await html('unprepare')
  assert.match(content, /quantités réellement retirées/)
  assert.match(content, /remises dans leurs lots d’origine/)
  assert.match(content, /Confirmer l’annulation/)
  assert.match(content, />Annuler<\/button>/)
})


test('ingredient merge requires a preview before the final confirmation is enabled', async () => {
  const pending = await html('merge', 0, { target_id: 8, preview: null })
  assert.match(pending, /Vérifier la fusion/)
  assert.match(pending, /disabled>Confirmer la fusion/)
  const ready = await html('merge', 0, { target_id: 8, preview: { source: { name: 'Tomates' }, target: { name: 'Tomate' }, counts: { recipe_ingredients: 2, stock: 1, movements: 3 } } })
  assert.match(ready, /quantités seront additionnées/)
  assert.match(ready, /Les lots, leurs dates et le journal seront conservés/)
  assert.doesNotMatch(ready, /disabled>Confirmer la fusion/)
})


test('the meal dialog offers ingredient accompaniments and an add button with all existing dishes', async () => {
  const content = await html('meal', 0, { side_choice: 'ingredient:7', side_ingredient: { ingredient_id: 7, quantity: 200, unit: 'g' }, dishes: [
    { recipe_id: null, ingredient_id: null, title: 'Entrée fictive', quantity: null, unit: null },
    { recipe_id: null, ingredient_id: 7, title: '', quantity: 100, unit: 'g' },
  ] })
  assert.match(content, /optgroup label="Ingrédients"/)
  assert.match(content, /Quantité totale pour ce repas/)
  assert.match(content, /Ajouter un plat ou un ingrédient/)
  assert.match(content, /Entrée fictive/)
  assert.match(content, /Type de plat/)
  assert.match(content, /value="dessert"/)
  assert.equal((content.match(/Retirer cet ajout/g) || []).length, 2)
})

test('meal serialization retains every dish and direct side without sending presentation fields', () => {
  const dish = chooseDish('ingredient:7', [{ id: 7, name: 'Riz fictif', dimension: 'masse' }])
  assert.equal(dish.unit, 'g')
  const data = mealPayload({ status: 'maison', title: '', portions: 4, recipe_id: null, side_id: null,
    side_ingredient: { ingredient_id: 7, quantity: 0.5, unit: 'kg' }, dishes: [
      { ...chooseDish('recipe:9', []), name: 'Nom de présentation', course: 'dessert' },
      { ...dish, quantity: 250 }, { ...chooseDish('title', []), title: 'Dessert fictif' },
    ] })
  assert.equal(data.dishes.length, 3)
  assert.equal(data.dishes[0].recipe_id, 9)
  assert.equal(data.dishes[0].course, 'dessert')
  assert.equal(data.dishes[1].quantity, 250)
  assert.equal(data.side_ingredient.quantity, 0.5)
  assert.equal(data.side_ingredient.unit, 'kg')
  assert.equal('name' in data.dishes[0], false)
  assert.equal(hasMealFood(data), true)
  assert.equal(hasMealFood({ dishes: [] }), false)
})
