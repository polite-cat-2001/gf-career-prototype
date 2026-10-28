export function plural(value, one, few, many) {
  const number = Math.abs(Number(value) || 0) % 100
  const last = number % 10
  if (number > 10 && number < 20) return many
  if (last === 1) return one
  if (last >= 2 && last <= 4) return few
  return many
}

export function formatValue(value) {  const number = Number(value) || 0
  if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)} млрд €`
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1)} млн €`
  if (number >= 1_000) return `${Math.round(number / 1_000)} тыс. €`
  return `${number} €`
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

const ROLE_SHORT = {
  GK: 'ВРТ',
  CB: 'ЦЗ',
  LB: 'ЛЗ',
  RB: 'ПЗ',
  DM: 'ОП',
  CM: 'ЦП',
  LM: 'ЛП',
  RM: 'ПП',
  AM: 'АП',
  CF: 'ФРВ',
  LW: 'ЛФА',
  RW: 'ПФА',
  ST: 'ФРВ',
}

export function shortRole(role) {
  return ROLE_SHORT[role] || role || '—'
}

export const STAT_LABELS = {
  mental_calmness: 'Хладнокровие',
  mental_defensivepositioning: 'Позиция в обороне',
  mental_offensivepositioning: 'Позиция в атаке',
  mental_resilience: 'Устойчивость',
  mental_vision: 'Видение поля',
  mental_workrate: 'Работоспособность',
  physical_acceleration: 'Ускорение',
  physical_agility: 'Ловкость',
  physical_balance: 'Баланс',
  physical_reaction: 'Реакция',
  physical_shotpower: 'Сила удара',
  physical_stamina: 'Выносливость',
  physical_velocity: 'Скорость',
  technical_ballcontrol: 'Контроль мяча',
  technical_dribble: 'Дриблинг',
  technical_header: 'Игра головой',
  technical_highpass: 'Длинный пас',
  technical_shortpass: 'Короткий пас',
  technical_shot: 'Удар',
  technical_slidingtackle: 'Подкат',
  technical_standingtackle: 'Отбор',
  technical_volley: 'Удар с лёта',
}

export const ATTRIBUTE_GROUPS = [
  {
    id: 'mental',
    label: 'Ментальные',
    keys: [
      'mental_calmness',
      'mental_defensivepositioning',
      'mental_offensivepositioning',
      'mental_resilience',
      'mental_vision',
      'mental_workrate',
    ],
  },
  {
    id: 'physical',
    label: 'Физические',
    keys: [
      'physical_acceleration',
      'physical_agility',
      'physical_balance',
      'physical_reaction',
      'physical_shotpower',
      'physical_stamina',
      'physical_velocity',
    ],
  },
  {
    id: 'technical',
    label: 'Технические',
    keys: [
      'technical_ballcontrol',
      'technical_dribble',
      'technical_header',
      'technical_highpass',
      'technical_shortpass',
      'technical_shot',
      'technical_slidingtackle',
      'technical_standingtackle',
      'technical_volley',
    ],
  },
]

export const RADAR_AXES = [
  { label: 'Темп', keys: ['physical_velocity', 'physical_acceleration'] },
  { label: 'Удар', keys: ['technical_shot', 'physical_shotpower', 'technical_volley'] },
  { label: 'Пасы', keys: ['technical_shortpass', 'technical_highpass', 'mental_vision'] },
  { label: 'Дрибл', keys: ['technical_ballcontrol', 'technical_dribble', 'physical_agility'] },
  {
    label: 'Защита',
    keys: ['technical_standingtackle', 'technical_slidingtackle', 'mental_defensivepositioning'],
  },
  { label: 'Физ', keys: ['physical_stamina', 'physical_resilience', 'physical_reaction'] },
]

export function attributeGroups(stats) {
  if (!stats) return []
  return ATTRIBUTE_GROUPS.map((group) => ({
    id: group.id,
    label: group.label,
    rows: group.keys
      .filter((key) => stats[key] !== undefined)
      .map((key) => ({ key, label: STAT_LABELS[key] || key, value: Math.round(stats[key]) })),
  })).filter((group) => group.rows.length)
}

