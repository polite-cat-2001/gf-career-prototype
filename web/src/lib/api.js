async function get(path) {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }
  return response.json()
}

export const api = {
  meta: () => get('/api/meta'),
  countries: () => get('/api/countries'),
  leagues: (countryId) => get(`/api/leagues?country_id=${encodeURIComponent(countryId)}`),
  clubs: (leagueId) => get(`/api/clubs?league_id=${encodeURIComponent(leagueId)}`),
  club: (clubId) => get(`/api/clubs/${encodeURIComponent(clubId)}`),
  squad: (clubId) => get(`/api/clubs/${encodeURIComponent(clubId)}/players`),
}
