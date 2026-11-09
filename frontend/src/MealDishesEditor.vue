<script setup lang="ts">
import type { Ingredient, MealDish, Recipe } from './api'
import { units } from './api'
import { chooseDish, dishChoice } from './mealItems'
const props = defineProps<{ modelValue: MealDish[]; recipes: Recipe[]; ingredients: Ingredient[]; disabled?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: MealDish[]] }>()
function patch(index: number, value: Partial<MealDish>) { emit('update:modelValue', props.modelValue.map((dish, i) => i === index ? { ...dish, ...value } : dish)) }
function choose(index: number, value: string) { emit('update:modelValue', props.modelValue.map((dish, i) => i === index ? { ...chooseDish(value, props.ingredients), course: dish.course || 'plat' } : dish)) }
function add() { if (props.modelValue.length < 20) emit('update:modelValue', [...props.modelValue, { ...chooseDish('title', props.ingredients), course: 'plat' }]) }
</script>
<template>
  <section class="meal-dishes-editor">
    <h3>Autres plats et ingrédients</h3>
    <p class="hint">Les recettes suivent les portions du repas. Pour un ingrédient seul, saisissez la quantité totale prévue pour ce repas.</p>
    <fieldset v-for="(dish, index) in modelValue" :key="index" class="meal-dish-row" :disabled="disabled">
      <label>Type de plat<select :value="dish.course || 'plat'" @change="patch(index, { course: ($event.target as HTMLSelectElement).value as any })"><option value="entree">Entrée</option><option value="plat">Plat</option><option value="dessert">Dessert</option></select></label>
      <label>{{ `Ajout ${index + 1}` }}<select :value="dishChoice(dish)" @change="choose(index, ($event.target as HTMLSelectElement).value)"><option value="title">Intitulé libre, sans quantités</option><optgroup label="Recettes"><option v-for="recipe in recipes" :key="recipe.id" :value="`recipe:${recipe.id}`">{{ recipe.name }}</option></optgroup><optgroup label="Ingrédients"><option v-for="ingredient in ingredients" :key="ingredient.id" :value="`ingredient:${ingredient.id}`">{{ ingredient.name }}</option></optgroup></select></label>
      <label v-if="!dish.recipe_id && !dish.ingredient_id">Nom du plat<input :value="dish.title" required maxlength="120" @input="patch(index, { title: ($event.target as HTMLInputElement).value })"></label>
      <div v-if="dish.ingredient_id" class="form-row"><label>Quantité totale<input :value="dish.quantity" type="number" min="0.001" step="0.001" required @input="patch(index, { quantity: Number(($event.target as HTMLInputElement).value) })"></label><label>Unité<select :value="dish.unit" @change="patch(index, { unit: ($event.target as HTMLSelectElement).value as any })"><option v-for="unit in units(ingredients.find(i => i.id === dish.ingredient_id))" :key="unit" :value="unit">{{ unit === 'piece' ? 'pièce(s)' : unit }}</option></select></label></div>
      <button type="button" class="text-button" @click="emit('update:modelValue', modelValue.filter((_, i) => i !== index))">Retirer cet ajout</button>
    </fieldset>
    <button type="button" class="secondary small" @click="add" :disabled="disabled || modelValue.length >= 20">+ Ajouter un plat ou un ingrédient</button>
  </section>
</template>
