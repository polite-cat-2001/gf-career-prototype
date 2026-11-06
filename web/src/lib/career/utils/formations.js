const LINE_BY_ROLE = {
  GK: 'GK',
  CB: 'DEF',
  LB: 'DEF',
  RB: 'DEF',
  DM: 'MID',
  CM: 'MID',
  LM: 'MID',
  RM: 'MID',
  AM: 'MID',
  CF: 'ATT',
}

const LINE_BY_POSITION = {
  GK: 'GK',
  LB: 'DEF',
  CB: 'DEF',
  RB: 'DEF',
  DM: 'MID',
  CM: 'MID',
  LM: 'MID',
  RM: 'MID',
  AM: 'MID',
  LW: 'ATT',
  RW: 'ATT',
  ST: 'ATT',
  CF: 'ATT',
}

function fitScore(player, slot) {
  const role = String(player.role ?? '')
  const roles = slot.roles ?? [slot.role]
  const index = roles.indexOf(role)
  let score = 0
  if (index >= 0) {
    score = 100 - index * 6
  } else {
    const playerLine = LINE_BY_ROLE[role]
    const slotLine = LINE_BY_POSITION[String(slot.position ?? '')]
    score = playerLine && playerLine === slotLine ? 30 : 0
  }
  return score + Number(player.overall ?? 0) * 0.01
}

function assignPlayers(players, slots) {
  const count = slots.length
  if (players.length < count) return players.map((player) => player.id)
  const scores = players
    .slice(0, count)
    .map((player) => slots.map((slot) => fitScore(player, slot)))
  const memo = new Map()

  function solve(slotIndex, mask) {
    if (slotIndex === count) return { score: 0, order: [] }
    const key = `${slotIndex}:${mask}`
    const cached = memo.get(key)
    if (cached) return cached
    let best = { score: -1, order: [] }
    for (let index = 0; index < count; index += 1) {
      const bit = 1 << index
      if (mask & bit) continue
      const rest = solve(slotIndex + 1, mask | bit)
      const score = scores[index][slotIndex] + rest.score
      if (score > best.score) {
        best = { score, order: [index, ...rest.order] }
      }
    }
    memo.set(key, best)
    return best
  }

  return solve(0, 0).order.map((index) => players[index].id)
}

export function previewLineup(lineup, formation) {
  if (!formation || formation.id === lineup.formation) return lineup
  const keeper =
    lineup.slots.find((slot) => slot.position === 'GK') ?? lineup.slots[0]
  if (!keeper) return lineup

  const keeperId = keeper.player.id
  const outfield = lineup.slots
    .filter((slot) => slot.player.id !== keeperId)
    .slice(0, 10)
    .map((slot) => slot.player)
  const outfieldSlots = formation.slots.filter((slot) => slot.position !== 'GK')
  const order = assignPlayers(outfield, outfieldSlots)
  const playersById = new Map(
    lineup.slots.map((slot) => [slot.player.id, slot.player]),
  )

  let outfieldIndex = 0
  const slots = formation.slots.map((slot) => {
    const player =
      slot.position === 'GK'
        ? keeper.player
        : playersById.get(order[outfieldIndex++])
    return { ...slot, player }
  })

  return {
    ...lineup,
    formation: formation.id,
    formation_label: formation.label,
    slots,
  }
}
