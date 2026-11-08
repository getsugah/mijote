<script setup lang="ts">
import type { Meal } from './api'
import { holidayName, mealPrintContent } from './calendar'

const props = defineProps<{ dates: string[]; meals: Meal[] }>()
const slots = [{ id: 'midi', label: 'Midi' }, { id: 'soir', label: 'Soir' }]
function label(day: string, options: Intl.DateTimeFormatOptions) {
  return new Date(day + 'T12:00:00').toLocaleDateString('fr-FR', options)
}
function content(day: string, slot: string) {
  return mealPrintContent(props.meals.find(meal => meal.day === day && meal.slot === slot))
}
</script>

<template>
  <section class="print-sheet" aria-label="Menu hebdomadaire pour l’impression">
    <header class="print-heading"><div><span class="print-brand">mijote.</span><h1>Le menu de la semaine</h1></div><p>Du {{ label(dates[0]!, { day: 'numeric', month: 'long', year: 'numeric' }) }}<br>au {{ label(dates[6]!, { day: 'numeric', month: 'long', year: 'numeric' }) }}</p></header>
    <table class="print-menu"><caption class="sr-only">Menu des sept jours, midi et soir</caption><thead><tr><th scope="col">Repas</th><th v-for="day in dates" :key="day" scope="col" :class="{ 'print-holiday': !!holidayName(day) }"><strong>{{ label(day, { weekday: 'long' }) }}</strong><span>{{ label(day, { day: 'numeric', month: 'short' }) }}</span><small v-if="holidayName(day)">Férié · {{ holidayName(day) }}</small></th></tr></thead><tbody><tr v-for="slot in slots" :key="slot.id"><th scope="row">{{ slot.label }}</th><td v-for="day in dates" :key="day"><strong>{{ content(day, slot.id).title }}</strong><span v-if="content(day, slot.id).side" class="print-side">+ {{ content(day, slot.id).side }}</span><small>{{ content(day, slot.id).detail }}</small><em v-if="content(day, slot.id).prepared">Préparé</em></td></tr></tbody></table>
    <footer class="print-footer">Bon appétit ! <span>Jours fériés nationaux · France</span></footer>
  </section>
</template>
