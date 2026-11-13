import type { Meal, Recipe } from './api'

export function mealRecipes(meal: Meal | undefined, recipes: Recipe[]): Recipe[] {
  if (!meal || meal.status !== 'maison') return []
  const ids = [meal.recipe_id, ...(meal.dishes || []).filter(d => (d.course || 'plat') === 'plat').map(d => d.recipe_id),
    ...(meal.dishes || []).map(d => d.recipe_id), meal.side_id]
  return [...new Set(ids)].flatMap(id => { const recipe = recipes.find(r => r.id === id); return recipe ? [recipe] : [] })
}
export function primaryMealRecipe(meal: Meal | undefined, recipes: Recipe[]): Recipe | undefined {
  return mealRecipes(meal, recipes)[0]
}
export function photographedMealRecipe(meal: Meal | undefined, recipes: Recipe[]): Recipe | undefined {
  return mealRecipes(meal, recipes).find(r => r.photo_version)
}
