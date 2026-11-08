<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api, type Dashboard, type Recipe } from './api'

const props = defineProps<{ section: 'ideas' | 'history' | 'copy' | 'preferences'; data: Dashboard; recipe?: Recipe }>()
const emit = defineEmits<{ changed: []; unauthorized: []; importWeb: [url: string] }>()
const busy = ref(false), error = ref(''), notice = ref('')
const mode = ref('varier'), ideas = ref<any[]>([]), excluded = ref<number[]>([])
interface WebIdea { name: string; url: string; source: string }
const webIdea = ref<WebIdea | null>(null), webSeen = ref<string[]>([]), webMessage = ref(''), webRequested = ref(false), webBusy = ref(false)
const events = ref<any[]>([]), cursor = ref<number | null>(null), target = ref(0)
const source = ref(''), preview = ref<any>(null), preferences = ref<any>({})
const ratings = { '': 'Pas encore d’avis', a_refaire: 'À refaire', pas_mal: 'Pas mal', a_ameliorer: 'À améliorer', ne_plus_proposer: 'Ne plus proposer' }
const categories = { autre: 'Autre', viande: 'Viande', poisson: 'Poisson', legumes: 'Légumes', vegetarien: 'Végétarien', feculents: 'Féculents', dessert: 'Dessert' }
const empty = computed(() => props.data.week.meals.filter(m => m.status === 'maison' && !m.prepared && !m.title && !m.recipe_id && !m.side_id))
const selected = computed(() => empty.value.find(m => m.id === target.value))
function uuid() { const b = crypto.getRandomValues(new Uint8Array(16)); b[6] = (b[6]! & 15) | 64; b[8] = (b[8]! & 63) | 128; const s = Array.from(b, x => x.toString(16).padStart(2, '0')).join(''); return `${s.slice(0,8)}-${s.slice(8,12)}-${s.slice(12,16)}-${s.slice(16,20)}-${s.slice(20)}` }
async function run(action: () => Promise<void>) { if (busy.value) return; busy.value = true; error.value = ''; notice.value = ''; try { await action() } catch (e: any) { error.value = e.message; if (e.status === 401) emit('unauthorized') } finally { busy.value = false } }
async function suggestions(reset = false) { await run(async () => { if (reset) excluded.value = []; ideas.value = (await api(`/suggestions?day=${selected.value?.day || props.data.week.start}&mode=${mode.value}&portions=${selected.value?.portions || props.data.settings.portions}&exclude=${excluded.value.join(',')}`)).items }) }
async function another() { excluded.value.push(...ideas.value.map(i => i.recipe_id)); await suggestions() }
function importWeb() { if (webIdea.value && !busy.value) emit('importWeb', webIdea.value.url) }
async function discoverWeb(reset = false) {
  await run(async () => {
    if (reset) webSeen.value = []
    webBusy.value = true
    try {
      const result = await api<{ item: WebIdea | null; message: string }>('/suggestions/web', 'POST', { exclude: webSeen.value })
      webRequested.value = true; webIdea.value = result.item; webMessage.value = result.message
      if (result.item) webSeen.value = [...webSeen.value, result.item.url].slice(-100)
    } finally { webBusy.value = false }
  })
}
async function history(more = false) { await run(async () => { const result = await api(`/history?limit=30${more && cursor.value ? `&before=${cursor.value}` : ''}`); events.value = more ? [...events.value, ...result.items] : result.items; cursor.value = result.next_before }) }
async function plan(recipeId: number) { await run(async () => { await api(`/meals/${target.value}/suggestion`, 'POST', { operation_id: uuid(), recipe_id: recipeId }); emit('changed'); notice.value = 'Recette ajoutée au créneau choisi. Aucun stock consommé.' }) }
async function reuse(id: number) { await run(async () => { await api(`/meals/${target.value}/reuse`, 'POST', { operation_id: uuid(), source_meal_id: id }); emit('changed'); notice.value = 'Repas replanifié. Sa préparation passée n’a pas été recopiée.' }) }
async function copyPreview() { await run(async () => { preview.value = null; preview.value = await api(`/weeks/${props.data.week.start}/copy-preview?source_start=${source.value}`) }) }
async function copy() { await run(async () => { const result = await api(`/weeks/${props.data.week.start}/copy`, 'POST', { operation_id: uuid(), source_start: source.value, preview_token: preview.value.preview_token }); preview.value = null; emit('changed'); notice.value = `${result.copied} repas copié(s).` }) }
async function savePreferences() { await run(async () => { await api(`/recipes/${props.recipe!.id}/preferences`, 'PATCH', preferences.value); emit('changed'); notice.value = 'Avis et préférences enregistrés.' }) }
watch(empty, value => { if (!value.some(m => m.id === target.value)) target.value = value[0]?.id || 0 }, { immediate: true })
watch(() => [props.section, props.recipe?.id, props.data.week.start], () => {
  error.value = ''; notice.value = ''; preview.value = null
  if (props.section === 'preferences' && props.recipe) { const r: any = props.recipe; preferences.value = { favorite: !!r.favorite, to_try: !!r.to_try, rating: r.rating || '', category: r.category || 'autre', comment: r.comment || '', variant: r.variant || '' } }
  if (props.section === 'history') void history()
  if (props.section === 'ideas') void suggestions(true)
}, { immediate: true })

