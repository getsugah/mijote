import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { compileTemplate } from '@vue/compiler-sfc'
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
async function html(modal, prepared = 0) {
  return renderToString(createSSRApp({
    components: { Icon: { render: () => null } }, render,
    setup() { return {
      modal, draft: { id: 7, day: '2026-11-09', slot: 'soir', prepared, status: 'maison', title: 'Plat fictif', recipe_id: null, side_id: null, portions: 4 },
      modalTitle: 'Repas de test', busy: false, online: true, error: '', data: { recipes: [] },
      statuses: [{ id: 'maison', label: 'À la maison' }], dateLabel: () => '9 novembre',
      close() {}, save() {}, openUnpreparation() {}, openPreparation() {},
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
