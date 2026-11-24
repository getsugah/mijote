<script setup lang="ts">
import { computed, nextTick, onScopeDispose, ref, watch } from 'vue'
import { api, type PhotoDraft } from './api'
interface Advice { title: string; title_reason: string; tags: { name: string; reason: string }[]; message: string }
const props = defineProps<{ name: string; ingredients: string[]; minutes: number; sourceUrl?: string; modelValue?: string[]; photo?: PhotoDraft | null; existingPhoto?: boolean; disabled?: boolean; allowPhoto?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [tags: string[]]; name: [name: string]; photo: [photo: PhotoDraft | null]; unauthorized: [] }>()
const busy = ref(false), photoBusy = ref(false), error = ref(''), notice = ref(''), result = ref<Advice | null>(null)
const candidate = ref<PhotoDraft | null>(null), custom = ref('')
const tags = computed(() => props.modelValue || [])
const signature = computed(() => JSON.stringify([props.name, props.ingredients, props.minutes]))
let epoch = 0, alive = true
const key = (value: string) => value.normalize('NFKC').trim().replace(/\s+/g, ' ').toLocaleLowerCase('fr')
watch(signature, () => { epoch++; result.value = null; notice.value = '' })
watch(() => props.sourceUrl, () => { candidate.value = null })
onScopeDispose(() => { alive = false; epoch++ })
function fail(e: any) { error.value = e.message || 'Proposition indisponible.'; if (e.status === 401) emit('unauthorized') }
async function propose() {
  if (props.disabled || busy.value) return
  busy.value = true; error.value = ''; notice.value = ''; const current = ++epoch
  try {
    const response = await api<Advice>('/recipes/advice', 'POST', { name: props.name || '', ingredients: props.ingredients.filter(Boolean), minutes: Number(props.minutes) || 0 })
    if (alive && current === epoch) result.value = response
    else if (alive) notice.value = 'La recette a changé. Redemandez les propositions.'
  } catch (e) { if (alive && current === epoch) fail(e) }
  finally { if (alive) busy.value = false }
}
function addTag(value: string) {
  if (props.disabled) return
  const clean = value.normalize('NFKC').trim().replace(/\s+/g, ' ')
  if (!clean || clean.length > 50) { error.value = 'Un tag doit contenir entre 1 et 50 caractères.'; return }
  if (tags.value.some(t => key(t) === key(clean))) return
  if (tags.value.length >= 20) { error.value = 'Conserver au maximum 20 tags par recette.'; return }
  emit('update:modelValue', [...tags.value, clean]); custom.value = ''; error.value = ''
}
function removeTag(value: string) { if (!props.disabled) emit('update:modelValue', tags.value.filter(t => t !== value)) }
async function adoptTitle() {
  if (!result.value?.title || props.disabled) return
  const value = result.value; emit('name', value.title); await nextTick()
  if (alive) result.value = value
}
async function proposePhoto() {
  if (!props.sourceUrl || props.disabled || photoBusy.value) return
  photoBusy.value = true; error.value = ''; candidate.value = null
  const source = props.sourceUrl
  try {
    const preview = await api<{ image_url?: string; image_author?: string; source_author?: string }>('/recipes/import/preview', 'POST', { mode: 'url', url: source, text: '' })
    if (!alive || source !== props.sourceUrl) return
    if (!preview.image_url) throw new Error('Aucune photo proposée par cette source. Vous pouvez ajouter votre photo après l’enregistrement.')
    const photo = await api<PhotoDraft>('/recipes/import/photo/preview', 'POST', { url: preview.image_url, attribution: preview.image_author || preview.source_author || '' })
    if (alive && source === props.sourceUrl) candidate.value = { data_base64: photo.data_base64, source_url: photo.source_url, attribution: photo.attribution }
  } catch (e) { if (alive && source === props.sourceUrl) fail(e) }
  finally { if (alive) photoBusy.value = false }
}
function adoptPhoto() { if (candidate.value && !props.disabled) { emit('photo', { ...candidate.value }); candidate.value = null } }
</script>
<template>
  <section class="recipe-suggestions" aria-label="Tags et propositions à valider" :aria-busy="busy || photoBusy">
    <h3>Tags et propositions</h3><p class="hint">Les propositions ne sont conservées qu’après votre choix, puis l’enregistrement de la recette.</p>
    <p v-if="error" class="alert error" role="alert">{{ error }}</p><p v-if="notice" class="hint" role="status">{{ notice }}</p>
    <div class="recipe-tags" aria-label="Tags choisis"><span v-for="tag in tags" :key="tag">{{ tag }}<button type="button" @click="removeTag(tag)" :disabled="disabled" :aria-label="`Retirer le tag ${tag}`">×</button></span><small v-if="!tags.length">Aucun tag choisi.</small></div>
    <div class="tag-entry"><label>Ajouter un tag<input v-model="custom" maxlength="50" :disabled="disabled" @keydown.enter.prevent="addTag(custom)" placeholder="Ex. cuisine familiale"></label><button type="button" class="secondary small" @click="addTag(custom)" :disabled="disabled || !custom.trim()">Ajouter ce tag</button></div>
    <button type="button" class="secondary" @click="propose" :disabled="disabled || busy">{{ busy ? 'Recherche…' : 'Proposer un titre et des tags' }}</button>
    <div v-if="result" class="recipe-advice-results">
      <div v-if="result.title"><strong>Titre proposé : {{ result.title }}</strong><p class="hint">{{ result.title_reason }}</p><button type="button" class="secondary small" @click="adoptTitle" :disabled="disabled || result.title === name">Utiliser ce titre</button></div>
      <p class="hint">{{ result.message }}</p>
      <div class="tag-proposals"><button v-for="tag in result.tags" :key="tag.name" type="button" class="secondary small" :title="tag.reason" @click="addTag(tag.name)" :disabled="disabled || tags.some(t => key(t) === key(tag.name))">+ {{ tag.name }}</button></div><p v-if="!result.tags.length" class="hint">Aucun tag évident. Vous pouvez en saisir un vous-même.</p>
    </div>
    <template v-if="allowPhoto !== false">
      <button v-if="sourceUrl" type="button" class="secondary" @click="proposePhoto" :disabled="disabled || photoBusy">{{ photoBusy ? 'Lecture du site…' : 'Proposer la photo du site source' }}</button>
      <p v-else class="hint">Renseignez le lien de la recette pour proposer sa photo, ou ajoutez une photo depuis votre appareil après l’enregistrement.</p>
      <div v-if="candidate" class="photo-proposal"><img :src="'data:image/jpeg;base64,' + candidate.data_base64" alt="Photo proposée, non encore choisie" class="photo-preview"><label>Attribution<input v-model="candidate.attribution" maxlength="300" :disabled="disabled"></label><a :href="candidate.source_url" target="_blank" rel="noopener noreferrer">Source de la photo</a><div class="comfort-actions"><button type="button" class="secondary" @click="adoptPhoto" :disabled="disabled">Choisir cette photo</button><button type="button" class="text-button" @click="candidate = null" :disabled="disabled">Écarter cette photo</button></div></div>
      <div v-if="photo" class="photo-proposal"><img :src="'data:image/jpeg;base64,' + photo.data_base64" alt="Photo choisie pour le prochain enregistrement" class="photo-preview"><p class="hint">Cette photo sera enregistrée avec la recette.</p><button type="button" class="text-button" @click="emit('photo', null)" :disabled="disabled">Annuler ce choix de photo</button></div>
      <p v-else-if="existingPhoto" class="hint">La photo existante est conservée tant que vous n’en choisissez pas une autre.</p>
    </template>
  </section>
</template>