watch(target, () => { if (props.section === 'ideas') void suggestions(true) })
</script>

<template>
  <section class="comfort-panel" :aria-busy="busy">
    <p v-if="error" class="alert error" role="alert">{{ error }}</p><p v-if="notice" class="alert success" role="status">{{ notice }}</p>
    <template v-if="section === 'preferences' && recipe">
      <h3>Mon avis · {{ recipe.name }}</h3>
      <form @submit.prevent="savePreferences" class="comfort-form"><div class="comfort-actions"><label class="check-label"><input type="checkbox" v-model="preferences.favorite">Favori</label><label class="check-label"><input type="checkbox" v-model="preferences.to_try">À tester</label></div>
        <div class="form-row"><label>Appréciation<select v-model="preferences.rating"><option v-for="(label, key) in ratings" :key="key" :value="key">{{ label }}</option></select></label><label>Catégorie<select v-model="preferences.category"><option v-for="(label, key) in categories" :key="key" :value="key">{{ label }}</option></select></label></div>
        <label>Commentaire<textarea v-model="preferences.comment" maxlength="4000" rows="3"></textarea></label><label>Ma variante<textarea v-model="preferences.variant" maxlength="12000" rows="3"></textarea><small>Une note personnelle : les ingrédients calculés restent ceux de la recette.</small></label><button class="secondary" :disabled="busy">Enregistrer mon avis</button>
      </form>
    </template>
    <template v-else-if="section === 'copy'">
      <h3>Réutiliser une semaine</h3><p>Seuls les créneaux maison vides de la semaine affichée seront remplis. Les présences et les repas existants sont conservés.</p>
      <form @submit.prevent="copyPreview" class="comfort-actions"><label>Lundi de la semaine source<input type="date" v-model="source" required @input="preview = null"></label><button class="secondary" :disabled="busy || !source">Voir l’aperçu</button></form>
      <div v-if="preview"><ul><li v-for="item in preview.items" :key="item.target_id">{{ item.day }} · {{ item.slot }} : {{ item.title }} <span v-if="item.side_name">+ {{ item.side_name }}</span> · {{ item.portions }} portions</li></ul><p>{{ preview.items.length }} repas à copier · {{ preview.skipped }} créneaux ignorés.</p><button class="primary" @click="copy" :disabled="busy || !preview.items.length">Confirmer la copie</button></div>
    </template>
    <template v-else>
      <h3>{{ section === 'ideas' ? 'Une idée pour le prochain repas ?' : 'Les repas préparés' }}</h3>
      <p>{{ section === 'ideas' ? 'Des suggestions issues de votre carnet, avec les réserves libres et vos préparations passées.' : 'Cet historique commence à la confirmation « Repas préparé », jamais à la simple planification.' }}</p>
      <label>Replanifier dans un créneau maison vide<select v-model.number="target" :disabled="busy"><option :value="0">Choisir un créneau</option><option v-for="m in empty" :key="m.id" :value="m.id">{{ m.day }} · {{ m.slot }} · {{ m.portions }} portions</option></select></label><p v-if="!empty.length" class="hint">Aucun créneau maison vide dans la semaine affichée.</p>
      <template v-if="section === 'ideas'"><div class="comfort-actions"><label>Envie de…<select v-model="mode" @change="suggestions(true)"><option value="varier">Varier</option><option value="stock">Utiliser le stock</option><option value="rapide">Cuisiner rapidement</option><option value="decouverte">Découvrir</option></select></label><button class="secondary" @click="suggestions(true)" :disabled="busy">Actualiser</button><button class="secondary" @click="another" :disabled="busy || !ideas.length">Une autre idée</button></div><div class="comfort-grid"><article v-for="idea in ideas" :key="idea.recipe_id" class="comfort-card"><h4>{{ idea.name }}</h4><ul><li v-for="reason in idea.reasons" :key="reason">{{ reason }}</li></ul><button class="secondary small" @click="plan(idea.recipe_id)" :disabled="busy || !selected">Ajouter au créneau choisi</button></article></div><p v-if="!busy && !ideas.length">Aucune autre suggestion. <button class="text-button" @click="suggestions(true)">Revoir toutes les idées</button></p>
        <section class="web-discovery" aria-labelledby="web-discovery-title">
          <h4 id="web-discovery-title">Une découverte sur le web</h4>
          <p>Une recette au hasard parmi les dernières publications du Journal des Femmes Cuisine. Rien n’est ajouté à votre carnet ni aux courses sans votre validation.</p>
          <button class="secondary" @click="discoverWeb()" :disabled="busy || (webRequested && !webIdea)">{{ webRequested ? 'Une autre idée sur le web' : 'Découvrir un plat sur le web' }}</button>
          <p v-if="webBusy" role="status">Recherche en cours…</p>
          <article v-if="webIdea" class="comfort-card web-idea" aria-live="polite">
            <h4>{{ webIdea.name }}</h4><p>Source : {{ webIdea.source }}</p>
            <div class="comfort-actions"><a class="secondary small" :href="webIdea.url" target="_blank" rel="noopener noreferrer">Voir la recette sur le site</a><button class="primary small" @click="importWeb" :disabled="busy">Importer cette recette</button></div>
          </article>
          <p v-if="webMessage" role="status">{{ webMessage }} <button class="text-button" @click="discoverWeb(true)" :disabled="busy">Revoir les idées web</button></p>
          <p class="hint">Ces découvertes ne tiennent pas compte de vos réserves ni de vos préférences. Une connexion Internet est nécessaire ; certains sites peuvent refuser l’import.</p>
        </section>
      </template>
      <template v-else><article v-for="event in events" :key="event.meal_id" class="comfort-card"><h4>{{ event.main_name }} <small v-if="event.side_name">+ {{ event.side_name }}</small></h4><p>{{ event.portions }} portions · prévu le {{ event.planned_day }} {{ event.slot }}<br>{{ event.prepared_at ? `Confirmé le ${new Date(event.prepared_at).toLocaleString('fr-FR')}` : 'Ancien repas préparé : date de confirmation inconnue' }}</p><button class="secondary small" @click="reuse(event.meal_id)" :disabled="busy || !selected">Replanifier ce repas</button></article><p v-if="!events.length && !busy">Aucun repas confirmé pour le moment.</p><button v-if="cursor" class="secondary" @click="history(true)" :disabled="busy">Afficher les précédents</button></template>
    </template>
  </section>
</template>
