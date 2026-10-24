export function formatValue(value) {
  const number = Number(value) || 0
  if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)} млрд €`
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1)} млн €`
  if (number >= 1_000) return `${Math.round(number / 1_000)} тыс. €`
  return `${number} €`
}

export function formatNumber(value) {
  return new Intl.NumberFormat('ru-RU').format(value)
}

export function formatDate(value) {
  if (!value) return '—'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(parsed)
}

export function formatTimestamp(value) {
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed)
}

export function initials(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

export function ovrClass(overall) {
  const value = Math.round(overall)
  if (value >= 90) return 'rating-dark'
  if (value >= 80) return 'rating-green'
  if (value >= 70) return 'rating-yellow'
  if (value >= 60) return 'rating-orange'
  return 'rating-red'
}

export function hexToRgba(hex, alpha) {
  if (!hex || !hex.startsWith('#') || hex.length < 7) return `rgba(91, 154, 139, ${alpha})`
  const value = hex.slice(1)
  const r = parseInt(value.slice(0, 2), 16)
  const g = parseInt(value.slice(2, 4), 16)
  const b = parseInt(value.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const ROLE_LABELS = {
  GK: 'Вратари',
  CB: 'Центральные защитники',
  LB: 'Левые защитники',
  RB: 'Правые защитники',
  DM: 'Опорные полузащитники',
  CM: 'Центральные полузащитники',
  LM: 'Левые полузащитники',
  RM: 'Правые полузащитники',
  AM: 'Атакующие полузащитники',
  CF: 'Нападающие',
}

export function roleLabel(role) {
  return ROLE_LABELS[role] || role
}

export function tierLabel(league) {
  if (!league) return ''
  const map = {
    'First Tier': 'D1',
    'Second Tier': 'D2',
    'Third Tier': 'D3',
    'Fourth Tier': 'D4',
    'Fifth Tier': 'D5',
    'Sixth Tier': 'D6',
    'Reserve league': 'Резерв',
    'Youth league': 'Молодёжь',
  }
  return map[league.tier] || league.tier
}

export function hideBrokenImage(event) {
  event.currentTarget.style.visibility = 'hidden'
}
