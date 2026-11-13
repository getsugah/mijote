<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Meal, Recipe } from './api'
import { photoUrl } from './api'
import { photographedMealRecipe } from './mealPresentation'
import Icon from './Icon.vue'
const props = defineProps<{ meal?: Meal; recipes: Recipe[] }>()
const recipe = computed(() => photographedMealRecipe(props.meal, props.recipes))
const source = computed(() => recipe.value ? photoUrl(recipe.value) : '')
const failed = ref('')
</script>
<template>
  <span class="meal-photo" aria-hidden="true">
    <img v-if="source && failed !== source" :src="source" alt="" loading="lazy" @error="failed = source">
    <Icon v-else name="pot" :size="34" />
  </span>
</template>
