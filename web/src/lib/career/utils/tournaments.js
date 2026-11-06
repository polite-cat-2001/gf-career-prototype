export const OVERVIEW_SECTIONS = [
  { id: 'table', label: 'Таблица' },
  { id: 'scorers', label: 'Бомбардиры' },
  { id: 'fixtures', label: 'Встречи' },
  { id: 'transfers-top', label: 'Главные трансферы' },
  { id: 'transfers-new', label: 'Новейшие трансферы' },
]

export function buildTournaments(career, season) {
  const club = career?.club
  const standings = season?.standings ?? []
  if (!club || !standings.length) return []

  const round = season?.next
    ? Math.max(0, season.round - 1)
    : (season?.rounds_total ?? 0)
  const id = season?.next?.competition_id || club.league_id || 'league'
  const league = {
    id,
    name: season?.next?.competition || club.league_name || 'Чемпионат',
    kind: 'league',
    standings,
    round,
    rounds_total: season?.rounds_total ?? 0,
    next: true,
  }

  return [league].sort((left, right) => Number(right.next) - Number(left.next))
}

export function tableWindow(rows, clubId, size = 6) {
  const list = rows ?? []
  if (!list.length || size <= 0) return []
  if (list.length <= size) return list

  const ownIndex = list.findIndex((row) => row.club_id === clubId)
  if (ownIndex < 0) return list.slice(0, size)

  const offset = Math.floor(size / 2)
  const start = Math.min(Math.max(ownIndex - offset, 0), list.length - size)
  return list.slice(start, start + size)
}
