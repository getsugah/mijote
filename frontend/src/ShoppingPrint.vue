<script setup lang="ts">
import type { Shopping } from './api'
const props = defineProps<{ start: string; items: Shopping[]; weeks?: string[] }>()
function label(offset: number) { const date = new Date(props.start + 'T12:00:00'); date.setDate(date.getDate() + offset); return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) }
function amount(value: number) { return Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 3 }) }
</script>
<template>
  <section class="print-sheet shopping-print" aria-label="Liste de courses pour l’impression">
    <header class="print-heading"><div><span class="print-brand">mijote.</span><h1>Ma liste de courses</h1></div><p v-if="weeks?.length">Semaines regroupées<br><span v-for="week in weeks" :key="week">{{ new Date(week + 'T12:00:00').toLocaleDateString('fr-FR') }}<br></span></p><p v-else>Du {{ label(0) }}<br>au {{ label(6) }}</p></header>
    <p class="shopping-print-note">Quantités manquantes après prise en compte des réserves, avec vos ajouts personnels. Les cases cochées indiquent les articles déjà dans le panier.</p>
    <table v-if="items.length" class="shopping-print-list"><thead><tr><th scope="col">Panier</th><th scope="col">Article</th><th scope="col">Quantité</th></tr></thead><tbody><tr v-for="item in items" :key="item.key"><td><span :aria-label="item.checked ? 'Dans le panier' : 'À acheter'">{{ item.checked ? '☑' : '☐' }}</span></td><td>{{ item.name }}<small v-if="item.manual_id">Ajout personnel</small></td><td>{{ amount(item.quantity) }} {{ item.unit === 'piece' ? 'pièce(s)' : item.unit }}</td></tr></tbody></table>
    <p v-else>Rien à acheter pour cette semaine.</p>
    <footer class="print-footer">Bonnes courses ! <span>La version papier ne synchronise pas les cases cochées.</span></footer>
  </section>
</template>
