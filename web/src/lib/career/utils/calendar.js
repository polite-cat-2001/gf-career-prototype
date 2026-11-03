import { weekStrip } from '../../format.js'
import { daysBetween } from './dates.js'

export function trackDays(simulating, simStart, days) {
  return simulating && simStart ? weekStrip(simStart, 14) : days
}

export function trackIndex(simulating, simStart, currentTrackDays, displayDate) {
  if (!simulating || !simStart || !currentTrackDays.length) return 0
  return Math.max(
    0,
    Math.min(daysBetween(simStart, displayDate), currentTrackDays.length - 1),
  )
}

export function trackWidth(currentTrackDays) {
  return (currentTrackDays.length / 7) * 100
}

export function trackShift(currentTrackDays, currentTrackIndex) {
  return currentTrackDays.length
    ? (currentTrackIndex / currentTrackDays.length) * 100
    : 0
}
