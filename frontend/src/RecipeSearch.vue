<script setup lang="ts">
import { computed, onScopeDispose, ref, watch } from 'vue'
import { api, type PhotoDraft } from './api'
interface Match { id: string; title: string; image_url: string; category: string; area: string; tags: string[]; source_url: string; provider_url: string; provider: string; attribution: string; image_origin: string }
interface Search { items: Match[]; query_used: string; adapted: boolean; message: string }
const props = defineProps<{ name: string; ingredients?: string[]; tags?: string[]; photo?: PhotoDraft | null; disabled?: boolean }>()
const emit = defineEmits<{ name: [name: string]; photo: [photo: PhotoDraft | null]; tags: [tags: string[]]; unauthorized: [] }>()
const query = ref(props.name || props.ingredients?.[0] || ''), busy = ref(false), photoBusy = ref(false), searched = ref(false)
const error = ref(''), response = ref<Search | null>(null), candidate = ref<PhotoDraft | null>(null), candidateMeal = ref<Match | null>(null)
let epoch = 0, alive = true
watch(() => props.name, name => { if (!searched.value) query.value = name || props.ingredients?.[0] || '' })
watch(query, () => { epoch++; response.value = null; candidate.value = null; candidateMeal.value = null; error.value = '' })
onScopeDispose(() => { alive = false; epoch++ })
const chosenTags = computed(() => props.tags || [])
const key = (value: string) => value.normalize('NFKC').trim().toLocaleLowerCase('fr')
function fail(e: any) { error.value = e.message || 'Recherche indisponible. Votre recette est conservée.'; if (e.status === 401) emit('unauthorized') }
async function search() {
  if (busy.value || photoBusy.value || props.disabled || !query.value.trim()) return
  busy.value = true; searched.value = true; error.value = ''; candidate.value = null; candidateMeal.value = null
  const current = ++epoch
  try {
    const result = await api<Search>('/recipes/search/mealdb', 'POST', { query: query.value.trim() })
    if (alive && current === epoch) response.value = result
  } catch (e) { if (alive && current === epoch) fail(e) }
  finally { if (alive) busy.value = false }
}
function chooseTitle(item: Match) { if (!props.disabled) emit('name', item.title) }
function chooseTag(name: string) {
  if (props.disabled || chosenTags.value.some(t => key(t) === key(name))) return
  if (chosenTags.value.length >= 20) { error.value = 'Conserver au maximum 20 tags par recette.'; return }
  emit('tags', [...chosenTags.value, name])
}
async function preview(item: Match) {
  if (props.disabled || photoBusy.value || busy.value) return
  photoBusy.value = true; error.value = ''; candidate.value = null; candidateMeal.value = null
  const current = ++epoch
  try {
    const photo = await api<PhotoDraft>('/recipes/search/mealdb/photo', 'POST', { meal_id: item.id })
    if (alive && current === epoch) { candidate.value = photo; candidateMeal.value = item }
  } catch (e) { if (alive && current === epoch) fail(e) }
  finally { if (alive) photoBusy.value = false }
}
function adopt(withTitle = true) {
  if (props.disabled || !candidate.value || !candidateMeal.value) return
  if (withTitle) emit('name', candidateMeal.value.title)
  emit('photo', { ...candidate.value }); candidate.value = null; candidateMeal.value = null
}
</script>
<template>
  <section class="recipe-search" aria-label="Proposer des titres et photos de plats" :aria-busy="busy || photoBusy">
    <h3>Un titre et sa photo</h3>
    <p class="hint">Recherchez des plats dans TheMealDB, puis choisissez un titre et sa photo, ou seulement la photo. Vos ingrédients et quantités restent conservés.</p>
    <div class="tag-entry"><label>Nom ou idée du plat<input v-model="query" maxlength="120" placeholder="Ex. poulet au curry" :disabled="disabled" @keydown.enter.prevent="search"></label><button type="button" class="secondary" @click="search" :disabled="disabled || busy || photoBusy || !query.trim()">{{ busy ? 'Recherche…' : 'Proposer des titres avec photo' }}</button></div>
    <p class="hint">Recherche externe : seul le texte recherché est envoyé à TheMealDB. Des noms français courants sont adaptés ; vous pouvez aussi chercher en anglais.</p>
    <p v-if="error" class="alert error" role="alert">{{ error }}</p>
    <template v-if="response"><p class="hint" role="status">{{ response.message }}<span v-if="response.adapted"> Recherche utilisée : « {{ response.query_used }} ».</span></p>
      <div class="recipe-search-results"><article v-for="item in response.items" :key="item.id" class="recipe-search-card">
        <img v-if="item.image_url" :src="item.image_url" alt="" loading="lazy" referrerpolicy="no-referrer"><span v-else class="recipe-search-no-photo">Sans photo</span>
        <div class="recipe-search-body"><h4>{{ item.title }}</h4><p>{{ item.category }}<span v-if="item.area"> · {{ item.area }}</span></p><p class="hint">Titre original de la source</p><a :href="item.provider_url" target="_blank" rel="noopener noreferrer">Voir sur TheMealDB</a><a v-if="item.source_url" :href="item.source_url" target="_blank" rel="noopener noreferrer">Recette d’origine</a>
          <div v-if="item.tags.length" class="tag-proposals"><button v-for="tag in item.tags" :key="tag" type="button" class="secondary small" @click="chooseTag(tag)" :disabled="disabled || chosenTags.some(t => key(t) === key(tag))">+ {{ tag }}</button></div>
        </div><div class="recipe-search-actions"><button type="button" class="secondary small" @click="chooseTitle(item)" :disabled="disabled || item.title === name">Utiliser ce titre</button><button v-if="item.image_url" type="button" class="secondary small" @click="preview(item)" :disabled="disabled || photoBusy || busy">{{ photoBusy ? 'Photo en cours…' : 'Prévisualiser le titre et sa photo' }}</button></div>
      </article></div>
    </template>
    <div v-if="candidate && candidateMeal" class="photo-proposal"><h4>{{ candidateMeal.title }}</h4><img :src="'data:image/jpeg;base64,' + candidate.data_base64" alt="Photo proposée pour le titre sélectionné" class="photo-preview"><label>Attribution conservée avec la photo<input v-model="candidate.attribution" maxlength="300" :disabled="disabled"></label><a :href="candidateMeal.provider_url" target="_blank" rel="noopener noreferrer">Source : TheMealDB</a><p class="hint">La photo illustre la recette trouvée, qui peut différer de votre version. L’enregistrement final reste nécessaire.</p><div class="comfort-actions"><button type="button" class="secondary" @click="adopt()" :disabled="disabled">Choisir ce titre et cette photo</button><button type="button" class="secondary" @click="adopt(false)" :disabled="disabled">Garder mon titre, choisir la photo</button><button type="button" class="text-button" @click="candidate = null; candidateMeal = null" :disabled="disabled">Écarter</button></div></div>
    <div v-if="photo" class="photo-proposal"><strong>Photo choisie pour l’enregistrement</strong><img :src="'data:image/jpeg;base64,' + photo.data_base64" alt="Photo choisie, pas encore enregistrée" class="photo-preview"><p class="hint">{{ photo.attribution }}</p><button type="button" class="text-button" @click="emit('photo', null)" :disabled="disabled">Annuler le choix de photo</button></div>
  </section>
</template>
