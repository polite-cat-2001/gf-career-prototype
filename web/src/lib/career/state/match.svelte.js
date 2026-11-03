import { tick } from 'svelte'

import { weekStrip } from '../../format.js'
import { addDay, daysBetween } from '../utils/dates.js'
import {
  trackDays as computeTrackDays,
  trackIndex as computeTrackIndex,
  trackShift as computeTrackShift,
  trackWidth as computeTrackWidth,
} from '../utils/calendar.js'

export function createMatchState(ctx) {
  const {
    getCareer,
    getNextMatch,
    getSeason,
    getReview,
    getPlaying,
    getSaveError,
    onpreview,
    onsimulate,
    onplay,
    onadvance,
    onnextseason,
    focusFirst,
  } = ctx

  let matchdayOpen = $state(false)
  let matchdayStep = $state('results')
  let matchdaySnapshot = $state(null)
  let seasonReview = $state(false)
  let reviewStep = $state(0)
  let simulating = $state(false)
  let advancing = $state(false)
  let simDate = $state(null)
  let simStart = $state(null)
  let simTimer = null
  let matchSimOpen = $state(false)
  let matchSimPhase = $state('setup')
  let matchSimSetup = $state(null)
  let matchSimResult = $state(null)
  let matchSimMinute = $state(0)
  let matchSimLoading = $state(false)
  let matchSimError = $state('')
  let matchSimTimer = null

  const matchdayData = $derived(matchdaySnapshot ?? getSeason()?.last_matchday ?? null)
  const displayDate = $derived(simulating && simDate ? simDate : getCareer().date)
  const days = $derived(weekStrip(displayDate, 7))
  const trackDays = $derived(computeTrackDays(simulating, simStart, days))
  const trackIndex = $derived(computeTrackIndex(simulating, simStart, trackDays, displayDate))
  const trackWidth = $derived(computeTrackWidth(trackDays))
  const trackShift = $derived(computeTrackShift(trackDays, trackIndex))
  const isMatchDay = $derived(Boolean(getNextMatch() && displayDate >= getNextMatch().date))
  const daysToMatch = $derived(
    getNextMatch() ? daysBetween(displayDate, getNextMatch().date) : 0,
  )

  async function openMatchSimulation() {
    if (getPlaying() || advancing || matchSimOpen || !isMatchDay || !getNextMatch()) return
    matchSimError = ''
    matchSimLoading = true
    const setup = await onpreview()
    matchSimLoading = false
    if (!setup) {
      matchSimError = getSaveError() || 'Не удалось открыть симуляцию'
      return
    }
    matchSimSetup = setup
    matchSimResult = null
    matchSimPhase = 'setup'
    matchSimMinute = 0
    matchSimOpen = true
    await tick()
    focusFirst()
  }

  async function launchMatchSimulation() {
    if (!matchSimOpen || matchSimPhase !== 'setup' || matchSimLoading) return
    matchSimError = ''
    matchSimLoading = true
    const result = await onsimulate()
    matchSimLoading = false
    if (!result) {
      matchSimError = getSaveError() || 'Не удалось запустить симуляцию'
      return
    }
    matchSimResult = result
    matchSimPhase = 'live'
    matchSimMinute = 0
    if (matchSimTimer) clearInterval(matchSimTimer)
    matchSimTimer = setInterval(tickMatchSimulation, 1000)
    await tick()
    focusFirst()
  }

  function tickMatchSimulation() {
    if (matchSimPhase !== 'live') return
    if (matchSimMinute >= 90) {
      finishMatchSimulation()
      return
    }
    matchSimMinute += 1
    if (matchSimMinute >= 90) finishMatchSimulation()
  }

  function finishMatchSimulation() {
    if (matchSimTimer) {
      clearInterval(matchSimTimer)
      matchSimTimer = null
    }
    if (matchSimPhase === 'live') {
      matchSimMinute = 90
      matchSimPhase = 'done'
    }
  }

  async function closeMatchSimulation() {
    if (matchSimLoading) return
    if (matchSimTimer) {
      clearInterval(matchSimTimer)
      matchSimTimer = null
    }
    matchSimOpen = false
    matchSimPhase = 'setup'
    matchSimSetup = null
    matchSimResult = null
    matchSimMinute = 0
    matchSimError = ''
    await tick()
    focusFirst()
  }

  function activateMatchSimulation() {
    if (matchSimLoading) return
    if (matchSimPhase === 'setup') {
      launchMatchSimulation()
      return
    }
    if (matchSimPhase === 'live') {
      finishMatchSimulation()
      return
    }
    openMatchday()
  }

  async function playMatch() {
    if (getPlaying() || !isMatchDay) return
    const updated = await onplay()
    if (!updated) return
    openMatchday(updated.season.last_matchday)
  }

  function openMatchday(data = null) {
    const nextData = data ?? matchdayData
    if (!nextData) {
      closeMatchSimulation()
      return
    }
    matchdaySnapshot = nextData
    matchSimOpen = false
    matchSimPhase = 'setup'
    matchSimSetup = null
    matchSimResult = null
    matchSimMinute = 0
    matchSimError = ''
    matchdayStep = 'results'
    matchdayOpen = true
    tick().then(() => document.activeElement?.blur())
  }

  async function closeMatchday() {
    matchdayOpen = false
    matchdayStep = 'results'
    matchdaySnapshot = null
    await tick()
    focusFirst()
  }

  function advanceMatchday() {
    if (matchdayStep === 'results') {
      matchdayStep = 'table'
      return
    }
    closeMatchday()
  }

  function startSimulation() {
    if (!getNextMatch() || isMatchDay || advancing) return
    simDate = getCareer().date
    simStart = getCareer().date
    simulating = true
    if (simTimer) clearInterval(simTimer)
    simTimer = setInterval(tickSimulation, 1000)
  }

  function tickSimulation() {
    if (!simulating || !getNextMatch()) return
    const next = addDay(simDate)
    if (next >= getNextMatch().date) {
      simDate = getNextMatch().date
      stopSimulation()
      return
    }
    simDate = next
  }

  async function stopSimulation() {
    if (advancing) return
    if (simTimer) {
      clearInterval(simTimer)
      simTimer = null
    }
    const target = simDate ?? getCareer().date
    advancing = true
    await onadvance(target)
    advancing = false
    simulating = false
    simDate = null
    simStart = null
    await tick()
    focusFirst()
  }

  async function handleNextWidget() {
    if (advancing) return
    if (simulating) {
      stopSimulation()
      return
    }
    if (!getNextMatch()) {
      openSeasonReview()
      return
    }
    if (isMatchDay) {
      await playMatch()
      return
    }
    startSimulation()
  }

  function openSeasonReview() {
    if (!getSeason()?.complete || advancing) return
    reviewStep = 0
    seasonReview = true
    tick().then(focusFirst)
  }

  function closeSeasonReview() {
    seasonReview = false
    reviewStep = 0
    tick().then(focusFirst)
  }

  async function advanceSeasonReview() {
    if (getReview()?.next && reviewStep === 0) {
      reviewStep = 1
      await tick()
      focusFirst()
      return
    }
    await startNewSeason()
  }

  async function startNewSeason() {
    if (advancing) return
    advancing = true
    const updated = await onnextseason()
    advancing = false
    if (!updated) return
    seasonReview = false
    reviewStep = 0
    await tick()
    focusFirst()
  }

  function dispose() {
    if (simTimer) clearInterval(simTimer)
    if (matchSimTimer) clearInterval(matchSimTimer)
  }

  return {
    get matchdayOpen() {
      return matchdayOpen
    },
    set matchdayOpen(value) {
      matchdayOpen = value
    },
    get matchdayStep() {
      return matchdayStep
    },
    set matchdayStep(value) {
      matchdayStep = value
    },
    get matchdaySnapshot() {
      return matchdaySnapshot
    },
    set matchdaySnapshot(value) {
      matchdaySnapshot = value
    },
    get seasonReview() {
      return seasonReview
    },
    set seasonReview(value) {
      seasonReview = value
    },
    get reviewStep() {
      return reviewStep
    },
    set reviewStep(value) {
      reviewStep = value
    },
    get simulating() {
      return simulating
    },
    get advancing() {
      return advancing
    },
    get simDate() {
      return simDate
    },
    get simStart() {
      return simStart
    },
    get matchSimOpen() {
      return matchSimOpen
    },
    set matchSimOpen(value) {
      matchSimOpen = value
    },
    get matchSimPhase() {
      return matchSimPhase
    },
    set matchSimPhase(value) {
      matchSimPhase = value
    },
    get matchSimSetup() {
      return matchSimSetup
    },
    get matchSimResult() {
      return matchSimResult
    },
    get matchSimMinute() {
      return matchSimMinute
    },
    get matchSimLoading() {
      return matchSimLoading
    },
    get matchSimError() {
      return matchSimError
    },
    get matchdayData() {
      return matchdayData
    },
    get displayDate() {
      return displayDate
    },
    get days() {
      return days
    },
    get trackDays() {
      return trackDays
    },
    get trackIndex() {
      return trackIndex
    },
    get trackWidth() {
      return trackWidth
    },
    get trackShift() {
      return trackShift
    },
    get isMatchDay() {
      return isMatchDay
    },
    get daysToMatch() {
      return daysToMatch
    },
    openMatchSimulation,
    launchMatchSimulation,
    finishMatchSimulation,
    closeMatchSimulation,
    activateMatchSimulation,
    playMatch,
    openMatchday,
    closeMatchday,
    advanceMatchday,
    startSimulation,
    stopSimulation,
    handleNextWidget,
    openSeasonReview,
    closeSeasonReview,
    advanceSeasonReview,
    startNewSeason,
    dispose,
  }
}
