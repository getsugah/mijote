<script setup lang="ts">
import { computed } from 'vue'
import type { Meal, Recipe } from './api'
import { mealGroups, hasMealFood } from './mealItems'
import { primaryMealRecipe } from './mealPresentation'
import { holidayName } from './calendar'
import Icon from './Icon.vue'
import MealPhoto from './MealPhoto.vue'
const props = defineProps<{ dates: string[]; meals: Meal[]; recipes: Recipe[]; selectedId: number | null; busy: boolean; online: boolean }>()
const emit = defineEmits<{ select: [id: number]; edit: [meal: Meal]; choose: [meal: Meal]; prepare: [meal: Meal]; favorite: [recipe: Recipe]; ideas: []; copy: [] }>()
const slots = [{ id: 'midi', label: 'Midi', icon: 'sun' }, { id: 'soir', label: 'Soir', icon: 'moon' }]
const selected = computed(() => props.meals.find(m => m.id === props.selectedId && props.dates.includes(m.day)) || props.meals.find(m => props.dates.includes(m.day)))
const selectedRecipe = computed(() => primaryMealRecipe(selected.value, props.recipes))
const today = new Date().toLocaleDateString('sv-SE')
function meal(day: string, slot: string) { return props.meals.find(m => m.day === day && m.slot === slot) }
function dateLabel(day: string, short = false) { return new Date(day + 'T12:00:00').toLocaleDateString('fr-FR', { weekday: short ? 'short' : 'long', day: 'numeric', ...(short ? {} : { month: 'long' }) }) }
function status(value?: Meal) { return ({ maison: 'À la maison', travail: 'Au travail', exterieur: 'À l’extérieur', a_decider: 'À décider' })[value?.status || 'a_decider'] }
function groups(value?: Meal) { return value?.status === 'maison' ? mealGroups(value) : [] }
function accessible(value: Meal | undefined, day: string, label: string) { return `${dateLabel(day)} · ${label} : ${groups(value).map(g => g.names.join(', ')).join(' · ') || status(value)}` }
function select(value?: Meal) {
  if (!value || props.busy) return
  emit('select', value.id)
  if (typeof window !== 'undefined' && window.matchMedia('(max-width: 720px)').matches && props.online) emit('edit', value)
}
</script>
<template>
  <div class="menu-layout">
    <section class="menu-table" aria-label="Menus des sept jours, midi et soir">
      <div class="menu-table-head" aria-hidden="true"><span>Jour</span><span><Icon name="sun" /> Midi</span><span><Icon name="moon" /> Soir</span></div>
      <article v-for="day in dates" :key="day" class="menu-day" :class="{ 'menu-today': day === today, 'menu-holiday': !!holidayName(day) }" :aria-current="day === today ? 'date' : undefined">
        <h3><span class="menu-short-day">{{ dateLabel(day, true) }}</span><span class="menu-long-day">{{ dateLabel(day) }}</span><small v-if="day === today">Aujourd’hui</small><small v-if="holidayName(day)" class="menu-holiday-name">{{ holidayName(day) }}</small></h3>
        <button v-for="slot in slots" :key="slot.id" class="menu-meal" :class="{ selected: meal(day, slot.id)?.id === selected?.id, outside: meal(day, slot.id)?.status !== 'maison' }" :disabled="busy || !meal(day, slot.id)" :aria-label="accessible(meal(day, slot.id), day, slot.label)" :aria-pressed="meal(day, slot.id)?.id === selected?.id" @click="select(meal(day, slot.id))">
          <span class="menu-slot" :class="slot.id"><Icon :name="slot.icon" /><small>{{ slot.label }}</small></span>
          <MealPhoto :meal="meal(day, slot.id)" :recipes="recipes" />
          <span class="menu-meal-text">
            <template v-if="groups(meal(day, slot.id)).length"><span v-for="group in groups(meal(day, slot.id))" :key="group.course" class="menu-course"><small v-if="group.course !== 'plat' || groups(meal(day, slot.id)).length > 1">{{ group.label }}</small><strong v-for="(name, index) in group.names" :key="index">{{ name }}</strong></span></template>
            <strong v-else>{{ meal(day, slot.id)?.status === 'maison' ? 'Ajouter un repas' : status(meal(day, slot.id)) }}</strong>
          </span>
          <span class="menu-meal-icons"><span v-if="meal(day, slot.id)?.prepared" class="menu-prepared" title="Repas préparé"><Icon name="check" :size="13" /></span><Icon :name="hasMealFood(meal(day, slot.id)) ? 'edit' : 'plus'" :size="16" /></span>
        </button>
      </article>
    </section>
    <aside v-if="selected" class="meal-detail" aria-label="Repas sélectionné">
      <h2>{{ dateLabel(selected.day) }} – {{ selected.slot === 'midi' ? 'Midi' : 'Soir' }}</h2>
      <MealPhoto :meal="selected" :recipes="recipes" class="meal-detail-photo" />
      <template v-if="groups(selected).length"><div v-for="group in groups(selected)" :key="group.course" class="meal-detail-course"><small v-if="group.course !== 'plat' || groups(selected).length > 1">{{ group.label }}</small><strong v-for="(name, index) in group.names" :key="index">{{ name }}</strong></div></template>
      <h3 v-else>{{ selected.status === 'maison' ? 'Un repas à imaginer' : status(selected) }}</h3>
      <p v-if="selected.status !== 'maison'" class="hint">Ce créneau ne génère pas de besoins. Les choix enregistrés sont conservés.</p>
      <div class="detail-portions"><Icon name="people" />Portions : {{ selected.portions }}<span v-if="selected.prepared" class="detail-prepared">Préparé</span></div>
      <div class="meal-detail-actions">
        <button class="secondary detail-edit" @click="emit('edit', selected)" :disabled="busy || !online"><Icon name="edit" />{{ selected.prepared ? 'Voir le repas / annuler la préparation' : 'Modifier le repas' }}</button>
        <button class="secondary" @click="emit('choose', selected)" :disabled="busy || !online || !!selected.prepared"><Icon name="book" />Choisir une recette</button>
        <button class="secondary" @click="emit('ideas')" :disabled="busy || !online"><Icon name="sparkle" />Trouver une suggestion</button>
        <button class="secondary" @click="emit('copy')" :disabled="busy || !online"><Icon name="copy" />Copier une semaine</button>
        <button v-if="selectedRecipe" class="secondary" @click="emit('favorite', selectedRecipe)" :disabled="busy || !online" :aria-pressed="!!selectedRecipe.favorite"><Icon name="heart" />{{ selectedRecipe.favorite ? 'Retirer des favoris' : 'Ajouter aux favoris' }}</button>
        <button v-if="selected.status === 'maison' && !selected.prepared && hasMealFood(selected)" class="primary" @click="emit('prepare', selected)" :disabled="busy || !online"><Icon name="check" />Repas préparé</button>
      </div>
    </aside>
  </div>
</template>
