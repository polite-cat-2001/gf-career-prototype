export function ownRow(standings, clubId) {
  return standings?.find((row) => row.club_id === clubId) ?? null
}

export function tableRows(standings, currentRow) {
  const rows = standings ?? []
  if (!rows.length) return []
  const visible = rows.slice(0, 5)
  if (currentRow && !visible.includes(currentRow)) {
    visible[4] = { ...currentRow, gapBefore: true }
  }
  return visible
}

export function tableRound(season) {
  return season ? (season.next ? Math.max(0, season.round - 1) : season.rounds_total) : 0
}
