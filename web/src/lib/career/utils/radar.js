export function radarPoints(values, radius = 44, centre = 72) {
  if (!values.length) return ''
  return values
    .map((axis, index) => {
      const angle = (Math.PI * 2 * index) / values.length - Math.PI / 2
      const reach = (axis.value / 100) * radius
      return `${(centre + Math.cos(angle) * reach).toFixed(1)},${(centre + Math.sin(angle) * reach).toFixed(1)}`
    })
    .join(' ')
}

export function radarGrid(values, radius = 44, centre = 72) {
  return values
    .map((_, index) => {
      const angle = (Math.PI * 2 * index) / values.length - Math.PI / 2
      return `${(centre + Math.cos(angle) * radius).toFixed(1)},${(centre + Math.sin(angle) * radius).toFixed(1)}`
    })
    .join(' ')
}

export function radarLabelPos(index, count, radius = 58, centre = 72) {
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2
  return {
    x: centre + Math.cos(angle) * radius,
    y: centre + Math.sin(angle) * radius,
  }
}