export function radarValues(stats) {
  if (!stats) return []
  return RADAR_AXES.map((axis) => {
    const values = axis.keys.map((key) => stats[key]).filter((value) => value !== undefined)
    const value = values.length ? values.reduce((total, item) => total + item, 0) / values.length : 0
    return { label: axis.label, value: Math.round(value) }
  })
}

export function statTone(value) {
  if (value >= 85) return 'elite'
  if (value >= 75) return 'good'
  if (value >= 60) return 'ok'
  return 'low'
}

export function compareTone(left, right) {
  if (left === right) return 'even'
  return left > right ? 'better' : 'worse'
}

export function shortDate(value) {
  if (!value) return '—'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(parsed)
}

export function monthLabel(value) {
  if (!value) return '—'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' }).format(parsed)
}

export function shortMonthLabel(value) {
  if (!value) return '—'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { month: 'short', year: 'numeric' })
    .format(parsed)
    .replace(/\s*г\.$/, '')
    .replace(/\./g, '')
    .toUpperCase()
}

const COMPETITION_SHORT = {
  'Premier League': 'АПЛ',
  Championship: 'Чемпионшип',
  Bundesliga: 'Бундеслига',
  '2. Bundesliga': '2. Бундеслига',
  LaLiga: 'Ла Лига',
  'LaLiga 2': 'Ла Лига 2',
  'Serie A': 'Серия А',
  'Serie B': 'Серия B',
  'Ligue 1': 'Лига 1',
  'Ligue 2': 'Лига 2',
  Eredivisie: 'Эредивизи',
  'Primeira Liga': 'Примейра',
  'UEFA Champions League': 'ЛЧ',
  'UEFA Europa League': 'ЛЕ',
}

export function competitionLabel(name) {
  return COMPETITION_SHORT[name] || name || '—'
}

export function weekStrip(value, count = 5) {
  const start = new Date(`${value}T00:00:00`)
  if (Number.isNaN(start.getTime())) return []
  return Array.from({ length: count }, (_, index) => {
    const day = new Date(start)
    day.setDate(start.getDate() + index)
    const key = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`
    return {
      key,
      weekday: new Intl.DateTimeFormat('ru-RU', { weekday: 'short' }).format(day),
      day: day.getDate(),
      today: index === 0,
    }
  })
}

const POSITION_LABELS = {
  Goalkeeper: 'Вратарь',
  Defender: 'Защитник',
  Sweeper: 'Свипер',
  'Centre-Back': 'Центральный защитник',
  'Left-Back': 'Левый защитник',
  'Right-Back': 'Правый защитник',
  Midfielder: 'Полузащитник',
  'Defensive Midfield': 'Опорный полузащитник',
  'Central Midfield': 'Центральный полузащитник',
  'Attacking Midfield': 'Атакующий полузащитник',
  'Left Midfield': 'Левый полузащитник',
  'Right Midfield': 'Правый полузащитник',
  Striker: 'Нападающий',
  'Centre-Forward': 'Центральный нападающий',
  'Second Striker': 'Оттянутый нападающий',
  'Left Winger': 'Левый вингер',
  'Right Winger': 'Правый вингер',
}

export function playerInitialName(player) {
  const first = (player.first_name || '').trim()
  const surname = player.last_name || player.name || ''
  const initial = first ? `${first[0]}. ` : ''
  return `${initial}${surname}`.toUpperCase()
}

export function posTone(role) {
  if (role === 'GK') return 'pos-gk'
  if (['CB', 'LB', 'RB'].includes(role)) return 'pos-def'
  if (['DM', 'CM'].includes(role)) return 'pos-mid'
  if (['AM', 'LM', 'RM'].includes(role)) return 'pos-wide'
  return 'pos-att'
}

export function positionLabel(position) {
  return POSITION_LABELS[position] || position || '—'
}

export function seasonLabel(value) {
  if (!value) return '—'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return '—'
  const year = parsed.getFullYear()
  const start = parsed.getMonth() + 1 >= 7 ? year : year - 1
  return `${start}/${String(start + 1).slice(2)}`
}
