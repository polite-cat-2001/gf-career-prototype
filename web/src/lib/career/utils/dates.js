export function daysBetween(from, to) {
  const start = new Date(`${from}T00:00:00Z`)
  const end = new Date(`${to}T00:00:00Z`)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0
  return Math.max(0, Math.round((end - start) / 86_400_000))
}

export function nextSeasonLabel(seasonStart) {
  const year = Number(seasonStart.slice(0, 4)) + 1
  if (Number.isNaN(year)) return ''
  return `${year}/${String((year + 1) % 100).padStart(2, '0')}`
}

export function addDay(value) {
  const parsed = new Date(`${value}T00:00:00Z`)
  parsed.setUTCDate(parsed.getUTCDate() + 1)
  return parsed.toISOString().slice(0, 10)
}
