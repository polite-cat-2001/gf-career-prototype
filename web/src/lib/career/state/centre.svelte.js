import { tick } from 'svelte'

import { buildTournaments, OVERVIEW_SECTIONS } from '../utils/tournaments.js'

export function createCentreState(ctx) {
  const { getCareer, getSeason, focusFirst } = ctx

  let section = $state('table')
  let widgetFocused = $state(false)
  let overlayOpen = $state(false)
  let overlayIndex = $state(0)

  const tournaments = $derived(buildTournaments(getCareer(), getSeason()))
  const overlayTournament = $derived(
    tournaments[overlayIndex] ?? tournaments[0] ?? null,
  )

  function setSection(id) {
    if (!OVERVIEW_SECTIONS.some((item) => item.id === id)) return
    section = id
  }

  function cycleSection(direction) {
    const index = OVERVIEW_SECTIONS.findIndex((item) => item.id === section)
    const offset = direction === 'right' ? 1 : -1
    const next = (index + offset + OVERVIEW_SECTIONS.length) % OVERVIEW_SECTIONS.length
    section = OVERVIEW_SECTIONS[next].id
  }

  function setWidgetFocused(value) {
    widgetFocused = value
  }

  function openOverlay() {
    if (!tournaments.length) return
    overlayIndex = 0
    overlayOpen = true
    tick().then(() => document.activeElement?.blur())
  }

  function closeOverlay() {
    overlayOpen = false
    tick().then(() => {
      const target = document.querySelector('[data-overview]')
      if (target) target.focus({ preventScroll: true })
      else focusFirst()
    })
  }

  function cycleTournament(direction) {
    if (!overlayOpen || tournaments.length < 2) return false
    const offset = direction === 'right' ? 1 : -1
    overlayIndex =
      (overlayIndex + offset + tournaments.length) % tournaments.length
    return true
  }

  return {
    get section() {
      return section
    },
    get widgetFocused() {
      return widgetFocused
    },
    get overlayOpen() {
      return overlayOpen
    },
    get overlayIndex() {
      return overlayIndex
    },
    get tournaments() {
      return tournaments
    },
    get overlayTournament() {
      return overlayTournament
    },
    setSection,
    cycleSection,
    setWidgetFocused,
    openOverlay,
    closeOverlay,
    cycleTournament,
  }
}
