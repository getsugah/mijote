<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api, ApiError, baseUnit, units, type Ingredient, type Unit } from './api'
import Icon from './Icon.vue'
import IngredientSuggestions from './IngredientSuggestions.vue'

interface Suggestion { raw: string; name: string; quantity: number | null; unit: Unit | null; needs_review: boolean }
interface Preview { image_url?: string; image_author?: string; name: string; portions: number | null; yield_text: string; minutes: number | null; steps: string; source_url: string; source_author: string; ingredient_notes: string; ingredients: Suggestion[]; warnings: string[]; method: string }
interface ImportRow { allow_distinct?: boolean; key: number; raw: string; name: string; ingredient_id: number | null; quantity: number | null; unit: Unit | ''; include: boolean }
const props = defineProps<{ ingredients: Ingredient[]; initial?: { url: string; text: string; message: string } | null }>()
const emit = defineEmits<{ close: []; saved: [id: number]; unauthorized: [] }>()
const dialog = ref<HTMLDialogElement | null>(null), busy = ref(false), error = ref('')
const mode = ref<'url' | 'text'>(props.initial && !props.initial.url ? 'text' : 'url'), url = ref(props.initial?.url || ''), pasted = ref(props.initial?.text || ''), preview = ref<Preview | null>(null), rows = ref<ImportRow[]>([])
const confirmed = ref(false)
const confirmationId = ref('')
const photo = ref<{ data_base64: string; source_url: string; attribution: string } | null>(null), keepPhoto = ref(false), photoWarning = ref('')
async function loadPhoto() {
  photo.value = null; keepPhoto.value = false; photoWarning.value = ''
  if (!preview.value?.image_url) return
  try { const value = await api('/recipes/import/photo/preview', 'POST', { url: preview.value.image_url, attribution: preview.value.image_author || preview.value.source_author || '' }); photo.value = { data_base64: value.data_base64, source_url: value.source_url, attribution: value.attribution }; keepPhoto.value = true }
  catch (e) { if (e instanceof ApiError && e.status === 401) handleError(e); else photoWarning.value = 'Photo indisponible. Vous pouvez enregistrer la recette sans photo et en ajouter une depuis votre appareil.' }
}
async function retryPhoto() { if (busy.value) return; busy.value = true; try { await loadPhoto() } finally { busy.value = false } }
let nextKey = 0
const selected = computed(() => rows.value.filter(row => row.include).length)
function normalized(value: string) { return value.normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('fr') }
function findIngredient(id: number | null) { return props.ingredients.find(i => i.id === id) }
function unitLabel(unit: string) { return unit === 'piece' ? 'pièce(s)' : unit }
function allowedUnits(row: ImportRow): Unit[] { return row.ingredient_id ? units(findIngredient(row.ingredient_id)) : ['g', 'kg', 'ml', 'l', 'piece'] }
function handleError(value: unknown) {
  if (value instanceof ApiError && value.status === 401) { emit('unauthorized'); return }
  error.value = value instanceof Error ? value.message : 'L’import n’a pas abouti.'
}
function changeIngredient(row: ImportRow) {
  const value = findIngredient(row.ingredient_id)
  if (value) { row.name = value.name; row.unit = baseUnit(value) }
}
function useIngredient(row: ImportRow, id: number) { row.ingredient_id = id; if (!units(findIngredient(id)).includes(row.unit as Unit)) row.unit = baseUnit(findIngredient(id)) }
function addRow() { rows.value.push({ key: nextKey++, raw: '', name: '', ingredient_id: null, quantity: null, unit: '', include: true }) }
function operationId() {
  if (crypto.randomUUID) return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6]! & 15) | 64; bytes[8] = (bytes[8]! & 63) | 128
  const value = Array.from(bytes, x => x.toString(16).padStart(2, '0')).join('')
  return `${value.slice(0,8)}-${value.slice(8,12)}-${value.slice(12,16)}-${value.slice(16,20)}-${value.slice(20)}`
}
async function analyze() {
  if (busy.value) return
  busy.value = true; error.value = ''; confirmed.value = false
  try {
    const result = await api<Preview>('/recipes/import/preview', 'POST', { mode: mode.value, url: url.value, text: pasted.value })
    preview.value = result
    photo.value = null; keepPhoto.value = false; photoWarning.value = ''
    confirmationId.value = operationId()
    rows.value = result.ingredients.map(line => {
      const match = props.ingredients.find(i => [i.name, ...(i.aliases || [])].some(name => normalized(name) === normalized(line.name)) && !!line.unit && units(i).includes(line.unit))
      return { key: nextKey++, raw: line.raw, name: line.name, ingredient_id: match?.id || null,
        quantity: line.quantity, unit: line.unit || '', include: !line.needs_review && !!line.quantity && !!line.unit && !!line.name }
    })
    await loadPhoto()
  } catch (value) { handleError(value) } finally { busy.value = false }
}
async function save() {
  if (busy.value || !preview.value || !confirmed.value) return
  busy.value = true; error.value = ''
  try {
    const p = preview.value
    const result = await api<{ id: number }>('/recipes/import/confirm', 'POST', { operation_id: confirmationId.value, recipe: {
      name: p.name, kind: 'recette', portions: Number(p.portions), minutes: Number(p.minutes), steps: p.steps,
      source_url: p.source_url, source_author: p.source_author, ingredient_notes: p.ingredient_notes, ingredients: [],
    }, ...(keepPhoto.value && photo.value ? { photo: photo.value } : {}), items: rows.value.filter(row => row.include).map(row => ({ ingredient_id: row.ingredient_id,
      name: row.name, quantity: Number(row.quantity), unit: row.unit, allow_distinct: !!row.allow_distinct })) })
    emit('saved', result.id)
  } catch (value) { handleError(value) } finally { busy.value = false }
}
onMounted(() => dialog.value?.showModal())
onUnmounted(() => dialog.value?.close())
</script>

