import type { Ingredient, Meal, MealDish, Unit } from './api'

export function dishChoice(dish: MealDish) {
  return dish.recipe_id ? `recipe:${dish.recipe_id}` : dish.ingredient_id ? `ingredient:${dish.ingredient_id}` : 'title'
}
export function chooseDish(choice: string, ingredients: Ingredient[]): MealDish {
  const [kind, value] = choice.split(':'); const id = Number(value)
  if (kind === 'recipe' && id > 0) return { recipe_id: id, ingredient_id: null, title: '', quantity: null, unit: null }
  if (kind === 'ingredient' && id > 0) {
    const ingredient = ingredients.find(i => i.id === id)
    const unit: Unit = ingredient?.dimension === 'masse' ? 'g' : ingredient?.dimension === 'volume' ? 'ml' : 'piece'
    return { recipe_id: null, ingredient_id: id, title: '', quantity: 1, unit }
  }
  return { recipe_id: null, ingredient_id: null, title: '', quantity: null, unit: null }
}
export function hasMealFood(meal?: Partial<Meal>) {
  return !!meal && !!(meal.recipe_id || meal.title || meal.side_id || meal.side_ingredient || meal.dishes?.length)
}
export function mealPayload(meal: Meal) {
  return { status: meal.status, title: meal.title, recipe_id: meal.recipe_id || null,
    side_id: meal.side_id || null, portions: Number(meal.portions),
    side_ingredient: meal.side_ingredient ? { ingredient_id: Number(meal.side_ingredient.ingredient_id), quantity: Number(meal.side_ingredient.quantity), unit: meal.side_ingredient.unit } : null,
    dishes: (meal.dishes || []).map(d => ({ course: d.course || 'plat', recipe_id: d.recipe_id || null, ingredient_id: d.ingredient_id || null, title: d.title || '',
      quantity: d.ingredient_id ? Number(d.quantity) : null, unit: d.ingredient_id ? d.unit : null })) }
}

export function mealGroups(meal?: Partial<Meal>): { course: string; label: string; names: string[] }[] {
  if (!meal) return []
  const dishes = meal.dishes || []
  const names = (course: string) => dishes.filter(d => (d.course || 'plat') === course).map(d => d.name || d.title || '').filter(Boolean)
  return [
    { course: 'entree', label: 'Entrée', names: names('entree') },
    { course: 'plat', label: 'Plat', names: [meal.recipe_name || meal.title || '', ...names('plat'), meal.side_name ? `+ ${meal.side_name}` : ''].filter(Boolean) },
    { course: 'dessert', label: 'Dessert', names: names('dessert') },
  ].filter(group => group.names.length)
}
