<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { api, ApiError, baseUnit, photoUrl, setCsrf, units, type Dashboard, type Ingredient, type Meal, type Recipe, type Status } from './api'
import Icon from './Icon.vue'
import WeeklyPrint from './WeeklyPrint.vue'
import RecipeImport from './RecipeImport.vue'
import RecipePhoto from './RecipePhoto.vue'
import ComfortPanel from './ComfortPanel.vue'
import ShoppingTravel from './ShoppingTravel.vue'
import { readTravel, updateTravel } from './shoppingTravel'
import { holidayName } from './calendar'
import { takeSharedRecipe, type SharedRecipe } from './recipeShare'

const nav = [
  { id: 'week', label: 'Ma semaine', icon: 'calendar' }, { id: 'recipes', label: 'Mes recettes', icon: 'book' },
  { id: 'stock', label: 'Mes réserves', icon: 'stock' }, { id: 'shopping', label: 'Mes courses', icon: 'cart' },
  { id: 'history', label: 'Historique', icon: 'clock' },
  { id: 'settings', label: 'Mon organisation', icon: 'settings' },
]
const statuses: { id: Status; label: string }[] = [{ id: 'maison', label: 'À la maison' }, { id: 'travail', label: 'Au travail' }, { id: 'exterieur', label: 'À l’extérieur' }, { id: 'a_decider', label: 'À décider' }]
const days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
const page = ref('week'), data = ref<Dashboard | null>(null), user = ref(''), initialized = ref(true), starting = ref(true)
const busy = ref(false), error = ref(''), notice = ref(''), search = ref(''), online = ref(navigator.onLine)
const login = reactive({ name: '', password: '' })
const settingsDraft = ref({ portions: 4, presence: [] as Dashboard['settings']['presence'] })
const ingredientDraft = reactive({ name: '', dimension: 'masse' })
const modal = ref(''), draft = ref<any>({}), dialog = ref<HTMLDialogElement | null>(null)
const importOpen = ref(false), travelOpen = ref(false), household = ref(''), recipeFilter = ref('all'), categoryFilter = ref('')
const opinion = ref<Recipe | undefined>()
const photoRecipeId = ref<number | null>(null)
const photoRecipe = computed(() => data.value?.recipes.find(r => r.id === photoRecipeId.value))
const showIdeas = ref(false), showCopy = ref(false)
const shareSecure = window.isSecureContext
const shared = ref<SharedRecipe | null>(null)
try { shared.value = takeSharedRecipe(document); if (shared.value) history.replaceState(null, '', '/') } catch (e) { error.value = e instanceof Error ? e.message : 'Partage illisible.' }
const dates = computed(() => Array.from({ length: 7 }, (_, n) => shiftDate(start.value, n)))
const today = localDate(new Date())
const start = ref(monday(today))
const title = computed(() => nav.find(n => n.id === page.value)?.label || 'Ma semaine')
const filteredRecipes = computed(() => data.value?.recipes.filter(r => r.name.toLocaleLowerCase('fr').includes(search.value.toLocaleLowerCase('fr')) && (recipeFilter.value !== 'favorite' || r.favorite) && (recipeFilter.value !== 'to_try' || r.to_try) && (!categoryFilter.value || r.category === categoryFilter.value)) || [])
const totalStock = computed(() => data.value?.stock.filter(s => s.quantity > 0).length || 0)
const planned = computed(() => data.value?.week.meals.filter(m => m.status === 'maison' && (m.recipe_id || m.title)).length || 0)
const checked = computed(() => data.value?.shopping.items.filter(i => i.checked).length || 0)
const modalTitle = computed(() => ({ meal: 'Au menu', recipe: draft.value.id ? 'Modifier la recette' : 'Nouvelle recette', ingredient: draft.value.id ? 'Modifier l’ingrédient' : 'Nouvel ingrédient', stock: 'Ajouter aux réserves', correct: 'Corriger la quantité', prepare: 'Repas préparé', purchase: 'Terminer les courses', manual: 'Ajouter à la liste' }[modal.value] || 'Mijote'))

