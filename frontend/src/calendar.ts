import type { Meal } from './api'

/** National French holidays, computed locally. Local/overseas additions are not included.
 * Reference: https://calendrier.api.gouv.fr/jours-feries/metropole/2026.json
 */
export function frenchPublicHolidays(year: number): Readonly<Record<string, string>> {
  if (!Number.isInteger(year) || year < 1583 || year > 4099) return {}
  const a = year % 19, b = Math.floor(year / 100), c = year % 100
  const d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25)
  const g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7
  const m = Math.floor((a + 11 * h + 22 * l) / 451)
  const month = Math.floor((h + l - 7 * m + 114) / 31)
  const day = (h + l - 7 * m + 114) % 31 + 1
  const easter = Date.UTC(year, month - 1, day)
  const afterEaster = (offset: number) => new Date(easter + offset * 86400000).toISOString().slice(0, 10)
  return Object.freeze({
    [`${year}-01-01`]: 'Jour de l’an',
    [afterEaster(1)]: 'Lundi de Pâques',
    [`${year}-05-01`]: 'Fête du Travail',
    [`${year}-05-08`]: 'Victoire 1945',
    [afterEaster(39)]: 'Ascension',
    [afterEaster(50)]: 'Lundi de Pentecôte',
    [`${year}-07-14`]: 'Fête nationale',
    [`${year}-08-15`]: 'Assomption',
    [`${year}-11-01`]: 'Toussaint',
    [`${year}-11-11`]: 'Armistice 1918',
    [`${year}-12-25`]: 'Noël',
  })
}

const cached = new Map<number, Readonly<Record<string, string>>>()
export function holidayName(value: string): string | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined
  const year = Number(value.slice(0, 4))
  if (!cached.has(year)) cached.set(year, frenchPublicHolidays(year))
  return cached.get(year)?.[value]
}

export function mealPrintContent(meal?: Meal) {
  if (!meal) return { title: 'À prévoir', side: '', detail: '', prepared: false }
  const away = { travail: 'Au travail', exterieur: 'À l’extérieur', a_decider: 'À décider' }
  if (meal.status !== 'maison') return { title: away[meal.status], side: '', detail: '', prepared: false }
  const title = meal.recipe_name || meal.title || 'À prévoir'
  return { title, side: meal.side_name || '',
    detail: meal.recipe_name || meal.title || meal.side_name ? `${meal.portions} portion${meal.portions > 1 ? 's' : ''}` : '',
    prepared: !!meal.prepared }
}
