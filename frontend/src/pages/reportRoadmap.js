// Display helpers for the workplace report's learning roadmap.
//
// The server already validates the roadmap (services/ai/roadmap.py). These
// helpers are a second, defensive layer: only readable strings are rendered,
// never object text, and links are limited to plain http(s) URLs.

const SAFE_PROTOCOLS = new Set(['http:', 'https:'])

function safeExternalUrl(value) {
  const raw = typeof value === 'string' ? value.trim() : ''
  if (!raw || /[\s<>"'`\\]/.test(raw)) return ''
  try {
    const url = new URL(raw)
    if (!SAFE_PROTOCOLS.has(url.protocol) || url.username || url.password) return ''
    return url.href
  } catch {
    return ''
  }
}

function readableText(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  if (typeof value !== 'string') return ''
  const text = value.replace(/\s+/g, ' ').trim()
  // Stored or truncated object text (for example "{'skill': ...") is never shown raw.
  if (/^[[{]/.test(text)) return ''
  return text
}

function readableList(values) {
  const seen = new Set()
  const items = []
  for (const value of Array.isArray(values) ? values : []) {
    const text = readableText(value)
    const key = text.toLowerCase()
    if (text && !seen.has(key)) {
      seen.add(key)
      items.push(text)
    }
  }
  return items
}

function displayResources(resources) {
  const seen = new Set()
  const items = []
  for (const resource of Array.isArray(resources) ? resources : []) {
    if (!resource || typeof resource !== 'object') continue
    const url = safeExternalUrl(resource.url)
    const title = readableText(resource.title)
    if (!url || !title || seen.has(url)) continue
    seen.add(url)
    items.push({ url, title, provider: readableText(resource.provider), relevance: readableText(resource.relevance) })
  }
  return items.slice(0, 2)
}

function roadmapForDisplay(evaluation = {}) {
  const items = []
  const bySkill = new Map()
  for (const item of Array.isArray(evaluation.personalized_roadmap) ? evaluation.personalized_roadmap : []) {
    if (!item || typeof item !== 'object') continue
    const skill = readableText(item.skill)
    if (!skill) continue
    const entry = {
      skill,
      evidence: readableText(item.evidence),
      gap: readableText(item.gap),
      steps: readableList(item.next_steps),
      resources: displayResources(item.resources),
    }
    const key = skill.toLowerCase()
    const existing = bySkill.get(key)
    if (existing) {
      // One card per skill: merge a duplicate's distinct steps and links.
      existing.steps = readableList([...existing.steps, ...entry.steps])
      existing.resources = displayResources([...existing.resources, ...entry.resources])
      continue
    }
    bySkill.set(key, entry)
    items.push(entry)
  }
  const usable = items.filter((item) => item.steps.length > 0)
  let status = evaluation.roadmap_status
  if (!['available', 'unavailable', 'none'].includes(status)) {
    status = usable.length ? 'available' : items.length ? 'unavailable' : 'none'
  }
  if (status === 'available' && !usable.length) status = 'unavailable'
  return { status, items: usable }
}

export { displayResources, readableList, readableText, roadmapForDisplay, safeExternalUrl }
