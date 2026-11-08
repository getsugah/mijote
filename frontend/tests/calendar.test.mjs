import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const source = readFileSync(new URL('../src/calendar.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
const { frenchPublicHolidays, holidayName, mealPrintContent } = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'))

test('all eleven national holiday dates match the official 2026 calendar', () => {
  assert.deepEqual(Object.keys(frenchPublicHolidays(2026)).sort(), [
    '2026-01-01', '2026-04-06', '2026-05-01', '2026-05-08', '2026-05-14',
    '2026-05-25', '2026-07-14', '2026-08-15', '2026-11-01', '2026-11-11', '2026-12-25',
  ])
})
test('movable holidays change in 2027 and a leap year', () => {
  assert.equal(holidayName('2027-03-29'), 'Lundi de Pâques')
  assert.equal(holidayName('2027-05-06'), 'Ascension')
  assert.equal(holidayName('2027-05-17'), 'Lundi de Pentecôte')
  assert.equal(holidayName('2024-04-01'), 'Lundi de Pâques')
  assert.equal(holidayName('2024-05-09'), 'Ascension')
  assert.equal(holidayName('2024-05-20'), 'Lundi de Pentecôte')
})
test('cross-year weeks use the actual year of each date', () => {
  assert.equal(holidayName('2026-12-25'), 'Noël')
  assert.equal(holidayName('2027-01-01'), 'Jour de l’an')
  assert.equal(holidayName('2026-12-31'), undefined)
  assert.equal(holidayName('2026-12-26'), undefined) // regional holiday is not national
  assert.equal(holidayName('invalid'), undefined)
})
const meal = { status: 'maison', title: '', recipe_name: 'Riz aux légumes', side_name: 'Salade', portions: 4, prepared: 1 }
test('print content includes dish, optional side, portions and preparation', () => {
  assert.deepEqual(mealPrintContent(meal), { title: 'Riz aux légumes', side: 'Salade', detail: '4 portions', prepared: true })
})
test('printing an away slot hides its saved recipes without changing the meal', () => {
  const away = { ...meal, status: 'travail' }
  assert.deepEqual(mealPrintContent(away), { title: 'Au travail', side: '', detail: '', prepared: false })
  assert.equal(away.recipe_name, 'Riz aux légumes')
  assert.equal(mealPrintContent({ ...away, status: 'exterieur' }).title, 'À l’extérieur')
  assert.equal(mealPrintContent({ ...away, status: 'a_decider' }).title, 'À décider')
})
test('unplanned and free-title meals print clearly', () => {
  assert.equal(mealPrintContent().title, 'À prévoir')
  assert.equal(mealPrintContent({ ...meal, title: 'Soupe du soir', recipe_name: null, side_name: null, portions: 1 }).detail, '1 portion')
  assert.equal(mealPrintContent({ ...meal, title: '', recipe_name: null, side_name: null, prepared: 0 }).detail, '')
})

test('the printable component renders seven days and fourteen slots without controls', async () => {
  const { descriptor } = parse(readFileSync(new URL('../src/WeeklyPrint.vue', import.meta.url), 'utf8'))
  const script = compileScript(descriptor, { id: 'weekly-print-test', inlineTemplate: true })
  const calendarUrl = 'data:text/javascript;base64,' + Buffer.from(compiled).toString('base64')
  const componentCode = ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
    .replace(/from ["']vue["']/g, 'from ' + JSON.stringify(import.meta.resolve('vue')))
    .replace(/from ["']\.\/calendar["']/g, 'from ' + JSON.stringify(calendarUrl))
  const { default: component } = await import('data:text/javascript;base64,' + Buffer.from(componentCode).toString('base64'))
  const dates = Array.from({ length: 7 }, (_, i) => `2026-11-${String(9 + i).padStart(2, '0')}`)
  const html = await renderToString(createSSRApp(component, { dates, meals: [
    { ...meal, day: '2026-11-09', slot: 'midi', recipe_name: 'Soupe maison', side_name: 'Tartines', prepared: 0 },
    { ...meal, day: '2026-11-09', slot: 'soir', status: 'travail', recipe_name: 'Recette gardée hors menu' },
  ] }))
  assert.equal((html.match(/scope="col"/g) || []).length, 8)
  assert.equal((html.match(/scope="row"/g) || []).length, 2)
  assert.equal((html.match(/<td>/g) || []).length, 14)
  assert.match(html, /Soupe maison/)
  assert.match(html, /Tartines/)
  assert.match(html, /4 portions/)
  assert.match(html, /Au travail/)
  assert.match(html, /Armistice 1918/)
  assert.doesNotMatch(html, /Recette gardée hors menu|<button|<input|<select/)
})
