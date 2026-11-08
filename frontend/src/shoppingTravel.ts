// Only an explicitly saved shopping list is persisted. No session or full dashboard.
export interface TravelItem { key: string; manual_id: number | null; ingredient_id: number; name: string; quantity: number; unit: string; checked: boolean; version: string }
export interface Snapshot { household_id: string; week_start: string; generated_at: string; ingredients: { id: number; name: string; dimension: string }[]; items: TravelItem[] }
export interface Queued { body: any; attempted: boolean; message?: string }
export interface TravelState { schema: 1; snapshot: Snapshot; queue: Queued[] }
export function newOperationId() {
  const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6]! & 15) | 64; bytes[8] = (bytes[8]! & 63) | 128
  const s = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''); return `${s.slice(0,8)}-${s.slice(8,12)}-${s.slice(12,16)}-${s.slice(16,20)}-${s.slice(20)}`
}
function open(): Promise<IDBDatabase> { return new Promise((resolve, reject) => { const r = indexedDB.open('mijote-shopping-v1', 1); r.onupgradeneeded = () => r.result.createObjectStore('list'); r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error) }) }
export async function updateTravel(change: (state: TravelState | null) => TravelState | null): Promise<TravelState | null> {
  const db = await open()
  return new Promise((resolve, reject) => {
    const tx = db.transaction('list', 'readwrite'), store = tx.objectStore('list'); let value: TravelState | null = null, failure: unknown
    const r = store.get('active'); r.onsuccess = () => { try { value = change(r.result || null); if (value) store.put(value, 'active'); else store.delete('active') } catch (e) { failure = e; tx.abort() } }
    tx.oncomplete = () => { db.close(); resolve(value) }; tx.onabort = tx.onerror = () => { db.close(); reject(failure || tx.error || new Error('La copie locale n’a pas pu être enregistrée.')) }
  })
}
export function readTravel() { return updateTravel(state => state) }
export function saveSnapshot(snapshot: Snapshot) { return updateTravel(state => {
  if (state?.queue.length && (state.snapshot.household_id !== snapshot.household_id || state.snapshot.week_start !== snapshot.week_start)) throw new Error('Envoyer ou résoudre la liste en attente avant de changer de semaine ou de maison.')
  if (state && state.snapshot.household_id === snapshot.household_id && state.snapshot.week_start === snapshot.week_start && state.snapshot.generated_at > snapshot.generated_at) return state
  return { schema: 1, snapshot, queue: state?.queue || [] }
}) }
export function localItems(state: TravelState): TravelItem[] {
  const items = structuredClone(state.snapshot.items)
  for (const { body: b } of state.queue) {
    if (b.action === 'add') { const i = state.snapshot.ingredients.find(i => i.id === b.ingredient_id); items.push({ key: 'local-' + b.operation_id, manual_id: -1, ingredient_id: b.ingredient_id, name: i?.name || 'Ingrédient retiré', quantity: b.quantity, unit: b.unit, checked: b.checked, version: '' }); continue }
    const i = items.findIndex(i => i.key === b.item_key); if (i < 0) continue
    if (b.action === 'remove') items.splice(i, 1)
    else { items[i]!.checked = b.checked; if (b.action === 'edit') { items[i]!.quantity = b.quantity; items[i]!.unit = b.unit } }
  }
  return items
}
export function queueChange(state: TravelState, action: 'check' | 'add' | 'edit' | 'remove', input: any): TravelState {
  const key = input.item_key
  const existing = key ? state.queue.find(q => q.body.item_key === key || 'local-' + q.body.operation_id === key) : undefined
  if (existing?.attempted) throw new Error('Cet article attend une réponse du serveur. Synchroniser ou résoudre le conflit avant de le modifier.')
  if (existing?.body.action === 'add') {
    if (action === 'remove') state.queue.splice(state.queue.indexOf(existing), 1)
    else Object.assign(existing.body, { checked: input.checked }, action === 'edit' ? { quantity: input.quantity, unit: input.unit } : {})
    return state
  }
  const item = state.snapshot.items.find(i => i.key === key)
  if (action !== 'add' && !item) throw new Error('Cet article n’est plus dans la copie locale.')
  if (item && input.expected_version !== undefined && item.version !== input.expected_version) throw new Error('La copie a changé dans un autre onglet. Vérifier la liste actualisée avant de modifier cet article.')
  if ((action === 'edit' || action === 'remove') && !item?.manual_id) throw new Error('Modifier le repas pour changer un besoin calculé.')
  if (existing) {
    if (action === 'check' && existing.body.action === 'edit') { existing.body.checked = input.checked; return state }
    state.queue.splice(state.queue.indexOf(existing), 1)
  }
  const body = { action, operation_id: newOperationId(), week_start: state.snapshot.week_start,
    ...(action === 'add' ? { ingredient_id: input.ingredient_id, quantity: input.quantity, unit: input.unit, checked: false } : { item_key: key, expected_version: item!.version, ...(action !== 'remove' ? { checked: input.checked } : {}), ...(action === 'edit' ? { quantity: input.quantity, unit: input.unit } : {}) }) }
  state.queue.push({ body, attempted: false }); return state
}
export async function syncTravel(household: string, request: (path: string, method?: string, body?: unknown) => Promise<any>) {
  let batch: Queued[] = []
  const current = await updateTravel(state => {
    if (!state) return null
    if (state.snapshot.household_id !== household) throw new Error('Cette liste appartient à une autre maison. Aucun changement envoyé.')
    batch = state.queue.filter(q => !q.message).slice(0, 50); batch.forEach(q => q.attempted = true); return state
  })
  if (!current) return null
  const response = batch.length ? await request('/shopping/sync', 'POST', { household_id: household, operations: batch.map(q => q.body) }) : { results: [] }
  // Keep all UUIDs on failure to fetch the new snapshot: a retry is safe on the server.
  const snapshot: Snapshot = await request(`/weeks/${current.snapshot.week_start}/shopping/offline`)
  return updateTravel(state => {
    if (!state || state.snapshot.household_id !== household || state.snapshot.week_start !== current.snapshot.week_start) return state
    const results = new Map<string, any>(response.results.map((r: any) => [r.operation_id, r]))
    state.queue = state.queue.filter(q => results.get(q.body.operation_id)?.status !== 'applied')
    state.queue.forEach(q => { const r = results.get(q.body.operation_id); if (r) q.message = r.message || 'À vérifier avant de renvoyer.' })
    if (snapshot.generated_at >= state.snapshot.generated_at) state.snapshot = snapshot
    return state
  })
}
export function resolveChange(state: TravelState, id: string, reapply: boolean, reviewedVersion?: string): TravelState {
  const q = state.queue.find(q => q.body.operation_id === id)
  if (!q?.message) throw new Error('Attendre une réponse du serveur avant de retirer une opération envoyée.')
  const b = q.body
  if (reapply) {
    if (b.action === 'add') throw new Error('Retirer puis corriger cet ajout avant de le renvoyer.')
    const item = state.snapshot.items.find(i => i.key === b.item_key)
    if (!item) throw new Error('L’article n’existe plus sur le serveur. Conserver la version actuelle.')
    if (reviewedVersion !== undefined && item.version !== reviewedVersion) throw new Error('La version a changé dans un autre onglet. Vérifier la liste actualisée avant de réappliquer.')
    q.body = { ...b, operation_id: newOperationId(), expected_version: item.version }; q.attempted = false; delete q.message
  } else state.queue.splice(state.queue.indexOf(q), 1)
  return state
}
