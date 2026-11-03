import { formatValue, positionLabel } from '../../format.js'

export function average(values) {
  if (!values.length) return 0
  return values.reduce((total, value) => total + value, 0) / values.length
}

export function slotFor(lineup, playerId) {
  return lineup.slots.find((slot) => slot.player.id === playerId) ?? null
}

export function currentRole(lineup, player) {
  return slotFor(lineup, player.id)?.role ?? player.role
}

export function teamAfterSwap(
  comparing,
  teamAverage,
  lineup,
  anchorPlayer,
  focusedPlayer,
) {
  if (!comparing) return teamAverage
  const starterIds = lineup.slots.map((slot) => slot.player.id)
  const anchorSlot = starterIds.indexOf(anchorPlayer.id)
  const focusedSlot = starterIds.indexOf(focusedPlayer.id)
  if (anchorSlot !== -1 && focusedSlot !== -1) return teamAverage
  if (anchorSlot === -1 && focusedSlot === -1) return teamAverage
  const overalls = lineup.slots.map(
    (slot) => slot.player.effective_overall ?? slot.player.overall,
  )
  if (anchorSlot !== -1) {
    overalls[anchorSlot] = focusedPlayer.effective_overall ?? focusedPlayer.overall
  }
  if (focusedSlot !== -1) {
    overalls[focusedSlot] = anchorPlayer.effective_overall ?? anchorPlayer.overall
  }
  return average(overalls)
}

export function ratingAt(player, slotRole) {
  if (player.role === slotRole) return Math.round(player.overall)
  const families = {
    GK: 'goalkeeper',
    CB: 'defence',
    LB: 'defence',
    RB: 'defence',
    DM: 'middle',
    CM: 'middle',
    AM: 'middle',
    LM: 'wing',
    RM: 'wing',
    CF: 'attack',
  }
  const order = ['goalkeeper', 'defence', 'middle', 'wing', 'attack']
  const from = order.indexOf(families[player.role])
  const to = order.indexOf(families[slotRole])
  const distance = from === -1 || to === -1 ? 3 : Math.abs(from - to)
  const penalty = distance === 1 ? 2 : distance === 2 ? 4 : 6
  return Math.max(1, Math.round(player.overall - penalty))
}

export function targetInfo(player, comparing, anchorPlayer, focusedPlayer, lineup) {
  if (!comparing || !player) return null
  const counterpart = player.id === anchorPlayer?.id ? focusedPlayer : anchorPlayer
  if (!counterpart) return null
  const slot = slotFor(lineup, counterpart.id)
  if (!slot) return null
  const rating = ratingAt(player, slot.role)
  return {
    role: slot.role,
    position: slot.position,
    rating,
    delta: rating - ratingAt(player, currentRole(lineup, player)),
  }
}

export function infoValues(player) {
  return {
    position: positionLabel(player.position),
    age: player.age ?? '—',
    height: player.height ? `${player.height} см` : '—',
    weight: player.weight ? `${player.weight} кг` : '—',
    foot: player.foot || '—',
    weakFoot: player.weak_foot ?? '—',
    skillMoves: player.skill_moves ?? '—',
    shirtNumber: player.shirt_number ?? '—',
    potential: player.pot ?? '—',
    marketValue: formatValue(player.market_value),
    citizenship: player.citizenship.join(', ') || '—',
  }
}

export function starCount(value) {
  const number = Math.round(Number(value))
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.min(5, number))
}
