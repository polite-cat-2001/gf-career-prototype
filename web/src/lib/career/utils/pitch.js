export function pitchX(x, y) {
  return 50 + (x - 50) * (0.62 + 0.38 * (y / 100))
}

export function pitchY(y) {
  return 8 + y * 0.84
}
