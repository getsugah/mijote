<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api, photoUrl, uploadPhoto, type Recipe } from './api'
const props = defineProps<{ recipe: Recipe }>()
const emit = defineEmits<{ close: []; changed: []; unauthorized: [] }>()
const dialog = ref<HTMLDialogElement | null>(null), busy = ref(false), error = ref(''), notice = ref('')
const file = ref<File | null>(null), local = ref(''), remote = ref<any>(null)
const preview = computed(() => local.value || (remote.value ? 'data:image/jpeg;base64,' + remote.value.data_base64 : props.recipe.photo_version ? photoUrl(props.recipe) : ''))
const credit = computed(() => file.value ? '' : remote.value?.attribution || props.recipe.photo_attribution || '')
const source = computed(() => file.value ? '' : remote.value?.source_url || props.recipe.photo_source || '')
async function run(action: () => Promise<void>) { if (busy.value) return; busy.value = true; error.value = ''; notice.value = ''; try { await action() } catch (e: any) { error.value = e.message; if (e.status === 401) emit('unauthorized') } finally { busy.value = false } }
async function choose(event: Event) {
  const input = event.target as HTMLInputElement, selected = input.files?.[0]; if (!selected) return
  await run(async () => {
    if (selected.size > 12*1024*1024) throw new Error('Choisir une photo de 12 Mio maximum.')
    if (selected.type && !['image/jpeg','image/png','image/webp'].includes(selected.type)) throw new Error('Choisir une photo JPEG, PNG ou WebP. Les fichiers HEIC ne sont pas pris en charge.')
    const value = await new Promise<string>((resolve,reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Lecture de la photo impossible.')); reader.readAsDataURL(selected) })
    local.value = value; file.value = selected; remote.value = null
  }); input.value = ''
}
async function fromSite() { await run(async () => {
  const recipe = await api('/recipes/import/preview','POST',{ mode:'url',url:props.recipe.source_url,text:'' })
  if (!recipe.image_url) throw new Error('Aucune photo indiquée par ce site. Vous pouvez choisir une photo sur votre appareil.')
  const value = await api('/recipes/import/photo/preview','POST',{ url:recipe.image_url,attribution:recipe.image_author || recipe.source_author || '' })
  remote.value = { data_base64:value.data_base64,source_url:value.source_url,attribution:value.attribution }; file.value = null; local.value = ''
}) }
async function save() { await run(async () => {
  if (file.value) await uploadPhoto(props.recipe.id,file.value)
  else if (remote.value) await api(`/recipes/${props.recipe.id}/photo/confirm`,'PUT',remote.value)
  else return
  local.value = ''; file.value = null; remote.value = null; emit('changed'); notice.value = 'Photo enregistrée et incluse dans les sauvegardes de Mijote.'
}) }
async function remove() { if (!window.confirm('Retirer la photo de cette recette ? La recette sera conservée.')) return; await run(async () => { await api(`/recipes/${props.recipe.id}/photo`,'DELETE'); local.value = ''; file.value = null; remote.value = null; emit('changed'); notice.value = 'Photo retirée.' }) }
onMounted(() => dialog.value?.showModal()); onUnmounted(() => dialog.value?.close())
</script>
<template>
  <dialog ref="dialog" class="photo-dialog" aria-labelledby="photo-title" @cancel.prevent="!busy && emit('close')" @click="($event.target === dialog) && !busy && emit('close')">
    <div class="dialog-form"><header><div><span class="eyebrow">MON CARNET EN IMAGES</span><h2 id="photo-title">Photo · {{ recipe.name }}</h2></div><button type="button" class="icon-button" @click="emit('close')" :disabled="busy" aria-label="Fermer">×</button></header>
      <p v-if="error" class="alert error" role="alert">{{ error }}</p><p v-if="notice" class="alert success" role="status">{{ notice }}</p>
      <img v-if="preview" :src="preview" :alt="`Aperçu de ${recipe.name}`" class="photo-preview"><p v-else class="inline-help">Cette recette n’a pas encore de photo.</p>
      <p v-if="credit || source" class="photo-credit"><span v-if="credit">{{ credit }} · </span><a v-if="source" :href="source" target="_blank" rel="noopener noreferrer">Source de la photo</a></p>
      <label>Choisir une photo<input type="file" accept="image/jpeg,image/png,image/webp" @change="choose" :disabled="busy"></label><p class="hint">JPEG, PNG ou WebP · 12 Mio et 24 mégapixels maximum. La photo sera réduite et ses métadonnées retirées.</p>
      <button v-if="recipe.source_url" type="button" class="secondary" @click="fromSite" :disabled="busy">Proposer la photo du site source</button>
      <label v-if="remote" class="photo-credit-edit">Attribution fournie par le site<input v-model="remote.attribution" maxlength="300" :disabled="busy"></label>
      <p v-if="file || remote" class="hint">Vérifiez l’aperçu puis conservez la photo. Fermer abandonne ce choix.</p>
      <footer><button v-if="recipe.photo_version" type="button" class="text-button" @click="remove" :disabled="busy">Retirer la photo</button><button type="button" class="secondary" @click="emit('close')" :disabled="busy">Fermer</button><button type="button" class="primary" @click="save" :disabled="busy || (!file && !remote)">{{ busy ? 'Traitement…' : 'Conserver cette photo' }}</button></footer>
    </div>
  </dialog>
</template>
