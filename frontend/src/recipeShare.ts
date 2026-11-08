export interface SharedRecipe { url: string; text: string; message: string }

function publicLink(value: string): string | null {
  if (value.length > 2000 || /[\s\u0000-\u001f]/.test(value)) return null
  try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password && url.hostname ? url.href : null } catch { return null }
}
export function sharedRecipe(payload: unknown): SharedRecipe {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new Error('Partage illisible. Utiliser le collage manuel.')
  const p = payload as Record<string, unknown>
  for (const [key, limit] of Object.entries({ title: 300, url: 2000, text: 60000 })) if (p[key] !== undefined && (typeof p[key] !== 'string' || (p[key] as string).length > limit)) throw new Error('Partage trop long ou invalide. Utiliser le collage manuel.')
  const title = ((p.title || '') as string).trim(), text = ((p.text || '') as string).trim(), explicit = ((p.url || '') as string).trim()
  if (!title && !text && !explicit) throw new Error('Le partage ne contient ni lien ni texte.')
  const combined = [title, text].filter(Boolean).join('\n')
  if (combined.length > 60000) throw new Error('Le titre et le texte partagés sont trop longs. Utiliser un texte plus court.')
  const direct = explicit ? publicLink(explicit) : null
  if (explicit && !direct) throw new Error('Le lien partagé doit être une URL HTTP ou HTTPS sans identifiants.')
  const candidates = new Set<string>()
  for (const match of combined.matchAll(/https?:\/\/[^\s<>"`]+/gi)) {
    let value = match[0]
    // Remove surrounding prose punctuation without damaging balanced URL parentheses.
    value = value.replace(/[.,;]+$/, '')
    while (value.endsWith(')') && (value.match(/\)/g)?.length || 0) > (value.match(/\(/g)?.length || 0)) value = value.slice(0, -1)
    const link = publicLink(value); if (link) candidates.add(link)
  }
  const url = direct || (candidates.size === 1 ? [...candidates][0]! : '')
  return { url, text: combined, message: !direct && candidates.size > 1 ? 'Plusieurs liens ont été partagés. Choisissez la source à utiliser ou analysez le texte.' : 'Partage reçu. Vérifiez le contenu puis lancez la prévisualisation.' }
}

export function takeSharedRecipe(doc: Document): SharedRecipe | null {
  const element = doc.getElementById('mijote-recipe-share')
  if (!element) return null
  const raw = element.textContent || ''; element.remove()
  if (raw.length > 400000) throw new Error('Partage trop volumineux.')
  return sharedRecipe(JSON.parse(raw))
}
