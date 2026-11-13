<script setup lang="ts">
defineProps<{ name: string; size?: number }>()
const paths: Record<string, string> = {
  menu: 'M3 5h18M3 12h18M3 19h18',
  pot: 'M4 10h16v7a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zm-3 2h3m16 0h3M3 7h18M9 4c-3-2 3-2 0-4m6 4c-3-2 3-2 0-4',
  people: 'M16 21v-3c0-5-12-5-12 0v3zm-2-14a4 4 0 1 1-8 0 4 4 0 0 1 8 0m3 6c5 0 6 3 6 6m-6-16a4 4 0 0 1 0 8',
  chef: 'M7 14a5 5 0 0 1-3-9 5 5 0 0 1 8-2 5 5 0 0 1 8 2 5 5 0 0 1-3 9v7H7zm0 3h10',
  cube: 'm12 2 10 5v11l-10 5-10-5V7zm-10 5 10 5 10-5M12 12v11M7 5l10 5',
  sparkle: 'm12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3zm7 0v5m-2-2h5',
  copy: 'M8 7h13v15H8zM5 17H2V2h13v2',
  heart: 'M20 4c-3-3-7-1-8 1-1-2-5-4-8-1-6 6 4 12 8 16 4-4 14-10 8-16z',
  gear: 'm9 2 6 0 1 3 3 1 3 2-1 4 1 4-3 2-3 1-1 3H9l-1-3-3-1-3-2 1-4-1-4 3-2 3-1zm7 10a4 4 0 1 0-8 0 4 4 0 0 0 8 0',
  calendar: 'M8 2v4m8-4v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m2 10h2m4 0h2m-8 4h2m4 0h2',
  book: 'M12 7c-3-3-7-3-10-1v15c3-2 7-2 10 1 3-3 7-3 10-1V6c-3-2-7-2-10 1zm0 0v15',
  stock: 'M3 5h18v16H3zm-1 0V2h20v3M9 10h6',
  cart: 'M2 3h3l3 13h11l3-9H6m3 14h.01M18 21h.01',
  settings: 'M4 7h16M4 17h16M8 4v6m8 4v6',
  plus: 'M12 5v14M5 12h14',
  left: 'm15 5-7 7 7 7', right: 'm9 5 7 7-7 7',
  check: 'm5 12 4 4L19 6', close: 'm6 6 12 12M6 18 18 6',
  clock: 'M12 8v5l3 2m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0',
  leaf: 'M20 3c-9-1-17 4-15 11 2 7 14 6 15-11zM4 21l10-11',
  logout: 'M9 3H3v18h6m6-15 6 6-6 6m-7-6h13',
  sun: 'M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2m-3 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
  moon: 'M20 15A9 9 0 0 1 9 3a9 9 0 1 0 11 12z',
  edit: 'm16 3 5 5-12 12H4v-5zM14 5l5 5',
  link: 'm10 13 4-4m-6 6-2 2a3 3 0 0 1-4-4l4-4a3 3 0 0 1 4 0m2 0 2-2a3 3 0 0 1 4 4l-4 4a3 3 0 0 1-4 0',
  print: 'M6 9V3h12v6M6 18H3V9h18v9h-3M6 14h12v7H6zm11-2h.01',
  trash: 'M3 6h18M8 6V3h8v3M6 6l1 15h10l1-15M10 10v7m4-7v7',
}
</script>
<template><svg :width="size || 21" :height="size || 21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[name] || paths.leaf" /></svg></template>
