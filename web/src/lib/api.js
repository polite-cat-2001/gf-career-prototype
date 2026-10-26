async function request(path, options = {}) {
  const response = await fetch(path, options)
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const payload = await response.json()
      if (typeof payload.detail === 'string') detail = payload.detail
      else if (payload.detail) detail = JSON.stringify(payload.detail)
    } catch {
      // Keep the HTTP status when the error body is not JSON.
    }
    throw new Error(detail)
  }
  return response.json()
}

function get(path) {
  return request(path)
}

function post(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export const api = {
  meta: () => get('/api/meta'),
  countries: () => get('/api/countries'),
  leagues: (countryId) => get(`/api/leagues?country_id=${encodeURIComponent(countryId)}`),
  clubs: (leagueId) => get(`/api/clubs?league_id=${encodeURIComponent(leagueId)}`),
  club: (clubId) => get(`/api/clubs/${encodeURIComponent(clubId)}`),
  squad: (clubId) => get(`/api/clubs/${encodeURIComponent(clubId)}/players`),
  careers: () => get('/api/careers'),
  latestCareer: () => get('/api/careers/latest'),
  career: (careerId) => get(`/api/careers/${encodeURIComponent(careerId)}`),
  createCareer: (payload) => post('/api/careers', payload),
  saveCareer: (careerId) => post(`/api/careers/${encodeURIComponent(careerId)}/save`),
  swapPlayers: (careerId, playerA, playerB) =>
    post(`/api/careers/${encodeURIComponent(careerId)}/actions`, {
      type: 'swap',
      player_a: playerA,
      player_b: playerB,
    }),
}
