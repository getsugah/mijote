import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { beforeEach, test } from 'node:test'
import 'fake-indexeddb/auto'
import ts from 'typescript'

const source = readFileSync(new URL('../src/shoppingTravel.ts', import.meta.url), 'utf8')
const code = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
const { readTravel, updateTravel, saveSnapshot, queueChange, localItems, syncTravel, resolveChange } = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'))
const household = '11111111-1111-4111-8111-111111111111'
const snapshot = () => ({ household_id: household, week_start: '2026-11-09', generated_at: '2026-11-09T12:00:00Z', ingredients: [{ id: 1, name: 'Riz', dimension: 'masse' }], items: [{ key: 'auto-1', manual_id: null, ingredient_id: 1, name: 'Riz', quantity: 100, unit: 'g', checked: false, version: 'a'.repeat(64) }] })
const change = (action, input) => updateTravel(s => queueChange(s, action, input))
beforeEach(async () => { await updateTravel(() => null); await saveSnapshot(snapshot()) })

test('offline checks survive reopening the database and never alter the server snapshot', async () => {
  await change('check', { item_key: 'auto-1', checked: true })
  const state = await readTravel()
  assert.equal(state.queue.length, 1)
  assert.equal(localItems(state)[0].checked, true)
  assert.equal(state.snapshot.items[0].checked, false)
  assert.deepEqual(Object.keys(state).sort(), ['queue','schema','snapshot'])
})
test('unsent changes are consolidated and local additions can be edited or cancelled', async () => {
  await change('check', { item_key: 'auto-1', checked: true }); await change('check', { item_key: 'auto-1', checked: false })
  await change('add', { ingredient_id: 1, quantity: 2, unit: 'kg' })
  let state = await readTravel(), key = localItems(state).find(i => i.key.startsWith('local-')).key
  await change('edit', { item_key: key, quantity: 3, unit: 'kg', checked: true })
  state = await readTravel(); assert.equal(state.queue.length, 2); assert.equal(localItems(state).find(i => i.key === key).quantity, 3)
  await change('remove', { item_key: key }); assert.equal((await readTravel()).queue.length, 1)
})
test('several independent additions stay independent; concurrent tabs keep both writes', async () => {
  await Promise.all([change('add', { ingredient_id: 1, quantity: 1, unit: 'g' }), change('add', { ingredient_id: 1, quantity: 2, unit: 'g' })])
  const state = await readTravel(); assert.equal(state.queue.length, 2); assert.notEqual(state.queue[0].body.operation_id, state.queue[1].body.operation_id)
})
test('an uncertain request keeps its immutable UUID and locks that article until retry', async () => {
  await change('check', { item_key: 'auto-1', checked: true }); const id = (await readTravel()).queue[0].body.operation_id
  await assert.rejects(syncTravel(household, async () => { throw new Error('réseau coupé') }), /réseau coupé/)
  assert.equal((await readTravel()).queue[0].attempted, true)
  await assert.rejects(change('check', { item_key: 'auto-1', checked: false }), /attend une réponse/)
  const fresh = snapshot(); fresh.generated_at = '2026-11-09T13:00:00Z'; fresh.items[0].checked = true
  const state = await syncTravel(household, async (path, method, payload) => { if (method === 'POST') { assert.equal(payload.operations[0].operation_id, id); return { results: [{ operation_id: id, status: 'applied' }] } } return fresh })
  assert.equal(state.queue.length, 0); assert.equal(localItems(state)[0].checked, true)
})
test('a lost snapshot after server acknowledgement also retains the UUID for safe replay', async () => {
  await change('add', { ingredient_id: 1, quantity: 1, unit: 'g' }); const id = (await readTravel()).queue[0].body.operation_id
  await assert.rejects(syncTravel(household, async (_, method) => { if (method === 'POST') return { results: [{ operation_id: id, status: 'applied' }] }; throw new Error('snapshot indisponible') }), /snapshot indisponible/)
  assert.equal((await readTravel()).queue[0].body.operation_id, id)
})
test('conflicts retain the local request and reapply explicitly against the new version', async () => {
  await change('check', { item_key: 'auto-1', checked: true }); const id = (await readTravel()).queue[0].body.operation_id
  const fresh = snapshot(); fresh.generated_at = '2026-11-09T13:00:00Z'; fresh.items[0].version = 'b'.repeat(64)
  await syncTravel(household, async (_, method) => method === 'POST' ? { results: [{ operation_id: id, status: 'conflict', message: 'modifié ailleurs' }] } : fresh)
  let state = await readTravel(); assert.equal(state.queue[0].message, 'modifié ailleurs')
  state = await updateTravel(s => resolveChange(s, id, true)); assert.notEqual(state.queue[0].body.operation_id, id); assert.equal(state.queue[0].body.expected_version, 'b'.repeat(64)); assert.equal(state.queue[0].attempted, false)
})
test('a missing item conflict can be discarded but cannot silently recreate a calculated need', async () => {
  await change('check', { item_key: 'auto-1', checked: true }); const id = (await readTravel()).queue[0].body.operation_id
  await syncTravel(household, async (_, method) => method === 'POST' ? { results: [{ operation_id: id, status: 'conflict', message: 'disparu' }] } : { ...snapshot(), generated_at: '2026-11-09T13:00:00Z', items: [] })
  await assert.rejects(updateTravel(s => resolveChange(s, id, true)), /n’existe plus/)
  await updateTravel(s => resolveChange(s, id, false)); assert.equal((await readTravel()).queue.length, 0)
})
test('another household cannot receive queued changes and a week switch preserves pending work', async () => {
  await change('check', { item_key: 'auto-1', checked: true }); let calls = 0
  await assert.rejects(syncTravel('another-house', async () => { calls++ }), /autre maison/); assert.equal(calls, 0)
  await assert.rejects(saveSnapshot({ ...snapshot(), week_start: '2026-11-16' }), /en attente/)
  assert.equal((await readTravel()).snapshot.week_start, '2026-11-09')
})
test('older snapshots cannot replace a newer list and calculated quantities cannot be edited', async () => {
  const fresh = snapshot(); fresh.generated_at = '2026-11-09T14:00:00Z'; fresh.items[0].quantity = 200
  await saveSnapshot(fresh); await saveSnapshot(snapshot()); assert.equal((await readTravel()).snapshot.items[0].quantity, 200)
  await assert.rejects(change('edit', { item_key: 'auto-1', quantity: 50, unit: 'g', checked: false }), /besoin calculé/)
})
test('a view left open in another tab cannot overwrite a newer local snapshot', async () => {
  const fresh = snapshot(); fresh.generated_at = '2026-11-09T14:00:00Z'; fresh.items[0].version = 'c'.repeat(64)
  await saveSnapshot(fresh)
  await assert.rejects(change('check', { item_key: 'auto-1', checked: true, expected_version: 'a'.repeat(64) }), /autre onglet/)
  assert.equal((await readTravel()).queue.length, 0)
})