function localDate(date: Date) { return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}` }
function shiftDate(value: string, amount: number) { const d = new Date(value + 'T12:00:00'); d.setDate(d.getDate() + amount); return localDate(d) }
function monday(value: string) { const d = new Date(value + 'T12:00:00'); return shiftDate(value, -((d.getDay() + 6) % 7)) }
function dateLabel(value: string, options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'long' }) { return new Date(value + 'T12:00:00').toLocaleDateString('fr-FR', options) }
function amount(value: number) { return Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 3 }) }
function unitLabel(value: string) { return value === 'piece' ? 'pièce(s)' : value }
async function printWeek() { page.value = 'week'; await nextTick(); window.print() }
function statusLabel(value: Status) { return statuses.find(s => s.id === value)?.label }
function ingredient(id: number): Ingredient | undefined { return data.value?.ingredients.find(i => i.id === Number(id)) }
function meal(day: string, slot: string) { return data.value?.week.meals.find(m => m.day === day && m.slot === slot) }
function newId() {
  if (crypto.randomUUID) return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6]! & 15) | 64; bytes[8] = (bytes[8]! & 63) | 128
  const s = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''); return `${s.slice(0, 8)}-${s.slice(8, 12)}-${s.slice(12, 16)}-${s.slice(16, 20)}-${s.slice(20)}`
}
function fail(e: unknown) { error.value = e instanceof Error ? e.message : 'Une erreur est survenue.'; if (e instanceof ApiError && e.status === 401) { user.value = ''; data.value = null } }
async function run(action: () => Promise<void>) { if (busy.value) return; busy.value = true; error.value = ''; notice.value = ''; try { await action() } catch (e) { fail(e) } finally { busy.value = false } }
async function load() {
  await api('/weeks', 'POST', { start: start.value })
  data.value = await api<Dashboard>(`/dashboard?start=${start.value}`)
  settingsDraft.value = JSON.parse(JSON.stringify(data.value.settings))
}
async function signIn() { await run(async () => { const result = await api(`/auth/${initialized.value ? 'login' : 'setup'}`, 'POST', login); user.value = result.name; household.value = result.household_id; setCsrf(result.csrf); login.password = ''; await load() }) }
async function logout() { await run(async () => { const local = await readTravel().catch(() => null); if (local?.queue.length && !window.confirm('Des modifications de courses sont en attente. Se déconnecter et effacer cette copie locale ? Une opération déjà envoyée peut avoir été appliquée au serveur.')) return; await api('/auth/logout', 'POST'); closeImport(); await updateTravel(() => null); user.value = ''; household.value = ''; data.value = null; setCsrf('') }) }
async function changeWeek(delta: number) { await run(async () => { start.value = shiftDate(start.value, delta * 7); await load() }) }
function show(kind: string, value: any) { error.value = ''; modal.value = kind; draft.value = JSON.parse(JSON.stringify(value)) }
function close() { modal.value = ''; error.value = '' }
function openMeal(value?: Meal) { if (value) show('meal', value) }
function firstMeal() { openMeal(data.value?.week.meals.find(m => !m.prepared && m.status === 'maison' && !m.recipe_id && !m.title) || data.value?.week.meals.find(m => !m.prepared)) }
function openRecipe(recipe?: Recipe) { show('recipe', recipe || { name: '', kind: 'recette', portions: data.value?.settings.portions || 4, steps: '', minutes: 20, source_url: '', source_author: '', ingredient_notes: '', ingredients: [] }) }
function openIngredient(value?: Ingredient) { show('ingredient', value || { name: '', dimension: 'masse' }) }
function openLine(kind: string) { const i = data.value?.ingredients[0]; show(kind, { ingredient_id: i?.id || 0, quantity: 1, unit: baseUnit(i), location: 'Placard', expires: '' }) }
function addLine() { const i = data.value?.ingredients[0]; draft.value.ingredients.push({ ingredient_id: i?.id || 0, quantity: 1, unit: baseUnit(i) }) }
function changeIngredient(line: any) { line.unit = baseUnit(ingredient(line.ingredient_id)) }
async function openPreparation() {
  await run(async () => {
    const current = draft.value as Meal
    await api(`/meals/${current.id}`, 'PUT', { status: current.status, title: current.title, recipe_id: current.recipe_id || null, side_id: current.side_id || null, portions: Number(current.portions) })
    await load()
    const lines = data.value?.shopping.needs.meals.find(m => m.meal_id === current.id)?.ingredients || []
    show('prepare', { id: current.id, operation_id: newId(), quantities: lines.map(l => ({ ingredient_id: l.ingredient_id, quantity: l.required, unit: baseUnit(ingredient(l.ingredient_id)) })) })
  })
}
function openPurchase() { show('purchase', { operation_id: newId(), items: data.value?.shopping.items.filter(i => i.checked).map(i => ({ ...i, found: true, requested_ingredient_id: i.ingredient_id, location: 'Placard', expires: '' })) || [] }) }
function closeImport() { importOpen.value = false; shared.value = null }
async function importedRecipe() { closeImport(); await run(async () => { await load(); notice.value = 'Recette importée après vérification. Aucun stock n’a été modifié.' }) }
function importUnauthorized() { importOpen.value = false; fail(new ApiError('Connexion nécessaire.', 401)) }
async function createIngredientInline() {
  await run(async () => { const result = await api('/ingredients', 'POST', ingredientDraft); ingredientDraft.name = ''; await load(); draft.value.ingredients.push({ ingredient_id: result.id, quantity: 1, unit: baseUnit(ingredient(result.id)) }) })
}
async function save() {
  await run(async () => {
    const d = draft.value
    if (modal.value === 'meal') {
      await api(`/meals/${d.id}`, 'PUT', { status: d.status, title: d.title, recipe_id: d.recipe_id || null, side_id: d.side_id || null, portions: Number(d.portions) })
    } else if (modal.value === 'recipe') {
      const body = { name: d.name, kind: d.kind, portions: Number(d.portions), steps: d.steps, minutes: Number(d.minutes), source_url: d.source_url, source_author: d.source_author || '', ingredient_notes: d.ingredient_notes || '',
        ingredients: d.kind === 'simple' ? [] : d.ingredients.map((l: any) => ({ ingredient_id: Number(l.ingredient_id), quantity: Number(l.quantity), unit: l.unit })) }
      await api('/recipes' + (d.id ? `/${d.id}` : ''), d.id ? 'PUT' : 'POST', body)
    } else if (modal.value === 'ingredient') {
      await api('/ingredients' + (d.id ? `/${d.id}` : ''), d.id ? 'PUT' : 'POST', { name: d.name, dimension: d.dimension })
    } else if (modal.value === 'stock') {
      await api('/stock', 'POST', { ingredient_id: Number(d.ingredient_id), quantity: Number(d.quantity), unit: d.unit, location: d.location, expires: d.expires || null })
    } else if (modal.value === 'manual') {
      await api(`/weeks/${start.value}/shopping/manual`, 'POST', { ingredient_id: Number(d.ingredient_id), quantity: Number(d.quantity), unit: d.unit })
    } else if (modal.value === 'correct') {
      await api(`/stock/${d.id}`, 'PATCH', { quantity: Number(d.quantity), unit: d.unit, reason: d.reason })
    } else if (modal.value === 'prepare') {
      const result = await api(`/meals/${d.id}/prepare`, 'POST', { operation_id: d.operation_id, quantities: d.quantities.filter((l: any) => Number(l.quantity) > 0).map((l: any) => ({ ingredient_id: l.ingredient_id, quantity: Number(l.quantity), unit: l.unit })) })
      notice.value = result.shortages.length ? `Repas confirmé. Stock insuffisant pour : ${result.shortages.map((l: any) => l.name).join(', ')}. Aucun stock négatif n’a été créé.` : 'Repas préparé : les réserves ont été mises à jour.'
    } else if (modal.value === 'purchase') {
      for (const line of d.items.filter((i: any) => !i.found)) await api(`/weeks/${start.value}/shopping/check`, 'PATCH', { checked: false, ...(line.manual_id ? { manual_id: line.manual_id } : { ingredient_id: line.requested_ingredient_id }) })
      const found = d.items.filter((i: any) => i.found)
      if (found.length) await api(`/weeks/${start.value}/shopping/complete`, 'POST', { operation_id: d.operation_id, items: found.map((l: any) => ({ ingredient_id: Number(l.ingredient_id), requested_ingredient_id: l.requested_ingredient_id, manual_id: l.manual_id, quantity: Number(l.quantity), unit: l.unit, location: l.location, expires: l.expires || null })) })
      notice.value = found.length ? 'Courses terminées : les achats sont dans les réserves.' : 'Les articles non trouvés restent sur la liste.'
    }
    modal.value = ''; await load()
  })
}
async function checkItem(item: any) { await run(async () => { await api(`/weeks/${start.value}/shopping/check`, 'PATCH', { checked: !item.checked, ...(item.manual_id ? { manual_id: item.manual_id } : { ingredient_id: item.ingredient_id }) }); await load() }) }
async function removeItem(item: any) { await run(async () => { await api(`/weeks/${start.value}/shopping/manual/${item.manual_id}`, 'DELETE'); await load() }) }
async function deleteEntry(kind: string, id: number) {
  if (!window.confirm('Supprimer cet élément ? Un élément utilisé par un repas ou un mouvement sera conservé.')) return
  await run(async () => { await api(`/${kind}/${id}`, 'DELETE'); await load() })
}
async function applyTemplate() {
  if (!window.confirm('Appliquer les habitudes et les portions à la semaine vide affichée ?')) return
  await run(async () => { await api('/settings', 'PUT', settingsDraft.value); await api(`/weeks/${start.value}/template`, 'POST'); await load(); notice.value = 'Les habitudes de la maison sont appliquées à cette semaine vide.' })
}
async function saveSettings() { await run(async () => { await api('/settings', 'PUT', settingsDraft.value); await load(); notice.value = 'Organisation enregistrée. Elle sera appliquée aux prochaines semaines ; les semaines existantes sont conservées.' }) }
async function updateOnline() { online.value = navigator.onLine; if (!online.value && await readTravel().catch(() => null)) travelOpen.value = true }
async function closeTravel() { travelOpen.value = false; if (user.value && online.value) await run(load) }
async function favorite(recipe: Recipe) { await run(async () => { await api(`/recipes/${recipe.id}/preferences`, 'PATCH', { favorite: !recipe.favorite }); await load() }) }
watch([user, data, starting], () => { if (user.value && data.value && !starting.value && shared.value) { page.value = 'recipes'; travelOpen.value = false; importOpen.value = true } })
watch(modal, value => { if (value) requestAnimationFrame(() => { if (!dialog.value?.open) dialog.value?.showModal() }); else dialog.value?.close() })
onMounted(async () => {
  window.addEventListener('online', updateOnline); window.addEventListener('offline', updateOnline)
  try {
    initialized.value = (await api('/auth/status')).initialized
    if (initialized.value) {
      try { const me = await api('/auth/me'); user.value = me.name; household.value = me.household_id; setCsrf(me.csrf); await load() } catch (e) { if (!(e instanceof ApiError && e.status === 401)) throw e }
    }
  } catch (e) { fail(e); if (await readTravel().catch(() => null)) travelOpen.value = true } finally { starting.value = false }
})
onUnmounted(() => { window.removeEventListener('online', updateOnline); window.removeEventListener('offline', updateOnline) })
</script>

<template>
  <div v-if="starting" class="loading"><img src="/icon.svg" width="64" height="64" alt=""><p>Mijote se prépare…</p></div>
  <ShoppingTravel v-else-if="travelOpen" :household="household" :week="start" @close="closeTravel" @changed="online && user && run(load)" @unauthorized="household = ''; user = ''; data = null; setCsrf('')" />
  <main v-else-if="!user" class="auth-page">
    <section class="auth-story"><a class="brand" href="/"><img src="/icon.svg" alt="" width="52" height="52"><span>mijote<span class="brand-dot">.</span></span></a><div><span class="eyebrow light">À TABLE, SIMPLEMENT</span><h1>Moins de « on mange quoi ? ».<br>Plus de bons moments.</h1><p>Les recettes, les réserves et les repas de la semaine,<br>réunis au même endroit.</p></div><span class="auth-signature">Une maison bien organisée, à votre rythme.</span></section>
    <section class="auth-form"><div class="auth-card"><span class="eyebrow">VOTRE CUISINE, VOTRE ESPACE</span><h2>{{ initialized ? 'Heureux de vous retrouver' : 'Bienvenue chez Mijote' }}</h2><p>{{ initialized ? 'Connectez-vous pour retrouver votre semaine.' : 'Créez le compte de la maison pour commencer.' }}</p>
      <p v-if="shared" class="alert" role="status">Un partage de recette vous attend après connexion.<button class="text-button" @click="closeImport">Annuler</button></p><p v-if="error" role="alert" class="alert error">{{ error }}</p><p v-if="!online" class="alert">Connexion nécessaire pour ouvrir votre espace.</p>
      <form @submit.prevent="signIn"><label>Nom du compte<input v-model="login.name" required maxlength="120" autocomplete="username" placeholder="La maison"></label><label>Mot de passe<input v-model="login.password" type="password" required minlength="12" maxlength="128" :autocomplete="initialized ? 'current-password' : 'new-password'"></label><small v-if="!initialized">Au moins 12 caractères. Ce compte sera partagé par la famille.</small><button class="primary wide" :disabled="busy || !online">{{ busy ? 'Un instant…' : initialized ? 'Entrer dans ma cuisine' : 'Créer mon espace' }}<Icon name="right" /></button></form><button class="text-button" @click="travelOpen = true">Ouvrir ma copie de courses locale</button><p class="private-note"><Icon name="leaf" :size="17" /> Vos données restent dans votre maison.</p>
    </div></section>
  </main>
  <div v-else class="app-shell">
    <aside class="sidebar"><a class="brand" href="/" @click.prevent="page = 'week'"><img src="/icon.svg" width="42" height="42" alt=""><span>mijote<span class="brand-dot">.</span></span></a><p class="sidebar-tagline">À table, simplement</p>
      <nav aria-label="Navigation principale"><button v-for="item in nav" :key="item.id" :class="{ active: page === item.id }" @click="page = item.id" :aria-current="page === item.id ? 'page' : undefined"><Icon :name="item.icon" /><span>{{ item.label }}</span><span v-if="item.id === 'shopping' && data?.shopping.items.length" class="nav-count">{{ data.shopping.items.length }}</span></button></nav>
      <div class="sidebar-bottom"><div class="little-leaf"><Icon name="leaf" :size="26" /></div><p>Un peu d’organisation.<br>Beaucoup de gourmandise.</p><button class="account" @click="logout" :disabled="busy"><span class="avatar">{{ user.slice(0, 1).toUpperCase() }}</span><span>{{ user }}<small>Compte de la maison</small></span><Icon name="logout" :size="18" /></button></div>
    </aside>
    <main class="workspace"><header class="topbar"><div><span class="eyebrow">LE QUOTIDIEN A BON GOÛT</span><h1>{{ title }}</h1></div><span class="today-label"><Icon name="calendar" :size="17" />{{ dateLabel(today, { weekday: 'long', day: 'numeric', month: 'long' }) }}</span></header>
      <div v-if="!online" class="alert" role="status">Hors connexion : le planning nécessite le réseau. Ouvrez votre liste à emporter si vous en avez enregistré une copie.</div>
      <div v-if="error && !modal" class="alert error" role="alert">{{ error }}<button class="text-button" @click="run(load)">Réessayer</button></div><div v-if="notice" class="alert success" role="status">{{ notice }}<button class="icon-button" @click="notice = ''" aria-label="Fermer le message"><Icon name="close" :size="16" /></button></div>
      <div v-if="!data" class="empty"><h2>Votre semaine n’a pas pu être chargée.</h2><button class="primary" @click="run(load)" :disabled="busy || !online">Réessayer</button></div>
      <template v-else>
        <section v-if="page === 'week'">
          <div class="week-intro"><div><h2>Une semaine qui donne envie.</h2><p>Un repas après l’autre, faites de la place aux bonnes idées.</p></div><button class="primary" @click="firstMeal" :disabled="busy || !online"><Icon name="plus" />Planifier un repas</button></div>
          <div class="week-toolbar"><div class="date-navigation"><button class="icon-button" aria-label="Semaine précédente" @click="changeWeek(-1)" :disabled="busy"><Icon name="left" /></button><h3>{{ dateLabel(start) }} <span>—</span> {{ dateLabel(shiftDate(start, 6)) }}</h3><button class="icon-button" aria-label="Semaine suivante" @click="changeWeek(1)" :disabled="busy"><Icon name="right" /></button></div><div class="week-actions"><button class="secondary small" @click="run(async () => { start = monday(today); await load() })" :disabled="busy">Cette semaine</button><button class="secondary small" @click="showCopy = !showCopy" :disabled="busy || !online">Copier un menu</button><button class="secondary small" @click="showIdeas = !showIdeas" :disabled="busy || !online">Des idées</button><button class="secondary small" @click="printWeek" :disabled="busy || !!modal"><Icon name="print" :size="16" />Imprimer la semaine</button></div></div><p class="calendar-legend"><span></span>Jours fériés nationaux · France</p>
          <ComfortPanel v-if="showCopy" section="copy" :data="data" @changed="run(load)" @unauthorized="importUnauthorized" /><ComfortPanel v-if="showIdeas" section="ideas" :data="data" @changed="run(load)" @unauthorized="importUnauthorized" />
          <div class="week-grid"><article v-for="(day, index) in dates" :key="day" class="day-column" :class="{ 'is-today': day === today, 'is-holiday': !!holidayName(day) }"><header><span>{{ days[index] }}</span><strong>{{ dateLabel(day, { day: 'numeric' }) }}</strong><small v-if="day === today">Aujourd’hui</small><small v-if="holidayName(day)" class="holiday-tag" :title="holidayName(day)">Férié · {{ holidayName(day) }}</small></header>
            <button v-for="slot in (['midi', 'soir'] as const)" :key="slot" class="meal-card" :class="{ outside: meal(day, slot)?.status !== 'maison', filled: !!(meal(day, slot)?.recipe_id || meal(day, slot)?.title), prepared: !!meal(day, slot)?.prepared }" @click="openMeal(meal(day, slot))" :disabled="busy || !online" :aria-label="`${days[index]} ${slot} : ${meal(day, slot)?.recipe_name || meal(day, slot)?.title || statusLabel(meal(day, slot)?.status || 'a_decider')}`">
              <span class="meal-slot"><Icon :name="slot === 'midi' ? 'sun' : 'moon'" :size="14" />{{ slot === 'midi' ? 'Midi' : 'Soir' }}<Icon v-if="meal(day, slot)?.prepared" name="check" :size="15" /></span>
              <template v-if="meal(day, slot)?.recipe_id || meal(day, slot)?.title"><span class="dish-mark"><Icon name="leaf" :size="23" /></span><strong>{{ meal(day, slot)?.recipe_name || meal(day, slot)?.title }}</strong><small v-if="meal(day, slot)?.side_name">+ {{ meal(day, slot)?.side_name }}</small><span class="meal-foot">{{ meal(day, slot)?.prepared ? 'Préparé' : meal(day, slot)?.status === 'maison' ? `${meal(day, slot)?.portions} portions` : statusLabel(meal(day, slot)!.status) }}</span></template>
              <template v-else-if="meal(day, slot)?.status === 'maison'"><span class="add-dish"><Icon name="plus" :size="22" /></span><span class="empty-dish">Ajouter un repas</span></template>
              <template v-else><span class="presence-symbol">{{ meal(day, slot)?.status === 'travail' ? '↗' : meal(day, slot)?.status === 'exterieur' ? '↗' : '…' }}</span><strong class="presence-title">{{ statusLabel(meal(day, slot)!.status) }}</strong></template>
            </button>
          </article></div>
          <div class="week-bottom"><div class="planning-note"><span class="round-icon"><Icon name="leaf" :size="26" /></span><div><h3>Chacun son rythme</h3><p>Un déjeuner au travail ? Une sortie prévue ? Changez le créneau : seuls les repas maison comptent dans les courses.</p><button class="text-button" @click="page = 'settings'">Définir mon organisation <Icon name="right" :size="15" /></button></div></div><button class="shopping-preview" @click="page = 'shopping'"><span class="round-icon orange"><Icon name="cart" :size="25" /></span><span><strong>Les courses de la semaine</strong><small>{{ data.shopping.items.length ? `${data.shopping.items.length} article(s) sur la liste` : 'La liste se remplit à partir de vos repas' }}</small></span><Icon name="right" /></button></div>
          <p class="quiet-note">{{ planned }} repas maison planifié(s) · {{ data.recipes.length }} recette(s) · {{ totalStock }} lot(s) dans les réserves</p>
        </section>

        <section v-else-if="page === 'recipes'">
          <div class="section-heading"><div><h2>Les bonnes idées se gardent.</h2><p>Un simple plat ou une recette détaillée : commencez à votre façon.</p></div><div class="recipe-actions"><button class="secondary" @click="importOpen = true" :disabled="busy || !online"><Icon name="link" :size="18" />Importer une recette</button><button class="primary" @click="openRecipe()" :disabled="busy || !online"><Icon name="plus" />Ajouter une recette</button></div></div>
          <input class="search" v-model="search" type="search" placeholder="Rechercher une recette…" aria-label="Rechercher une recette">
          <div class="comfort-actions recipe-filters"><label>Afficher<select v-model="recipeFilter"><option value="all">Toutes les recettes</option><option value="favorite">Favoris</option><option value="to_try">À tester</option></select></label><label>Catégorie<select v-model="categoryFilter"><option value="">Toutes les catégories</option><option value="autre">Autre</option><option value="viande">Viande</option><option value="poisson">Poisson</option><option value="legumes">Légumes</option><option value="vegetarien">Végétarien</option><option value="feculents">Féculents</option><option value="dessert">Dessert</option></select></label></div>
          <ComfortPanel v-if="opinion" section="preferences" :data="data" :recipe="opinion" @changed="run(load)" @unauthorized="importUnauthorized" /><button v-if="opinion" class="text-button" @click="opinion = undefined">Fermer mon avis</button>
          <div v-if="!filteredRecipes.length" class="empty"><span class="empty-icon"><Icon name="book" :size="38" /></span><h3>{{ search ? 'Aucune recette correspondante' : 'Votre carnet attend sa première recette' }}</h3><p>{{ search ? 'Essayez un autre nom.' : 'Enregistrez un plat habituel, puis ajoutez les ingrédients quand vous le souhaitez.' }}</p><button v-if="!search" class="secondary" @click="openRecipe()">Créer ma première recette</button></div>
          <div class="recipe-grid"><article v-for="recipe in filteredRecipes" :key="recipe.id" class="recipe-card"><button class="recipe-open" @click="openRecipe(recipe)"><div class="recipe-cover" :class="recipe.kind"><img v-if="recipe.photo_version" :src="photoUrl(recipe)" :alt="recipe.name" loading="lazy"><Icon v-else :name="recipe.kind === 'simple' ? 'book' : 'leaf'" :size="44" /><span v-if="!recipe.photo_version">{{ recipe.kind === 'simple' ? 'Plat du quotidien' : recipe.kind === 'improvise' ? 'Cuisine improvisée' : 'Recette maison' }}</span></div><div class="recipe-body"><h3>{{ recipe.name }}</h3><p><span>{{ recipe.portions }} portions</span><span v-if="recipe.minutes"><Icon name="clock" :size="14" />{{ recipe.minutes }} min</span></p><small>{{ recipe.ingredients.length ? `${recipe.ingredients.length} ingrédient(s)` : 'Intitulé seul · pas de déduction de stock' }}</small><span v-if="recipe.to_try" class="recipe-badge">À tester</span></div></button><div class="comfort-actions recipe-options"><button class="text-button" @click="favorite(recipe)" :disabled="busy || !online" :aria-pressed="!!recipe.favorite">{{ recipe.favorite ? '★ Favori' : '☆ Favori' }}</button><button class="text-button" @click="photoRecipeId = recipe.id" :disabled="busy || !online">Photo</button><button class="text-button" @click="opinion = recipe" :disabled="!online">Mon avis</button></div><button class="icon-button delete-recipe" :aria-label="`Supprimer ${recipe.name}`" @click="deleteEntry('recipes', recipe.id)"><Icon name="trash" :size="17" /></button></article></div>
          <details class="ingredient-panel"><summary>Importer depuis mon téléphone</summary><p>Avec Mijote installé dans Chrome sur Android, ouvrez une recette puis choisissez Partager → Mijote. Le lien ou le texte préremplit l’import ; la prévisualisation et votre confirmation restent nécessaires.</p><p v-if="!shareSecure">Sur cette adresse HTTP, copiez le lien puis utilisez « Importer une recette ». Le partage direct demandera une adresse HTTPS et l’installation de Mijote.</p></details>
          <details class="ingredient-panel"><summary>Mon répertoire d’ingrédients <span>{{ data.ingredients.length }}</span></summary><p>Un ingrédient décrit un aliment, indépendamment de sa marque. Gardez des noms distincts lorsque la différence compte en cuisine.</p><div class="ingredient-tags"><div v-for="i in data.ingredients" :key="i.id"><button @click="openIngredient(i)">{{ i.name }} <small>{{ unitLabel(baseUnit(i)) }}</small><Icon name="edit" :size="13" /></button><button class="icon-button" :aria-label="`Supprimer ${i.name}`" @click="deleteEntry('ingredients', i.id)"><Icon name="close" :size="13" /></button></div></div><button class="secondary small" @click="openIngredient()"><Icon name="plus" :size="17" />Nouvel ingrédient</button></details>
        </section>

        <section v-else-if="page === 'history'"><ComfortPanel section="history" :data="data" @changed="run(load)" @unauthorized="importUnauthorized" /></section>

        <section v-else-if="page === 'stock'">
          <div class="section-heading"><div><h2>Déjà dans la cuisine.</h2><p>Notez les réserves utiles, même approximativement. Tout reste corrigeable.</p></div><button class="primary" @click="openLine('stock')" :disabled="busy || !online"><Icon name="plus" />Ajouter un aliment</button></div>
          <div v-if="!data.ingredients.length" class="inline-help">Commencez par <button class="text-button" @click="openIngredient()">créer un ingrédient</button> pour renseigner vos réserves.</div>
          <div v-if="!data.stock.some(s => s.quantity > 0)" class="empty"><span class="empty-icon"><Icon name="stock" :size="38" /></span><h3>Un coup d’œil dans les placards ?</h3><p>Ajoutez quelques aliments : Mijote en tiendra compte pour les courses.</p></div>
          <div class="stock-grid"><article v-for="location in [...new Set(data.stock.filter(s => s.quantity > 0).map(s => s.location))]" :key="location" class="stock-location"><h3><Icon name="stock" />{{ location }}</h3><button v-for="lot in data.stock.filter(s => s.location === location && s.quantity > 0)" :key="lot.id" class="stock-line" @click="show('correct', { ...lot, reason: 'Correction manuelle' })"><span><strong>{{ lot.name }}</strong><small v-if="lot.expires" :class="{ expired: lot.expires < today }">{{ lot.expires < today ? 'Date dépassée · ' : 'À utiliser avant le ' }}{{ dateLabel(lot.expires) }}</small></span><span>{{ amount(lot.quantity) }} {{ unitLabel(lot.unit) }} <Icon name="edit" :size="15" /></span></button></article></div>
          <details class="ingredient-panel"><summary>Journal des mouvements</summary><p>Chaque ajout, achat, correction et préparation laisse une trace.</p><div v-for="entry in data.movements" :key="entry.id" class="movement"><span><strong>{{ entry.name }}</strong><small>{{ entry.reason }} · {{ new Date(entry.created).toLocaleString('fr-FR') }}</small></span><strong :class="entry.delta > 0 ? 'positive' : ''">{{ entry.delta > 0 ? '+' : '' }}{{ amount(entry.delta) }} {{ unitLabel(entry.unit) }}</strong></div><p v-if="!data.movements.length">Aucun mouvement pour le moment.</p></details>
        </section>

        <section v-else-if="page === 'shopping'">
          <div class="section-heading"><div><h2>Juste ce qu’il manque.</h2><p>Du {{ dateLabel(start) }} au {{ dateLabel(shiftDate(start, 6)) }} · les repas maison, moins les réserves disponibles.</p></div><button class="secondary" @click="openLine('manual')" :disabled="busy || !online"><Icon name="plus" />Ajouter un article</button></div>
          <div class="comfort-actions"><button class="primary" @click="travelOpen = true">Emporter ma liste / courses hors connexion</button></div>
          <div class="shopping-layout"><div class="shopping-list"><div class="list-heading"><h3>Ma liste <span>{{ data.shopping.items.length }}</span></h3><small>{{ checked }} dans le panier</small></div>
            <div v-if="!data.shopping.items.length" class="empty"><span class="empty-icon"><Icon name="cart" :size="38" /></span><h3>Rien à ajouter pour le moment</h3><p>Planifiez une recette avec des quantités ou ajoutez un article à la main.</p><button class="text-button" @click="page = 'week'">Revenir à la semaine <Icon name="right" :size="15" /></button></div>
            <div v-for="item in data.shopping.items" :key="item.key" class="shopping-line" :class="{ checked: item.checked }"><label><input type="checkbox" :checked="item.checked" :disabled="busy || !online" @change="checkItem(item)"><span><strong>{{ item.name }}</strong><small>{{ item.manual_id ? 'Ajout personnel' : 'Pour les repas de la semaine' }}</small></span><b>{{ amount(item.quantity) }} {{ unitLabel(item.unit) }}</b></label><button v-if="item.manual_id" class="icon-button" :aria-label="`Retirer ${item.name}`" @click="removeItem(item)" :disabled="busy"><Icon name="close" :size="16" /></button></div>
          </div><aside class="shopping-summary"><span class="round-icon orange"><Icon name="cart" :size="29" /></span><h3>Le panier est prêt ?</h3><p>Cocher un article le place dans le panier. Il rejoint les réserves uniquement après confirmation des achats.</p><button class="primary wide" @click="openPurchase" :disabled="busy || !online || !checked">Terminer les courses <Icon name="check" :size="18" /></button><small>Vérifiez les quantités achetées, les remplacements et les articles non trouvés avant de valider.</small></aside></div>
          <details class="ingredient-panel"><summary>Comprendre les besoins</summary><p>Le stock est affecté dans l’ordre des dates à tous les repas maison planifiés, y compris ceux d’autres semaines. Une réservation ne retire rien des réserves.</p><div v-for="need in data.shopping.needs.items" :key="need.ingredient_id" class="movement"><span><strong>{{ need.name }}</strong><small>Besoin : {{ amount(need.required) }} {{ unitLabel(need.unit) }} · réservé : {{ amount(need.reserved) }}</small></span><strong>{{ amount(need.missing) }} manquant(s)</strong></div><p v-if="!data.shopping.needs.items.length">Aucun besoin quantifié cette semaine.</p></details>
        </section>

        <section v-else-if="page === 'settings'" class="settings-section"><div class="section-heading"><div><h2>Une semaine à votre rythme.</h2><p>Votre organisation habituelle sert de point de départ, jamais de contrainte.</p></div></div><form @submit.prevent="saveSettings" class="settings-form"><div class="settings-card"><h3>Combien à table ?</h3><p>Le nombre de portions par défaut pour les nouvelles semaines. Chaque repas peut avoir ses propres portions.</p><label class="portions-label">Portions<input v-model.number="settingsDraft.portions" type="number" min="1" max="30" required></label></div><div class="settings-card"><h3>Les habitudes de la maison</h3><p>Ce modèle s’applique à la création d’une semaine. Une exception dans le planning ne le modifie pas.</p><div class="presence-table"><div class="presence-header"><span></span><strong>Midi</strong><strong>Soir</strong></div><div v-for="(day, index) in days" :key="day"><strong>{{ day }}</strong><label v-for="slot in (['midi','soir'] as const)" :key="slot"><span class="sr-only">{{ day }} {{ slot }}</span><select :value="settingsDraft.presence.find(p => p.day === index && p.slot === slot)?.status" @change="settingsDraft.presence.find(p => p.day === index && p.slot === slot)!.status = ($event.target as HTMLSelectElement).value as Status"><option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.label }}</option></select></label></div></div></div><button class="primary" :disabled="busy || !online"><Icon name="check" :size="18" />Enregistrer mon organisation</button></form><div v-if="data.week.meals.every(m => !m.prepared && !m.title && !m.recipe_id && !m.side_id)" class="settings-card extra-setting"><h3>Commencer avec les bonnes habitudes</h3><p>La semaine affichée ne contient aucun repas. Vous pouvez lui appliquer ce modèle explicitement.</p><button class="secondary" @click="applyTemplate" :disabled="busy || !online">Appliquer à cette semaine vide</button></div><div class="settings-card extra-setting"><h3>Compte de la maison</h3><p>Session ouverte pour {{ user }}.</p><button class="secondary" @click="logout" :disabled="busy"><Icon name="logout" :size="17" />Se déconnecter</button></div></section>
      </template><footer class="app-footer">mijote<span>·</span>Les bonnes habitudes commencent dans l’assiette.</footer>
    </main>
  </div>

  <RecipeImport v-if="importOpen && user && data" :ingredients="data.ingredients" :initial="shared" @close="closeImport" @saved="importedRecipe" @unauthorized="importUnauthorized" />

  <RecipePhoto v-if="photoRecipe && user" :recipe="photoRecipe" @close="photoRecipeId = null" @changed="run(load)" @unauthorized="photoRecipeId = null; importUnauthorized()" />

  <WeeklyPrint v-if="user && data" :dates="dates" :meals="data.week.meals" />

  <dialog ref="dialog" @cancel.prevent="!busy && close()" @click="($event.target === dialog) && !busy && close()" :aria-label="modalTitle">
    <form v-if="modal" @submit.prevent="save" class="dialog-form"><header><div><span class="eyebrow">DANS MA CUISINE</span><h2>{{ modalTitle }}</h2></div><button type="button" class="icon-button" @click="close" :disabled="busy" aria-label="Fermer"><Icon name="close" /></button></header><div v-if="error" role="alert" class="alert error">{{ error }}</div>
      <template v-if="modal === 'meal'"><p>{{ dateLabel(draft.day, { weekday: 'long', day: 'numeric', month: 'long' }) }} · {{ draft.slot === 'midi' ? 'Midi' : 'Soir' }}</p><div v-if="draft.prepared" class="alert success">Ce repas est préparé. Les quantités consommées sont conservées dans le journal.</div><fieldset :disabled="busy || !!draft.prepared"><label>Où se passe ce repas ?<select v-model="draft.status"><option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.label }}</option></select></label><p v-if="draft.status !== 'maison'" class="hint">Les choix restent enregistrés, mais ce créneau ne compte pas dans les besoins.</p><label>Plat principal<select v-model="draft.recipe_id"><option :value="null">Un intitulé libre, sans recette</option><option v-for="r in data?.recipes" :key="r.id" :value="r.id">{{ r.name }}</option></select></label><label v-if="!draft.recipe_id">Nom du plat<input v-model="draft.title" maxlength="120" placeholder="Ex. soupe et tartines"></label><label>Accompagnement <small>facultatif</small><select v-model="draft.side_id"><option :value="null">Sans accompagnement</option><option v-for="r in data?.recipes" :key="r.id" :value="r.id">{{ r.name }}</option></select></label><label>Portions<input v-model.number="draft.portions" type="number" min="1" max="30" required></label></fieldset><button v-if="!draft.prepared && draft.status === 'maison' && (draft.recipe_id || draft.title)" type="button" class="secondary wide" @click="openPreparation" :disabled="busy"><Icon name="check" :size="18" />Ce repas est préparé</button><p class="hint">Enregistrer le planning ne consomme aucun stock.</p></template>
      <template v-else-if="modal === 'recipe'"><label>Nom du plat<input v-model="draft.name" required maxlength="120" placeholder="Ex. gratin de courgettes"></label><div class="form-row"><label>Format<select v-model="draft.kind"><option value="simple">Intitulé seul</option><option value="improvise">Plat improvisé</option><option value="recette">Recette détaillée</option></select></label><label>Portions de référence<input v-model.number="draft.portions" type="number" min="1" max="30" required></label></div><template v-if="draft.kind !== 'simple'"><h3>Ingrédients</h3><p class="hint">Les quantités seront adaptées aux portions de chaque repas.</p><div v-for="(line, index) in draft.ingredients" :key="index" class="ingredient-row"><select v-model.number="line.ingredient_id" @change="changeIngredient(line)" :aria-label="`Ingrédient ${Number(index)+1}`" required><option :value="0" disabled>Choisir</option><option v-for="i in data?.ingredients" :key="i.id" :value="i.id">{{ i.name }}</option></select><input v-model.number="line.quantity" type="number" min="0.001" step="0.001" required aria-label="Quantité"><select v-model="line.unit" aria-label="Unité"><option v-for="unit in units(ingredient(line.ingredient_id))" :key="unit" :value="unit">{{ unitLabel(unit) }}</option></select><button type="button" class="icon-button" @click="draft.ingredients.splice(index, 1)" aria-label="Retirer cet ingrédient"><Icon name="close" :size="16" /></button></div><button type="button" class="secondary small" @click="addLine" :disabled="!data?.ingredients.length"><Icon name="plus" :size="16" />Ajouter une ligne</button><details class="inline-ingredient"><summary>Un ingrédient manque au répertoire ?</summary><div class="form-row"><label>Nom<input v-model="ingredientDraft.name" maxlength="120" placeholder="Ex. riz basmati"></label><label>Mesure<select v-model="ingredientDraft.dimension"><option value="masse">Poids (g / kg)</option><option value="volume">Volume (ml / l)</option><option value="piece">Pièces</option></select></label></div><button type="button" class="text-button" @click="createIngredientInline" :disabled="busy || !ingredientDraft.name.trim()">Créer et ajouter cet ingrédient</button></details><label>Étapes<textarea v-model="draft.steps" rows="5" maxlength="20000" placeholder="Les étapes de préparation…"></textarea></label></template><div class="form-row"><label>Temps total (minutes)<input v-model.number="draft.minutes" type="number" min="0" max="1440" required></label><label>Source <small>facultative</small><input v-model="draft.source_url" type="url" maxlength="2000" placeholder="https://…"><small>Pour lire un lien, utiliser « Importer une recette » dans le carnet.</small></label></div></template>
      <template v-else-if="modal === 'ingredient'"><label>Nom de l’ingrédient<input v-model="draft.name" required maxlength="120" placeholder="Ex. tomates concassées"></label><label>Comment le mesurer ?<select v-model="draft.dimension"><option value="masse">Au poids (g / kg)</option><option value="volume">Au volume (ml / l)</option><option value="piece">En pièces</option></select></label><p class="hint">Le type d’unité d’un ingrédient déjà utilisé ne peut pas être changé.</p></template>
      <template v-else-if="modal === 'stock' || modal === 'manual'"><div v-if="!data?.ingredients.length" class="inline-help">Créer d’abord un ingrédient dans le répertoire des recettes. <button type="button" class="text-button" @click="openIngredient()">Créer un ingrédient</button></div><label>Aliment<select v-model.number="draft.ingredient_id" @change="changeIngredient(draft)" required><option :value="0" disabled>Choisir un ingrédient</option><option v-for="i in data?.ingredients" :key="i.id" :value="i.id">{{ i.name }}</option></select></label><div class="form-row"><label>Quantité<input v-model.number="draft.quantity" type="number" min="0.001" step="0.001" required></label><label>Unité<select v-model="draft.unit"><option v-for="unit in units(ingredient(draft.ingredient_id))" :key="unit" :value="unit">{{ unitLabel(unit) }}</option></select></label></div><template v-if="modal === 'stock'"><label>Emplacement<input v-model="draft.location" list="locations" required maxlength="120"></label><label>Date limite <small>facultative</small><input v-model="draft.expires" type="date"></label></template></template>
      <template v-else-if="modal === 'correct'"><h3>{{ draft.name }}</h3><label>Quantité réellement disponible<input v-model.number="draft.quantity" type="number" min="0" step="0.001" required></label><p class="hint">Unité : {{ unitLabel(draft.unit) }} · saisir 0 pour vider ce lot.</p><label>Motif de la correction<input v-model="draft.reason" maxlength="250" required></label></template>
      <template v-else-if="modal === 'prepare'"><p>Vérifiez ce qui a été utilisé. Les quantités indiquées seront retirées une seule fois des réserves.</p><p v-if="!draft.quantities.length" class="inline-help">Ce repas ne contient pas de quantités : aucun stock ne sera déduit.</p><div v-for="line in draft.quantities" :key="line.ingredient_id" class="preparation-line"><label>{{ ingredient(line.ingredient_id)?.name }}<input v-model.number="line.quantity" type="number" min="0" step="0.001" required></label><span>{{ unitLabel(line.unit) }}</span></div><p class="hint">Une quantité à 0 n’est pas déduite. Un stock insuffisant sera signalé sans empêcher la confirmation.</p></template>
      <template v-else-if="modal === 'purchase'"><p>Seuls les achats confirmés ci-dessous entreront dans les réserves. Décochez les articles non trouvés.</p><article v-for="item in draft.items" :key="item.key" class="purchase-item"><label class="check-label"><input v-model="item.found" type="checkbox"><strong>{{ item.name }}</strong><span>{{ item.found ? 'Acheté' : 'Non trouvé' }}</span></label><fieldset :disabled="!item.found || busy"><label>Aliment réellement acheté<select v-model.number="item.ingredient_id" @change="changeIngredient(item)"><option v-for="i in data?.ingredients" :key="i.id" :value="i.id">{{ i.name }}</option></select></label><div class="form-row"><label>Quantité<input v-model.number="item.quantity" type="number" min="0.001" step="0.001" required></label><label>Unité<select v-model="item.unit"><option v-for="unit in units(ingredient(item.ingredient_id))" :key="unit" :value="unit">{{ unitLabel(unit) }}</option></select></label></div><div class="form-row"><label>Emplacement<input v-model="item.location" list="locations" required maxlength="120"></label><label>Date limite<input v-model="item.expires" type="date"></label></div></fieldset></article></template>
      <template v-if="modal === 'recipe'"><label>Auteur ou attribution<input v-model="draft.source_author" maxlength="300" placeholder="Source de la recette"></label><label>Texte d’origine / ingrédients non quantifiés<textarea v-model="draft.ingredient_notes" rows="4" maxlength="12000" placeholder="Ces lignes restent une référence, hors calcul des besoins."></textarea></label><p class="hint">Seules les lignes avec un ingrédient, une quantité et une unité entrent dans les besoins.</p></template>
      <datalist id="locations"><option>Placard</option><option>Réfrigérateur</option><option>Congélateur</option></datalist>
      <footer><button type="button" class="secondary" @click="close" :disabled="busy">{{ draft.prepared && modal === 'meal' ? 'Fermer' : 'Annuler' }}</button><button v-if="!(draft.prepared && modal === 'meal')" class="primary" :disabled="busy || !online || ((modal === 'stock' || modal === 'manual') && !draft.ingredient_id)">{{ busy ? 'Enregistrement…' : modal === 'prepare' ? 'Confirmer la préparation' : modal === 'purchase' ? 'Confirmer les achats' : 'Enregistrer' }}</button></footer>
    </form>
  </dialog>
</template>
