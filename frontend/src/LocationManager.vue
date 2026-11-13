<script setup lang="ts">
import { ref } from 'vue'
import { api } from './api'
const props = defineProps<{ options: string[]; disabled: boolean }>()
const emit = defineEmits<{ changed: []; unauthorized: [] }>()
const selected = ref(''), name = ref(''), destination = ref(''), busy = ref(false), error = ref('')
function select() { name.value = selected.value; destination.value = ''; error.value = '' }
async function save(remove = false) {
  if (busy.value || props.disabled) return
  if (remove && !window.confirm(`Supprimer « ${selected.value} » ? Tous ses articles seront déplacés vers « ${destination.value} », sans modifier les quantités.`)) return
  busy.value = true; error.value = ''
  try {
    await api(`/locations/${encodeURIComponent(selected.value)}`, remove ? 'DELETE' : 'PATCH', { name: remove ? destination.value : name.value })
    selected.value = ''; emit('changed')
  } catch (e: any) { error.value = e.message; if (e.status === 401) emit('unauthorized') }
  finally { busy.value = false }
}
</script>
<template>
  <details class="ingredient-panel location-manager">
    <summary>Gérer les emplacements</summary>
    <p>Renommez un emplacement ou supprimez-le en déplaçant ses articles vers un autre. Les quantités et l’historique sont conservés.</p>
    <p v-if="error" class="alert error" role="alert">{{ error }}</p>
    <fieldset :disabled="disabled || busy">
      <label>Emplacement à modifier<select v-model="selected" @change="select"><option value="">Choisir un emplacement</option><option v-for="item in options" :key="item">{{ item }}</option></select></label>
      <template v-if="selected">
        <form @submit.prevent="save()"><label>Nouveau nom<input v-model="name" maxlength="120" required></label><button class="secondary" :disabled="!name.trim()">Enregistrer le nom</button></form>
        <label>Déplacer les articles vers<select v-model="destination"><option value="">Choisir un autre emplacement</option><option v-for="item in options.filter(x => x !== selected)" :key="item">{{ item }}</option></select></label>
        <button type="button" class="secondary" :disabled="!destination" @click="save(true)">Supprimer cet emplacement</button>
        <p v-if="options.length < 2">Créez un autre emplacement avant de supprimer celui-ci.</p>
      </template>
    </fieldset>
  </details>
</template>
