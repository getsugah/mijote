<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { api, type Ingredient } from './api'
const props = defineProps<{ name: string; dimension: string; disabled?: boolean }>()
const emit = defineEmits<{ reuse: [id: number]; distinct: []; unauthorized: [] }>()
const candidates = ref<Ingredient[]>([]), exact = ref(false), error = ref('')
let timer: ReturnType<typeof setTimeout> | undefined, sequence = 0
async function check() {
  const current = ++sequence
  candidates.value = []; error.value = ''
  if (!props.name.trim()) return
  try {
    const result = await api<{ exact: Ingredient[]; suggestions: Ingredient[] }>(`/ingredients/matches?name=${encodeURIComponent(props.name.trim())}&dimension=${props.dimension}`)
    if (current !== sequence) return
    exact.value = !!result.exact.length
    candidates.value = exact.value ? result.exact : result.suggestions
  } catch (e: any) { if (current === sequence) { error.value = e.message; if (e.status === 401) emit('unauthorized') } }
}
watch(() => [props.name, props.dimension], () => { sequence++; candidates.value = []; clearTimeout(timer); timer = setTimeout(check, 250) }, { immediate: true })
onUnmounted(() => { sequence++; clearTimeout(timer) })
</script>
<template>
  <div v-if="candidates.length" class="ingredient-suggestions" role="status">
    <p>{{ exact ? 'Ce nom existe déjà dans votre répertoire.' : 'Un nom proche existe. S’agit-il du même aliment ?' }}</p>
    <div class="comfort-actions"><button v-for="candidate in candidates" :key="candidate.id" type="button" class="secondary small" @click="emit('reuse', candidate.id)" :disabled="disabled || candidate.dimension !== dimension">Utiliser « {{ candidate.name }} »</button><button v-if="!exact" type="button" class="text-button" @click="emit('distinct')" :disabled="disabled">Créer un ingrédient distinct</button></div>
    <small>Une correspondance confirmée sera reconnue aux prochains imports.</small>
  </div>
  <p v-if="error" class="hint" role="alert">{{ error }}</p>
</template>
