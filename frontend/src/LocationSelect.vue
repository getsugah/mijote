<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from './api'
const props = defineProps<{ modelValue: string; options: string[]; disabled?: boolean; all?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: string]; created: [name: string] }>()
const busy = ref(false), error = ref('')
const selected = computed({ get: () => props.modelValue, set: (value: string) => emit('update:modelValue', value) })
const choices = computed(() => [...new Set([...props.options, ...(props.modelValue ? [props.modelValue] : [])])])
async function create() {
  const name = window.prompt('Nom du nouvel emplacement :')?.trim()
  if (!name) return
  busy.value = true; error.value = ''
  try {
    const result = await api<{ name: string }>('/locations', 'POST', { name })
    emit('update:modelValue', result.name); emit('created', result.name)
  } catch (e) { error.value = e instanceof Error ? e.message : 'Emplacement non créé.' }
  finally { busy.value = false }
}
</script>
<template>
  <div class="location-choice">
    <label>Emplacement<select v-model="selected" :required="!all" :disabled="disabled || busy"><option v-if="all" value="">Tous les emplacements</option><option v-for="name in choices" :key="name" :value="name">{{ name }}</option></select></label>
    <button type="button" class="text-button" :disabled="disabled || busy" @click="create">{{ busy ? 'Création…' : '+ Nouvel emplacement' }}</button>
    <p v-if="error" role="alert" class="hint">{{ error }}</p>
  </div>
</template>