<template>
  <dialog ref="dialog" class="import-dialog" aria-labelledby="import-title" @cancel.prevent="!busy && emit('close')" @click="($event.target === dialog) && !busy && emit('close')">
    <form class="dialog-form" @submit.prevent="preview ? save() : analyze()">
      <header><div><span class="eyebrow">DU WEB À VOTRE CARNET</span><h2 id="import-title">{{ preview ? 'Vérifier la recette' : 'Importer une recette' }}</h2></div><button type="button" class="icon-button" aria-label="Fermer" @click="emit('close')" :disabled="busy"><Icon name="close" /></button></header>
      <div v-if="error" role="alert" class="alert error">{{ error }}</div>
      <template v-if="!preview">
        <p v-if="initial" class="import-notice" role="status">{{ initial.message }}</p>
        <div class="import-tabs" role="group" aria-label="Méthode d’import"><button type="button" :class="{ selected: mode === 'url' }" @click="mode = 'url'" :disabled="busy">Depuis un lien</button><button type="button" :class="{ selected: mode === 'text' }" @click="mode = 'text'" :disabled="busy">Coller le texte</button></div>
        <p>Récupérez les informations d’une recette, puis vérifiez-les avant de l’enregistrer. Rien n’est ajouté aux réserves.</p>
        <label>{{ mode === 'url' ? 'Lien public de la recette' : 'Lien de la source (facultatif)' }}<input v-model="url" type="url" maxlength="2000" :required="mode === 'url'" placeholder="https://…" :disabled="busy"></label>
        <label v-if="mode === 'text'">Texte de la recette<textarea v-model="pasted" rows="12" maxlength="60000" required :disabled="busy" placeholder="Soupe maison&#10;Pour 4 personnes&#10;Ingrédients :&#10;500 g de légumes&#10;1 l d’eau&#10;Préparation :&#10;Couper les légumes et les cuire…"></textarea></label>
        <p class="hint">Certains sites protègent leur contenu ou demandent une connexion. Dans ce cas, le collage du texte reste disponible. Une photo proposée par le site pourra être prévisualisée avant de la conserver.</p>
      </template>
      <template v-else>
        <div class="import-notice"><strong>Une dernière vérification avant de cuisiner</strong><p>Seules les lignes cochées ci-dessous serviront aux besoins et aux déductions de stock. Les autres restent dans le texte d’origine.</p></div>
        <ul v-if="preview.warnings.length" class="import-warnings"><li v-for="(warning, index) in preview.warnings" :key="index">{{ warning }}</li></ul>
        <section v-if="preview.image_url" class="import-photo"><h3>Photo proposée par le site</h3><img v-if="photo" :src="'data:image/jpeg;base64,' + photo.data_base64" alt="Photo proposée pour la recette" class="photo-preview"><p v-if="photoWarning" class="hint" role="status">{{ photoWarning }}</p><template v-if="photo"><label class="check-label"><input v-model="keepPhoto" type="checkbox" :disabled="busy">Conserver cette photo avec la recette</label><label>Attribution fournie par le site<input v-model="photo.attribution" maxlength="300" :disabled="busy"></label><p class="photo-credit"><a :href="photo.source_url" target="_blank" rel="noopener noreferrer">Source de la photo</a></p></template><button v-else type="button" class="secondary small" @click="retryPhoto" :disabled="busy">Réessayer la photo</button></section>
        <label>Nom de la recette<input v-model="preview.name" required maxlength="120" :disabled="busy"></label>
        <div class="form-row"><label>Portions de référence<input v-model.number="preview.portions" type="number" min="1" max="30" required placeholder="À préciser" :disabled="busy"><small v-if="preview.yield_text">Source : {{ preview.yield_text }}</small></label><label>Temps total (minutes)<input v-model.number="preview.minutes" type="number" min="0" max="1440" required placeholder="0 si inconnu" :disabled="busy"></label></div>
        <h3>Ingrédients et quantités <small>{{ selected }} ligne(s) incluse(s)</small></h3>
        <p class="hint">Associez chaque ligne à votre répertoire ou corrigez son nom pour créer un nouvel ingrédient. Les mesures non reconnues ne sont pas converties automatiquement.</p>
        <article v-for="row in rows" :key="row.key" class="import-line" :class="{ excluded: !row.include }">
          <label class="check-label"><input v-model="row.include" type="checkbox" :disabled="busy"><strong>{{ row.raw || 'Nouvelle ligne' }}</strong><span>{{ row.include ? 'Dans les besoins' : 'Texte seulement' }}</span></label>
          <fieldset :disabled="busy || !row.include"><label>Dans le répertoire<select v-model="row.ingredient_id" @change="changeIngredient(row)"><option :value="null">Créer un nouvel ingrédient</option><option v-for="i in ingredients" :key="i.id" :value="i.id">{{ i.name }}</option></select></label>
            <label v-if="!row.ingredient_id">Nom à conserver<input v-model="row.name" required maxlength="120" placeholder="Ex. farine de blé"></label>
            <IngredientSuggestions v-if="!row.ingredient_id && row.unit && !row.allow_distinct" :name="row.name" :dimension="['g','kg'].includes(row.unit) ? 'masse' : row.unit === 'piece' ? 'piece' : 'volume'" :disabled="busy" @reuse="id => useIngredient(row, id)" @distinct="row.allow_distinct = true" @unauthorized="emit('unauthorized')" />
            <div class="form-row"><label>Quantité à utiliser<input v-model.number="row.quantity" type="number" min="0.001" step="0.001" required placeholder="À vérifier"></label><label>Unité<select v-model="row.unit" required><option value="" disabled>À choisir</option><option v-for="unit in allowedUnits(row)" :key="unit" :value="unit">{{ unitLabel(unit) }}</option></select></label></div>
          </fieldset><button type="button" class="text-button" @click="rows = rows.filter(r => r.key !== row.key)" :disabled="busy">Retirer cette ligne du calcul</button>
        </article>
        <button type="button" class="secondary small" @click="addRow" :disabled="busy"><Icon name="plus" :size="16" />Ajouter une ligne quantifiée</button>
        <label class="import-steps">Préparation<textarea v-model="preview.steps" rows="9" maxlength="20000" :disabled="busy" placeholder="Compléter les étapes si nécessaire…"></textarea></label>
        <details class="import-original"><summary>Texte d’origine des ingrédients (hors calcul)</summary><p class="hint">Ces lignes sont conservées comme référence. Elles ne sont pas additionnées aux lignes cochées.</p><textarea v-model="preview.ingredient_notes" rows="6" maxlength="12000" aria-label="Texte d’origine des ingrédients" :disabled="busy"></textarea></details>
        <div class="form-row"><label>Source<input v-model="preview.source_url" type="url" maxlength="2000" :disabled="busy"></label><label>Auteur ou attribution<input v-model="preview.source_author" maxlength="300" :disabled="busy"></label></div>
        <label class="check-label import-confirm"><input v-model="confirmed" type="checkbox" required :disabled="busy"><span>J’ai vérifié les portions, les ingrédients et les quantités incluses dans les besoins.</span></label>
      </template>
      <footer><button type="button" class="secondary" :disabled="busy" @click="preview ? (preview = null, error = '') : emit('close')">{{ preview ? 'Revenir à la source' : 'Annuler' }}</button><button class="primary" :disabled="busy || (preview !== null && !confirmed)">{{ busy ? preview ? 'Enregistrement…' : 'Lecture de la recette…' : preview ? 'Enregistrer la recette vérifiée' : 'Prévisualiser la recette' }}</button></footer>
    </form>
  </dialog>
</template>
