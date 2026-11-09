export type Status = 'maison' | 'travail' | 'exterieur' | 'a_decider'
export type Unit = 'g' | 'kg' | 'ml' | 'l' | 'piece'
export interface Ingredient { id: number; name: string; dimension: 'masse' | 'volume' | 'piece' }
export interface Line { ingredient_id: number; quantity: number; unit: Unit; name?: string }
export interface Recipe { photo_version?: string | null; photo_source?: string | null; photo_attribution?: string | null; favorite?: number; to_try?: number; rating?: string; category?: string; comment?: string; variant?: string; id: number; name: string; kind: 'simple' | 'improvise' | 'recette'; portions: number; steps: string; minutes: number; source_url: string; source_author: string; ingredient_notes: string; ingredients: Line[] }
export interface Meal { id: number; day: string; slot: 'midi' | 'soir'; status: Status; title: string; recipe_id: number | null; side_id: number | null; portions: number; prepared: number; preparation_id?: string | null; recipe_name: string | null; side_name: string | null }
export interface Stock { id: number; ingredient_id: number; name: string; location: string; quantity: number; unit: Unit; expires: string | null }
export interface Shopping { key: string; manual_id: number | null; ingredient_id: number; name: string; quantity: number; unit: Unit; checked: boolean }
export interface Presence { day: number; slot: 'midi' | 'soir'; status: Status }
export interface Settings { portions: number; presence: Presence[] }
export interface Need { ingredient_id: number; name: string; unit: Unit; required: number; reserved: number; missing: number }
export interface Dashboard {
  week: { start: string; meals: Meal[] }; settings: Settings; recipes: Recipe[]; ingredients: Ingredient[]; stock: Stock[];
  shopping: { items: Shopping[]; needs: { items: Need[]; meals: { meal_id: number; ingredients: { ingredient_id: number; required: number }[] }[] } };
  movements: { id: number; name: string; delta: number; unit: Unit; reason: string; created: string }[]
}

let csrf = ''
export function setCsrf(value: string) { csrf = value }
export class ApiError extends Error { constructor(message: string, public status: number) { super(message) } }
export async function api<T = any>(path: string, method = 'GET', body?: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch('/api/v1' + path, { method, credentials: 'same-origin', cache: 'no-store',
      headers: { ...(method !== 'GET' ? { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf } : {}) },
      ...(method !== 'GET' ? { body: JSON.stringify(body ?? {}) } : {}),
    })
  } catch { throw new ApiError('Connexion au serveur impossible. Les modifications nécessitent une connexion.', 0) }
  const value = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof value.detail === 'string' ? value.detail : 'Vérifier les champs et les quantités saisis.'
    throw new ApiError(detail, response.status)
  }
  return value
}

export function photoUrl(recipe: Recipe) { return `/api/v1/recipes/${recipe.id}/photo?v=${recipe.photo_version || ''}` }
export async function uploadPhoto(id: number, image: Blob) {
  let response: Response
  try { response = await fetch(`/api/v1/recipes/${id}/photo`, { method: 'PUT', credentials: 'same-origin', cache: 'no-store', headers: { 'Content-Type': image.type || 'application/octet-stream', 'X-CSRF-Token': csrf }, body: image }) }
  catch { throw new ApiError('Photo non envoyée : connexion au serveur impossible.', 0) }
  const value = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(typeof value.detail === 'string' ? value.detail : 'Cette photo ne peut pas être enregistrée.', response.status)
  return value
}

export function baseUnit(ingredient?: Ingredient): Unit {
  return ingredient?.dimension === 'masse' ? 'g' : ingredient?.dimension === 'volume' ? 'ml' : 'piece'
}
export function units(ingredient?: Ingredient): Unit[] {
  return ingredient?.dimension === 'masse' ? ['g', 'kg'] : ingredient?.dimension === 'volume' ? ['ml', 'l'] : ['piece']
}
