export function ownRow(standings, clubId) {
  return standings?.find((row) => row.club_id === clubId) ?? null
}
