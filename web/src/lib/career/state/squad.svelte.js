import { tick } from 'svelte'

import {
  CONTRACT_ROLES,
  attributeGroups,
  formatValue,
  positionLabel,
  radarValues,
} from '../../format.js'
import { attributePages } from '../constants/hub.js'
import { INFO_LABELS, centreTabs } from '../constants/hub.js'
import { average, infoValues, teamAfterSwap } from '../utils/squad.js'

export function createSquadState(ctx) {
  const {
    getCareer,
    getLineup,
    getSummary,
    getDetailsPage,
    setTab,
    setView,
    onaction,
    onswap,
    focusFirst,
    focusElement,
  } = ctx

  let centreTab = $state('status')
  let centrePlayerId = $state(null)
  let centreOpenId = $state(null)
  let centreActionBusy = $state(false)
  let negotiationDraft = $state(null)
  let numberCandidate = $state(null)
  let amountField = $state(null)
  let amountDigits = $state('000000000')
  let amountIndex = $state(8)
  let centreAttributePage = $state('overview')
  let focusPlayerId = $state(null)
  let anchorId = $state(null)
  let swapping = $state(false)
  let benchFocused = $state(false)

  const squadPlayers = $derived([
    ...getLineup().slots.map((slot) => slot.player),
    ...getLineup().bench,
    ...(getLineup().reserve ?? []),
  ])
  const centrePlayers = $derived(getCareer().squad.groups.flatMap((group) => group.players))
  const centrePlayer = $derived(
    centrePlayers.find((player) => player.id === centrePlayerId) ?? centrePlayers[0] ?? null,
  )
  const negotiationState = $derived(centrePlayer?.negotiation ?? null)
  const negotiationTerms = $derived(negotiationState?.offer ?? negotiationState?.counter ?? null)
  const amountGroups = $derived.by(() => {
    const digits = amountDigits.padStart(9, '0').slice(-9)
    return [
      { digits: digits.slice(0, 3), start: 0 },
      { digits: digits.slice(3, 6), start: 3 },
      { digits: digits.slice(6, 9), start: 6 },
    ]
  })
  const centreTotals = $derived(centrePlayer?.season_stats ?? {})
  const centreCompetitions = $derived(centrePlayer?.competition_stats ?? [])
  const centreRadar = $derived(centrePlayer ? radarValues(centrePlayer.stats) : [])
  const centreAttributeGroups = $derived(
    centrePlayer ? attributeGroups(centrePlayer.stats) : [],
  )
  const centreAttributeGroup = $derived(
    centreAttributeGroups.find((group) => group.id === centreAttributePage) ??
      centreAttributeGroups[0] ??
      null,
  )
  const finance = $derived(
    getCareer().squad.finance ?? {
      balance: 0,
      total_market_value: getSummary()?.total_market_value ?? 0,
      weekly_wage_bill: 0,
    },
  )
  const focusedPlayer = $derived(
    squadPlayers.find((player) => player.id === focusPlayerId) ?? getLineup().slots[0]?.player ?? null,
  )
  const anchorPlayer = $derived(
    anchorId ? squadPlayers.find((player) => player.id === anchorId) ?? null : null,
  )
  const comparing = $derived(
    Boolean(anchorPlayer && focusedPlayer && anchorPlayer.id !== focusedPlayer.id),
  )
  const canSwap = $derived(
    comparing && anchorPlayer?.available !== false && focusedPlayer?.available !== false,
  )
  const anchorRadar = $derived(anchorPlayer ? radarValues(anchorPlayer.stats) : [])
  const teamAverage = $derived(
    average(
      getLineup().slots.map((slot) => slot.player.effective_overall ?? slot.player.overall),
    ),
  )
  const teamStrength = $derived(Math.round(teamAverage))
  const projectedTeamAverage = $derived(
    teamAfterSwap(comparing, teamAverage, getLineup(), anchorPlayer, focusedPlayer),
  )
  const teamDelta = $derived(comparing ? projectedTeamAverage - teamAverage : 0)
  const teamDisplay = $derived(Math.round(comparing ? projectedTeamAverage : teamAverage))
  const profileGroups = $derived(focusedPlayer ? attributeGroups(focusedPlayer.stats) : [])
  const detailGroups = $derived(
    getDetailsPage() === 1
      ? profileGroups.filter((group) => group.id !== 'technical')
      : getDetailsPage() === 2
        ? profileGroups.filter((group) => group.id === 'technical')
        : [],
  )
  const seasonRows = $derived.by(() => {
    if (!focusedPlayer) return []
    const right = focusedPlayer.season_stats ?? {}
    const left = anchorPlayer ? (anchorPlayer.season_stats ?? {}) : null
    return [
      ['apps', 'Матчи'],
      ['starts', 'В старте'],
      ['minutes', 'Минуты'],
      ['goals', 'Голы'],
      ['assists', 'Ассисты'],
      ['yellow', 'Жёлтые'],
      ['red', 'Красные'],
    ].map(([key, label]) => ({
      key,
      label,
      left: left ? left[key] ?? 0 : right[key] ?? 0,
      right: comparing ? right[key] ?? 0 : null,
    }))
  })
  const infoRows = $derived.by(() => {
    if (!focusedPlayer) return []
    const right = infoValues(focusedPlayer)
    const left = anchorPlayer ? infoValues(anchorPlayer) : null
    return INFO_LABELS.map((item) => ({
      label: item.label,
      left: left ? left[item.key] : right[item.key],
      right: comparing ? right[item.key] : null,
    }))
  })
  const radar = $derived(focusedPlayer ? radarValues(focusedPlayer.stats) : [])

  async function openSquadCentre() {
    setTab('squad')
    setView('centre')
    centreTab = 'status'
    centreAttributePage = 'overview'
    anchorId = null
    benchFocused = false
    focusPlayerId = null
    centreOpenId = null
    centrePlayerId = centrePlayers[0]?.id ?? null
    await tick()
    focusFirst()
  }

  async function setCentreTab(next) {
    if (centreOpenId) return
    if (next === centreTab) return
    centreTab = next
    centreOpenId = null
    await tick()
    focusFirst()
  }

  function switchCentreTab(direction) {
    const index = centreTabs.findIndex((item) => item.id === centreTab)
    const offset = direction === 'right' ? 1 : -1
    const next = centreTabs[(index + offset + centreTabs.length) % centreTabs.length]
    setCentreTab(next.id)
  }

  async function toggleCentreActions(player) {
    if (!player) return
    if (centreOpenId === player.id) {
      closeCentreActions()
      return
    }
    centrePlayerId = player.id
    centreOpenId = player.id
    await tick()
    focusActions(player.id)
    revealRow(player.id)
  }

  function focusActions(playerId = centreOpenId, actionKey = null) {
    if (!playerId) return
    const panel = document.querySelector(`[data-actions="${playerId}"]`)
    const selector = actionKey ? `[data-action="${actionKey}"]` : '[data-autofocus]'
    const target = panel?.querySelector(selector) ?? panel?.querySelector('[data-nav]')
    focusElement(target)
  }

  function rowElement(playerId) {
    return document.querySelector(`.centre [data-player="${playerId}"]`)
  }

  function revealRow(playerId) {
    const wrap = document.querySelector(`.centre-row-wrap[data-row="${playerId}"]`)
    if (!wrap) return
    window.setTimeout(() => {
      wrap.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }, 220)
  }

  function closeCentreActions() {
    const playerId = centreOpenId
    centreOpenId = null
    if (!playerId) return
    tick().then(() => focusElement(rowElement(playerId)))
  }

  async function applyTransferStatus(status) {
    if (!centrePlayer || centreActionBusy) return
    const playerId = centrePlayer.id
    const next = centrePlayer.transfer_status === status ? 'none' : status
    centreActionBusy = true
    const updated = await onaction({
      type: 'transfer_status',
      player_id: playerId,
      status: next,
    })
    centreActionBusy = false
    if (!updated) return
    await tick()
    focusActions(playerId, status)
    revealRow(playerId)
  }

  function freeShirtNumbers(player) {
    if (!player) return []
    const taken = new Set(
      centrePlayers.filter((other) => other.id !== player.id).map((other) => other.shirt_number),
    )
    return Array.from({ length: 99 }, (_, index) => index + 1).filter(
      (number) => !taken.has(number),
    )
  }

  function openNumberScreen() {
    if (!centrePlayer) return
    const free = freeShirtNumbers(centrePlayer)
    numberCandidate = free.includes(centrePlayer.shirt_number)
      ? centrePlayer.shirt_number
      : free[0] ?? null
    setView('number')
    tick().then(focusFirst)
  }

  function cycleNumber(direction) {
    if (!centrePlayer || numberCandidate === null) return
    const free = freeShirtNumbers(centrePlayer)
    if (!free.length) return
    const index = Math.max(0, free.indexOf(numberCandidate))
    const next = (index + (direction === 'right' ? 1 : -1) + free.length) % free.length
    numberCandidate = free[next]
  }

  async function confirmNumber() {
    if (!centrePlayer || numberCandidate === null || centreActionBusy) return
    const playerId = centrePlayer.id
    centreActionBusy = true
    const updated = await onaction({
      type: 'shirt_number',
      player_id: playerId,
      number: numberCandidate,
    })
    centreActionBusy = false
    if (!updated) return
    setView('centre')
    await tick()
    focusActions(playerId, 'number')
    revealRow(playerId)
  }

  function closeNumberScreen() {
    const playerId = centrePlayer?.id
    setView('centre')
    tick().then(() => focusActions(playerId, 'number'))
  }

  function openReleaseScreen() {
    if (!centrePlayer) return
    setView('release')
    tick().then(focusFirst)
  }

  function closeReleaseScreen() {
    const playerId = centrePlayer?.id
    setView('centre')
    tick().then(() => focusActions(playerId, 'release'))
  }

  async function confirmRelease() {
    if (!centrePlayer || centreActionBusy) return
    centreActionBusy = true
    const updated = await onaction({ type: 'release_player', player_id: centrePlayer.id })
    centreActionBusy = false
    if (!updated) return
    setView('centre')
    centreOpenId = null
    centrePlayerId = centrePlayers[0]?.id ?? null
    await tick()
    focusFirst()
  }

  function negotiationSource() {
    const current = centrePlayer
    if (!current) return null
    const state = current.negotiation
    const source = state?.offer ??
      state?.counter ?? {
        years: current.contract?.years ?? 1,
        weekly_wage: current.contract?.weekly_wage ?? 1_000,
        squad_role: current.squad_role ?? 'rotation',
        release_clause: current.contract?.release_clause ?? 0,
      }
    return { ...source }
  }

  function openNegotiationScreen() {
    if (!centrePlayer) return
    negotiationDraft = negotiationSource()
    setView('negotiation')
    if (negotiationNotice(centrePlayer)) {
      onaction({ type: 'ack_negotiation', player_id: centrePlayer.id })
    }
    tick().then(focusFirst)
  }

  function closeNegotiationScreen() {
    const playerId = centrePlayer?.id
    setView('centre')
    negotiationDraft = null
    tick().then(() => focusActions(playerId, 'renew'))
  }

  function negotiationNotice(player) {
    const state = player?.negotiation
    return Boolean(state && state.status !== 'pending' && state.acknowledged === false)
  }

  function openAmount(field) {
    if (!negotiationDraft) return
    const value = Math.max(
      0,
      Math.min(999_999_999, Math.round(Number(negotiationDraft[field]) || 0)),
    )
    amountField = field
    amountDigits = String(value).padStart(9, '0')
    const firstDigit = amountDigits.search(/[1-9]/)
    amountIndex = firstDigit === -1 ? 8 : firstDigit
    setView('amount')
    tick().then(focusFirst)
  }

  function adjustAmount(direction) {
    if (direction === 'left') {
      amountIndex = Math.max(0, amountIndex - 1)
      return
    }
    if (direction === 'right') {
      amountIndex = Math.min(8, amountIndex + 1)
      return
    }
    const digits = amountDigits.split('')
    const digit = Number(digits[amountIndex])
    digits[amountIndex] = String(direction === 'up' ? (digit + 1) % 10 : (digit + 9) % 10)
    amountDigits = digits.join('')
  }

  function focusNegotiationField(field) {
    focusElement(document.querySelector(`.negotiation [data-field="${field}"]`))
  }

  function closeAmountScreen() {
    const field = amountField ?? 'weekly_wage'
    amountField = null
    setView('negotiation')
    tick().then(() => focusNegotiationField(field))
  }

  function finishAmount() {
    if (!negotiationDraft || !amountField) return
    const value = Number.parseInt(amountDigits || '0', 10) || 0
    if (amountField === 'weekly_wage') {
      negotiationDraft.weekly_wage = Math.max(1_000, Math.min(2_000_000, value))
    } else {
      negotiationDraft.release_clause = Math.max(0, Math.min(999_999_999, value))
    }
    negotiationDraft = { ...negotiationDraft }
    const field = amountField
    amountField = null
    setView('negotiation')
    tick().then(() => focusNegotiationField(field))
  }

  function wageStep() {
    const base = centrePlayer?.contract?.weekly_wage ?? 1_000
    return Math.max(1_000, Math.round((base * 0.1) / 100) * 100)
  }

  function clauseStep() {
    const base = centrePlayer?.market_value ?? 1_000_000
    return Math.max(100_000, Math.round((base * 0.05) / 100_000) * 100_000)
  }

  function adjustNegotiationField(field, step) {
    if (!negotiationDraft) return
    if (field === 'years') {
      negotiationDraft.years = Math.min(5, Math.max(1, negotiationDraft.years + step))
    } else if (field === 'weekly_wage') {
      negotiationDraft.weekly_wage = Math.max(
        1_000,
        negotiationDraft.weekly_wage + step * wageStep(),
      )
    } else if (field === 'release_clause') {
      negotiationDraft.release_clause = Math.max(
        0,
        negotiationDraft.release_clause + step * clauseStep(),
      )
    } else if (field === 'squad_role') {
      const index = Math.max(
        0,
        CONTRACT_ROLES.findIndex((role) => role.id === negotiationDraft.squad_role),
      )
      const next = (index + step + CONTRACT_ROLES.length) % CONTRACT_ROLES.length
      negotiationDraft.squad_role = CONTRACT_ROLES[next].id
    }
    negotiationDraft = { ...negotiationDraft }
  }

  async function submitNegotiation() {
    if (!centrePlayer || !negotiationDraft || centreActionBusy) return
    if (centrePlayer.negotiation?.status === 'accepted') {
      await signNegotiation()
      return
    }
    const playerId = centrePlayer.id
    centreActionBusy = true
    const updated = await onaction({
      type: 'negotiate',
      player_id: playerId,
      ...negotiationDraft,
    })
    centreActionBusy = false
    if (!updated) return
    await tick()
    focusFirst()
  }

  async function acceptCounterOffer() {
    if (!centrePlayer || centreActionBusy) return
    const playerId = centrePlayer.id
    centreActionBusy = true
    const updated = await onaction({ type: 'accept_counter', player_id: playerId })
    centreActionBusy = false
    if (!updated) return
    setView('centre')
    negotiationDraft = null
    await tick()
    focusActions(playerId, 'renew')
  }

  async function signNegotiation() {
    if (!centrePlayer || centreActionBusy) return
    const playerId = centrePlayer.id
    centreActionBusy = true
    const updated = await onaction({ type: 'sign_contract', player_id: playerId })
    centreActionBusy = false
    if (!updated) return
    setView('centre')
    negotiationDraft = null
    await tick()
    focusActions(playerId, 'renew')
  }

  async function manageTeamFromCentre() {
    if (!centrePlayer) return
    const playerId = centrePlayer.id
    centreOpenId = null
    negotiationDraft = null
    await openPlan(playerId)
  }

  function shiftAttributePage(offset) {
    const index = Math.max(
      0,
      attributePages.findIndex((page) => page.id === centreAttributePage),
    )
    const next = (index + offset + attributePages.length) % attributePages.length
    centreAttributePage = attributePages[next].id
  }

  async function openPlan(playerId = null) {
    setTab('squad')
    setView('plan')
    anchorId = null
    benchFocused = false
    focusPlayerId = playerId ?? getLineup().slots[0]?.player.id ?? null
    await tick()
    focusPlayer(focusPlayerId)
  }

  function focusPlayer(playerId) {
    if (!playerId) return
    const element = document.querySelector(`[data-player="${playerId}"]`)
    focusElement(element)
  }

  async function activatePlayer(player) {
    if (swapping || player.available === false) return
    if (!anchorId) {
      anchorId = player.id
      focusPlayerId = player.id
      return
    }
    if (anchorId === player.id) {
      anchorId = null
      return
    }
    if (!canSwap) return
    swapping = true
    const anchor = anchorId
    const updated = await onswap(anchor, player.id)
    swapping = false
    if (!updated) return
    anchorId = null
    focusPlayerId = player.id
    await tick()
    focusPlayer(player.id)
  }

  function revealName(event) {
    const wrapper = event.currentTarget.querySelector('.player-name-wrap')
    const name = wrapper?.querySelector('.player-name')
    if (!name || name.classList.contains('is-scrolling')) return
    const shift = wrapper.clientWidth - name.scrollWidth
    if (shift >= -1) return
    name.style.setProperty('--name-shift', `${shift}px`)
    name.classList.remove('is-scrolling')
    void name.offsetWidth
    name.classList.add('is-scrolling')
    name.addEventListener('animationend', () => name.classList.remove('is-scrolling'), {
      once: true,
    })
  }

  return {
    get centreTab() {
      return centreTab
    },
    set centreTab(value) {
      centreTab = value
    },
    get centrePlayerId() {
      return centrePlayerId
    },
    set centrePlayerId(value) {
      centrePlayerId = value
    },
    get centreOpenId() {
      return centreOpenId
    },
    set centreOpenId(value) {
      centreOpenId = value
    },
    get centreActionBusy() {
      return centreActionBusy
    },
    set centreActionBusy(value) {
      centreActionBusy = value
    },
    get negotiationDraft() {
      return negotiationDraft
    },
    set negotiationDraft(value) {
      negotiationDraft = value
    },
    get numberCandidate() {
      return numberCandidate
    },
    get amountField() {
      return amountField
    },
    set amountField(value) {
      amountField = value
    },
    get amountDigits() {
      return amountDigits
    },
    set amountDigits(value) {
      amountDigits = value
    },
    get amountIndex() {
      return amountIndex
    },
    set amountIndex(value) {
      amountIndex = value
    },
    get centreAttributePage() {
      return centreAttributePage
    },
    set centreAttributePage(value) {
      centreAttributePage = value
    },
    get focusPlayerId() {
      return focusPlayerId
    },
    set focusPlayerId(value) {
      focusPlayerId = value
    },
    get anchorId() {
      return anchorId
    },
    set anchorId(value) {
      anchorId = value
    },
    get swapping() {
      return swapping
    },
    get benchFocused() {
      return benchFocused
    },
    set benchFocused(value) {
      benchFocused = value
    },
    get squadPlayers() {
      return squadPlayers
    },
    get centrePlayers() {
      return centrePlayers
    },
    get centrePlayer() {
      return centrePlayer
    },
    get negotiationState() {
      return negotiationState
    },
    get negotiationTerms() {
      return negotiationTerms
    },
    get amountGroups() {
      return amountGroups
    },
    get centreTotals() {
      return centreTotals
    },
    get centreCompetitions() {
      return centreCompetitions
    },
    get centreRadar() {
      return centreRadar
    },
    get centreAttributeGroups() {
      return centreAttributeGroups
    },
    get centreAttributeGroup() {
      return centreAttributeGroup
    },
    get finance() {
      return finance
    },
    get focusedPlayer() {
      return focusedPlayer
    },
    get anchorPlayer() {
      return anchorPlayer
    },
    get comparing() {
      return comparing
    },
    get canSwap() {
      return canSwap
    },
    get anchorRadar() {
      return anchorRadar
    },
    get teamAverage() {
      return teamAverage
    },
    get teamStrength() {
      return teamStrength
    },
    get projectedTeamAverage() {
      return projectedTeamAverage
    },
    get teamDelta() {
      return teamDelta
    },
    get teamDisplay() {
      return teamDisplay
    },
    get profileGroups() {
      return profileGroups
    },
    get detailGroups() {
      return detailGroups
    },
    get seasonRows() {
      return seasonRows
    },
    get infoRows() {
      return infoRows
    },
    get radar() {
      return radar
    },
    openSquadCentre,
    setCentreTab,
    switchCentreTab,
    toggleCentreActions,
    closeCentreActions,
    applyTransferStatus,
    openNumberScreen,
    cycleNumber,
    confirmNumber,
    closeNumberScreen,
    openReleaseScreen,
    closeReleaseScreen,
    confirmRelease,
    openNegotiationScreen,
    closeNegotiationScreen,
    negotiationNotice,
    openAmount,
    adjustAmount,
    closeAmountScreen,
    finishAmount,
    adjustNegotiationField,
    submitNegotiation,
    acceptCounterOffer,
    signNegotiation,
    manageTeamFromCentre,
    shiftAttributePage,
    openPlan,
    focusPlayer,
    activatePlayer,
    revealName,
  }
}
