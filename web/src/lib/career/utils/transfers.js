import { positionLabel } from '../../format.js'
import {
  OFFER_KIND_LABELS,
  OFFER_STATUS_LABELS,
  POSITION_BADGES,
  TRANSFER_GROUP_OPTIONS,
  TRANSFER_PAGE,
  TRANSFER_STATUS_OPTIONS,
} from '../constants/transfers.js'

export function offerStatusLabel(status) {
  return OFFER_STATUS_LABELS[status] ?? status
}

export function offerKindLabel(kind) {
  return OFFER_KIND_LABELS[kind] ?? kind
}

export function contractStatusLabel(status) {
  if (status === 'pending') return 'переговоры'
  if (status === 'counter') return 'контрпредложение'
  if (status === 'accepted') return 'согласован'
  if (status === 'signed') return 'подписан'
  return null
}

export function transferFieldLabel(
  field,
  { filters, countries = [], leagues = [], clubs = [] },
) {
  if (field === 'group') {
    return (
      TRANSFER_GROUP_OPTIONS.find((option) => option.value === filters.group)?.label ?? 'Любая'
    )
  }
  if (field === 'position') {
    return filters.position ? positionLabel(filters.position) : 'Любое'
  }
  if (field === 'citizenship') return filters.citizenship || 'Любое'
  if (field === 'country') {
    return countries.find((country) => country.id === filters.country)?.name ?? 'Любая'
  }
  if (field === 'league') {
    return leagues.find((league) => league.id === filters.league)?.name ?? 'Любая'
  }
  if (field === 'club') {
    return clubs.find((club) => club.id === filters.club)?.name ?? 'Любой'
  }
  if (field === 'status') {
    return (
      TRANSFER_STATUS_OPTIONS.find((option) => option.value === filters.status)?.label ?? 'Любой'
    )
  }
  return '—'
}

export function transferPositionShort(position) {
  if (!position) return 'Любое'
  return POSITION_BADGES[position] ?? positionLabel(position)
}

export function transferValueMeta(
  field,
  { filters, countries = [], leagues = [], clubs = [] },
) {
  if (field === 'position') {
    return { badge: filters.position ? POSITION_BADGES[filters.position] : null }
  }
  if (field === 'citizenship') {
    const country = countries.find((item) => item.name === filters.citizenship)
    return { logo: country?.flag ?? null }
  }
  if (field === 'country') {
    const country = countries.find((item) => item.id === filters.country)
    return { logo: country?.flag ?? null }
  }
  if (field === 'league') {
    const league = leagues.find((item) => item.id === filters.league)
    return { logo: league?.logo ?? null }
  }
  if (field === 'club') {
    const club = clubs.find((item) => item.id === filters.club)
    return { logo: club?.logo ?? null }
  }
  return { logo: null, badge: null }
}

export function buildTransferParams(filters, offset = 0) {
  return {
    name: filters.name.trim() || undefined,
    group: filters.group || undefined,
    position: filters.position || undefined,
    age_min: filters.ageMin ?? undefined,
    age_max: filters.ageMax ?? undefined,
    citizenship: filters.citizenship || undefined,
    country_id: filters.country || undefined,
    league_id: filters.league || undefined,
    club_id: filters.club || undefined,
    status: filters.status || undefined,
    sort: 'overall',
    direction: 'desc',
    limit: TRANSFER_PAGE,
    offset,
  }
}

export function transferFiltersActive(filters) {
  return Object.entries(filters).filter(([, value]) => value !== '' && value !== null).length
}
