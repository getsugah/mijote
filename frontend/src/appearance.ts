import { ref } from 'vue'

export const appearance = ref('light')
try { if (localStorage.getItem('mijote-appearance') === 'dark') appearance.value = 'dark' } catch { /* Storage may be unavailable. */ }
export function setAppearance(value: string) {
  appearance.value = value === 'dark' ? 'dark' : 'light'
  document.documentElement.dataset.appearance = appearance.value
  try { localStorage.setItem('mijote-appearance', appearance.value) } catch { /* Keep the choice for this session. */ }
}
setAppearance(appearance.value)
