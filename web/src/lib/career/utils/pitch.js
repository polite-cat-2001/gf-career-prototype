const LINE_BY_POSITION = {
  GK: 'GK',
  LB: 'DEF',
  CB: 'DEF',
  RB: 'DEF',
  LWB: 'DEF',
  RWB: 'DEF',
  SW: 'DEF',
  DM: 'MID',
  CM: 'MID',
  AM: 'MID',
  LM: 'MID',
  RM: 'MID',
  LW: 'ATT',
  RW: 'ATT',
  CF: 'ATT',
  ST: 'ATT',
}

const LINE_TOP = {
  GK: 'min(92%, calc(100% - 40px))',
  DEF: '74%',
  MID: '47%',
  ATT: '20%',
}

export function pitchLine(slot) {
  const position = String(slot.position ?? '').toUpperCase()
  if (LINE_BY_POSITION[position]) return LINE_BY_POSITION[position]
  const role = String(slot.role ?? '').toUpperCase()
  return LINE_BY_POSITION[role] ?? 'MID'
}

export function pitchSpot(slot) {
  const line = pitchLine(slot)
  const top = Number.isFinite(slot.y)
    ? line === 'GK'
      ? `min(${slot.y}%, calc(100% - 40px))`
      : `${slot.y}%`
    : LINE_TOP[line]
  return {
    left: Number.isFinite(slot.x) ? slot.x : 50,
    top,
    line,
  }
}
