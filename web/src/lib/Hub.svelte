<script>
  import { onMount, tick } from 'svelte'
  import {
    registerBack,
    registerCycle,
    registerDetails,
    registerPrimary,
    registerSave,
    registerTabs,
  } from './actions.js'
  import BenchDrawer from './BenchDrawer.svelte'
  import Controls from './Controls.svelte'
  import Icon from './Icon.svelte'
  import MatchScreen from './MatchScreen.svelte'
  import MatchdayScreen from './MatchdayScreen.svelte'
  import PlayerCard from './PlayerCard.svelte'
  import Tabs from './Tabs.svelte'
  import { focusElement, focusFirst } from './input.js'
  import {
    attributeGroups,
    compareTone,
    competitionLabel,
    formatDate,
    formatTimestamp,
    formatValue,
    hideBrokenImage,
    moraleFace,
    ovrClass,
    playerInitialName,
    plural,
    posTone,
    positionLabel,
    radarValues,
    seasonLabel,
    shortDate,
    shortMonthLabel,
    shortRole,
    statTone,
    statusLabel,
    tierLabel,
    weekStrip,
  } from './format.js'

  let {
    career,
    saving = false,
    playing = false,
    saveNotice = '',
    saveError = '',
    onsave,
    onswap,
    onplay,
    onpreview,
    onsimulate,
    onadvance,
    onnextseason,
    onexit,
  } = $props()

  const tabs = [
    { id: 'centre', label: 'Центр' },
    { id: 'squad', label: 'Состав' },
    { id: 'transfers', label: 'Трансферы', disabled: true },
    { id: 'office', label: 'Офис', disabled: true },
    { id: 'season', label: 'Сезон', disabled: true },
  ]
  const enabledTabs = tabs.filter((tab) => !tab.disabled).map((tab) => tab.id)

  const planTabs = [
    { label: 'Состав', active: true },
    { label: 'Схемы' },
    { label: 'Амплуа' },
    { label: 'Задачи' },
    { label: 'Тактика' },
  ]

  const detailPages = [
    { id: 'general', label: 'Общая информация' },
    { id: 'stats-one', label: 'Статы 1' },
    { id: 'stats-two', label: 'Статы 2' },
    { id: 'season', label: 'Сезон' },
  ]

  const centreTabs = [
    { id: 'status', label: 'Статус' },
    { id: 'stats', label: 'Статистика' },
    { id: 'attributes', label: 'Характеристики' },
    { id: 'finance', label: 'Финансы' },
  ]

  const attributePages = [
    { id: 'overview', label: 'Общая информация' },
    { id: 'mental', label: 'Ментальные' },
    { id: 'physical', label: 'Физические' },
    { id: 'technical', label: 'Технические' },
  ]

  const INFO_LABELS = [
    { key: 'position', label: 'Амплуа' },
    { key: 'age', label: 'Возраст' },
    { key: 'height', label: 'Рост' },
    { key: 'weight', label: 'Вес' },
    { key: 'foot', label: 'Рабочая нога' },
    { key: 'weakFoot', label: 'Слабая нога' },
    { key: 'skillMoves', label: 'Финты' },
    { key: 'shirtNumber', label: 'Номер' },
    { key: 'potential', label: 'Потенциал' },
    { key: 'marketValue', label: 'Стоимость' },
    { key: 'citizenship', label: 'Гражданство' },
  ]

  const squadTiles = [
    { id: 'club', label: 'Состав клуба', note: 'Текущий состав на матч', selected: true },
    { id: 'national', label: 'Сборная', note: 'Сейчас вы не являетесь тренером сборной', icon: 'globe', disabled: true },
    { id: 'centre', label: 'Центр составов', note: 'Статус, статистика и финансы', icon: 'users' },
    { id: 'national-squad', label: 'Выбор состава сборной', note: 'Доступно только для сборных', icon: 'globe', disabled: true },
    { id: 'main-squads', label: 'Основные составы', note: 'Несколько составов — #4', icon: 'layers', disabled: true },
    { id: 'change', label: 'Изменить игрока', note: 'Заблокировано', icon: 'lock', disabled: true },
  ]

  let tab = $state('centre')
  let view = $state('overview')
  let detailsPage = $state(0)
  let centreTab = $state('status')
  let centrePlayerId = $state(null)
  let centreAttributePage = $state('overview')
  let focusPlayerId = $state(null)
  let anchorId = $state(null)
  let swapping = $state(false)
  let benchFocused = $state(false)
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

  let summary = $derived(career.squad.summary)
  let lineup = $derived(career.squad.lineup)
  let season = $derived(career.season)
  let review = $derived(season?.review ?? null)
  let nextMatch = $derived(season?.next ?? null)
  let matchdayData = $derived(matchdaySnapshot ?? season?.last_matchday ?? null)
  let displayDate = $derived(simulating && simDate ? simDate : career.date)
  let days = $derived(weekStrip(displayDate, 7))
  let trackDays = $derived(simulating && simStart ? weekStrip(simStart, 14) : days)
  let trackIndex = $derived(
    simulating && simStart && trackDays.length
      ? Math.max(0, Math.min(daysBetween(simStart, displayDate), trackDays.length - 1))
      : 0,
  )
  let trackWidth = $derived((trackDays.length / 7) * 100)
  let trackShift = $derived(trackDays.length ? (trackIndex / trackDays.length) * 100 : 0)
  let isMatchDay = $derived(Boolean(nextMatch && displayDate >= nextMatch.date))
  let daysToMatch = $derived(nextMatch ? daysBetween(displayDate, nextMatch.date) : 0)
  let ownRow = $derived(
    season?.standings.find((row) => row.club_id === career.club.id) ?? null,
  )
  let tableRows = $derived.by(() => {
    const rows = season?.standings ?? []
    if (!rows.length) return []
    const visible = rows.slice(0, 5)
    if (ownRow && !visible.includes(ownRow)) {
      visible[4] = { ...ownRow, gapBefore: true }
    }
    return visible
  })
  let tableRound = $derived(
    season ? (season.next ? Math.max(0, season.round - 1) : season.rounds_total) : 0,
  )
  let centreAction = $derived(
    advancing
      ? 'Сохраняем дату…'
      : simulating
        ? 'Остановить'
        : playing
          ? 'Матч идёт…'
          : !nextMatch
            ? 'Перейти в следующий сезон'
            : isMatchDay
              ? 'Играть матч'
              : 'Перемотать',
  )
  let squadPlayers = $derived([
    ...lineup.slots.map((slot) => slot.player),
    ...lineup.bench,
    ...(lineup.reserve ?? []),
  ])
  let centrePlayers = $derived(
    career.squad.groups.flatMap((group) => group.players),
  )
  let centrePlayer = $derived(
    centrePlayers.find((player) => player.id === centrePlayerId) ?? centrePlayers[0] ?? null,
  )
  let centreTotals = $derived(centrePlayer?.season_stats ?? {})
  let centreCompetitions = $derived(centrePlayer?.competition_stats ?? [])
  let centreRadar = $derived(centrePlayer ? radarValues(centrePlayer.stats) : [])
  let centreAttributeGroups = $derived(
    centrePlayer ? attributeGroups(centrePlayer.stats) : [],
  )
  let centreAttributeGroup = $derived(
    centreAttributeGroups.find((group) => group.id === centreAttributePage) ??
      centreAttributeGroups[0] ??
      null,
  )
  let finance = $derived(
    career.squad.finance ?? {
      balance: 0,
      total_market_value: summary?.total_market_value ?? 0,
      weekly_wage_bill: 0,
    },
  )
  let focusedPlayer = $derived(
    squadPlayers.find((player) => player.id === focusPlayerId) ?? lineup.slots[0]?.player ?? null,
  )
  let anchorPlayer = $derived(
    anchorId ? squadPlayers.find((player) => player.id === anchorId) ?? null : null,
  )
  let comparing = $derived(
    Boolean(anchorPlayer && focusedPlayer && anchorPlayer.id !== focusedPlayer.id),
  )
  let canSwap = $derived(
    comparing && anchorPlayer?.available !== false && focusedPlayer?.available !== false,
  )
  let anchorRadar = $derived(anchorPlayer ? radarValues(anchorPlayer.stats) : [])
  let teamAverage = $derived(average(lineup.slots.map((slot) => slot.player.effective_overall ?? slot.player.overall)))
  let teamStrength = $derived(Math.round(teamAverage))
  let projectedTeamAverage = $derived(teamAfterSwap())
  let teamDelta = $derived(comparing ? projectedTeamAverage - teamAverage : 0)
  let teamDisplay = $derived(Math.round(comparing ? projectedTeamAverage : teamAverage))
  let profileGroups = $derived(focusedPlayer ? attributeGroups(focusedPlayer.stats) : [])
  let detailGroups = $derived(
    detailsPage === 1
      ? profileGroups.filter((group) => group.id !== 'technical')
      : detailsPage === 2
        ? profileGroups.filter((group) => group.id === 'technical')
        : [],
  )
  let seasonRows = $derived.by(() => {
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
  let infoRows = $derived.by(() => {
    if (!focusedPlayer) return []
    const right = infoValues(focusedPlayer)
    const left = anchorPlayer ? infoValues(anchorPlayer) : null
    return INFO_LABELS.map((item) => ({
      label: item.label,
      left: left ? left[item.key] : right[item.key],
      right: comparing ? right[item.key] : null,
    }))
  })
  let radar = $derived(focusedPlayer ? radarValues(focusedPlayer.stats) : [])

  let hints = $derived.by(() => {
    const start = { gamepad: ['Start'], keyboard: ['S'], label: 'Сохранить' }
    const sections = { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Разделы' }
    if (matchdayOpen) {
      return matchdayStep === 'results'
        ? [
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Таблица' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'В хаб' },
          ]
        : [
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Продолжить' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'К результатам' },
          ]
    }
    if (matchSimOpen) {
      if (matchSimPhase === 'live') {
        return [
          {
            gamepad: ['Y'],
            keyboard: ['R'],
            label: matchSimLoading ? 'Симуляция…' : 'Пропустить',
          },
        ]
      }
      if (matchSimPhase === 'done') {
        return [{ gamepad: ['A'], keyboard: ['Enter'], label: 'Далее' }]
      }
      return [
        {
          gamepad: ['A'],
          keyboard: ['Enter'],
          label: matchSimLoading ? 'Загрузка…' : 'Начать симуляцию',
        },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
      ]
    }
    if (seasonReview) {
      return [
        {
          gamepad: ['A'],
          keyboard: ['Enter'],
          label: reviewStep === 0 ? 'Далее' : 'Начать новый сезон',
        },
        {
          gamepad: ['B'],
          keyboard: ['Esc'],
          label: reviewStep === 1 ? 'К таблице' : 'Закрыть',
        },
      ]
    }
    if (simulating || advancing) {
      return [{ gamepad: ['A'], keyboard: ['Enter'], label: centreAction }]
    }
    if (tab === 'squad' && view === 'centre') {
      const list = [{ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' }]
      if (centreTab === 'attributes') {
        list.push({
          gamepad: ['R-stick'],
          keyboard: ['←', '→'],
          label: 'Страницы',
        })
      }
      list.push({ gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Вкладки' })
      list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
      list.push(start)
      return list
    }
    if (tab === 'squad' && view === 'details') {
      return [
        { gamepad: ['B'], keyboard: ['Esc'], label: 'К полю' },
        { gamepad: ['Y'], keyboard: ['R'], label: 'План игры' },
        { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Страницы' },
        start,
      ]
    }
    if (tab === 'squad' && view === 'plan') {
      return [
        { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
        comparing
          ? { gamepad: ['A'], keyboard: ['Enter'], label: canSwap ? 'Обменять' : 'Просмотр' }
          : { gamepad: ['A'], keyboard: ['Enter'], label: 'Сравнить' },
        { gamepad: ['Y'], keyboard: ['R'], label: 'Подробности' },
        { gamepad: ['B'], keyboard: ['Esc'], label: comparing ? 'Отменить' : 'Назад' },
        start,
      ]
    }
    const list = [sections]
    if (tab === 'centre') {
      list.push({
        gamepad: ['A'],
        keyboard: ['Enter'],
        label: isMatchDay ? 'Выбрать' : centreAction,
      })
      list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'В меню' })
    } else {
      list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'План игры' })
      list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
    }
    list.push(start)
    return list
  })

  onMount(() => {
    const stopBack = registerBack(handleBack)
    const stopTabs = registerTabs(switchTab)
    const stopSave = registerSave(handleSave)
    const stopDetails = registerDetails(handleDetails)
    const stopPrimary = registerPrimary(handlePrimaryAction)
    const stopCycle = registerCycle(handleCycle)
    tick().then(focusFirst)
    return () => {
      stopBack()
      stopTabs()
      stopSave()
      stopDetails()
      stopPrimary()
      stopCycle()
      if (simTimer) clearInterval(simTimer)
      if (matchSimTimer) clearInterval(matchSimTimer)
    }
  })

  function handleSave() {
    if (
      !saving &&
      !seasonReview &&
      !simulating &&
      !advancing &&
      !matchSimOpen &&
      !matchdayOpen
    ) {
      onsave()
    }
  }

  async function openMatchSimulation() {
    if (playing || advancing || matchSimOpen || !isMatchDay || !nextMatch) return
    matchSimError = ''
    matchSimLoading = true
    const setup = await onpreview()
    matchSimLoading = false
    if (!setup) {
      matchSimError = saveError || 'Не удалось открыть симуляцию'
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
      matchSimError = saveError || 'Не удалось запустить симуляцию'
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
    if (playing || !isMatchDay) return
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

  function daysBetween(from, to) {
    const start = new Date(`${from}T00:00:00Z`)
    const end = new Date(`${to}T00:00:00Z`)
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0
    return Math.max(0, Math.round((end - start) / 86_400_000))
  }

  function nextSeasonLabel() {
    const year = Number(season.season_start.slice(0, 4)) + 1
    if (Number.isNaN(year)) return ''
    return `${year}/${String((year + 1) % 100).padStart(2, '0')}`
  }

  function addDay(value) {
    const parsed = new Date(`${value}T00:00:00Z`)
    parsed.setUTCDate(parsed.getUTCDate() + 1)
    return parsed.toISOString().slice(0, 10)
  }

  function startSimulation() {
    if (!nextMatch || isMatchDay || advancing) return
    simDate = career.date
    simStart = career.date
    simulating = true
    if (simTimer) clearInterval(simTimer)
    simTimer = setInterval(tickSimulation, 1000)
  }

  function tickSimulation() {
    if (!simulating || !nextMatch) return
    const next = addDay(simDate)
    if (next >= nextMatch.date) {
      simDate = nextMatch.date
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
    const target = simDate ?? career.date
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
    if (!nextMatch) {
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
    if (!season?.complete || advancing) return
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
    if (review?.next && reviewStep === 0) {
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

  function average(values) {
    if (!values.length) return 0
    return values.reduce((total, value) => total + value, 0) / values.length
  }

  function slotFor(playerId) {
    return lineup.slots.find((slot) => slot.player.id === playerId) ?? null
  }

  function currentRole(player) {
    return slotFor(player.id)?.role ?? player.role
  }

  function teamAfterSwap() {
    if (!comparing) return teamAverage
    const starterIds = lineup.slots.map((slot) => slot.player.id)
    const anchorSlot = starterIds.indexOf(anchorPlayer.id)
    const focusedSlot = starterIds.indexOf(focusedPlayer.id)
    if (anchorSlot !== -1 && focusedSlot !== -1) return teamAverage
    if (anchorSlot === -1 && focusedSlot === -1) return teamAverage
    const overalls = lineup.slots.map((slot) => slot.player.effective_overall ?? slot.player.overall)
    if (anchorSlot !== -1) {
      overalls[anchorSlot] = focusedPlayer.effective_overall ?? focusedPlayer.overall
    }
    if (focusedSlot !== -1) {
      overalls[focusedSlot] = anchorPlayer.effective_overall ?? anchorPlayer.overall
    }
    return average(overalls)
  }

  function ratingAt(player, slotRole) {
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

  function targetInfo(player) {
    if (!comparing || !player) return null
    const counterpart = player.id === anchorPlayer?.id ? focusedPlayer : anchorPlayer
    if (!counterpart) return null
    const slot = slotFor(counterpart.id)
    if (!slot) return null
    const rating = ratingAt(player, slot.role)
    return {
      role: slot.role,
      position: slot.position,
      rating,
      delta: rating - ratingAt(player, currentRole(player)),
    }
  }

  function infoValues(player) {    return {
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

  function handleBack() {
    if (matchdayOpen) {
      if (matchdayStep === 'table') {
        matchdayStep = 'results'
      } else {
        closeMatchday()
      }
      return
    }
    if (matchSimOpen) {
      if (matchSimLoading || matchSimPhase !== 'setup') return
      closeMatchSimulation()
      return
    }
    if (simulating) {
      stopSimulation()
      return
    }
    if (advancing) return
    if (seasonReview) {
      if (reviewStep === 1) {
        reviewStep = 0
        tick().then(focusFirst)
      } else {
        closeSeasonReview()
      }
      return
    }
    if (tab === 'squad') {
      if (view === 'centre') {
        backToOverview()
        return
      }
      if (view === 'details') {
        closeDetails()
        return
      }
      if (view === 'plan') {
        if (anchorId) {
          const anchor = anchorId
          anchorId = null
          tick().then(() => focusPlayer(anchor))
          return
        }
        backToOverview()
        return
      }
      setTab('centre')
      return
    }
    if (tab !== 'centre') {
      setTab('centre')
      return
    }
    onexit()
  }

  function closeDetails() {
    view = 'plan'
    tick().then(() => focusPlayer(focusPlayerId))
  }

  function handlePrimaryAction() {
    if (matchdayOpen) {
      advanceMatchday()
      return true
    }
    if (!matchSimOpen) return false
    activateMatchSimulation()
    return true
  }

  function handleDetails() {
    if (matchdayOpen) return
    if (matchSimOpen) {
      if (matchSimPhase === 'live') finishMatchSimulation()
      return
    }
    if (tab === 'squad' && view === 'centre') return
    toggleDetails()
  }

  function toggleDetails() {
    if (matchdayOpen || seasonReview) return
    if (tab !== 'squad' || !focusedPlayer) return
    if (view === 'centre') return
    if (view === 'details') {
      closeDetails()
      return
    }
    if (view === 'plan') {
      anchorId = null
      benchFocused = false
      detailsPage = 0
      view = 'details'
      tick().then(() => {
        document.querySelector('.details-panel')?.focus({ preventScroll: true })
      })
    }
  }

  async function backToOverview() {
    view = 'overview'
    anchorId = null
    benchFocused = false
    focusPlayerId = null
    await tick()
    focusFirst()
  }

  async function setTab(next) {
    if (simulating || advancing || matchSimOpen || matchdayOpen) return
    if (!enabledTabs.includes(next)) return
    tab = next
    view = 'overview'
    anchorId = null
    benchFocused = false
    focusPlayerId = null
    centrePlayerId = null
    centreTab = 'status'
    await tick()
    focusFirst()
  }

  function switchTab(direction) {
    if (simulating || advancing || seasonReview || matchSimOpen || matchdayOpen) return
    if (tab === 'squad' && view === 'centre') {
      switchCentreTab(direction)
      return
    }
    if (tab === 'squad' && view === 'details') {
      switchDetailsPage(direction)
      return
    }
    const index = enabledTabs.indexOf(tab)
    const offset = direction === 'right' ? 1 : -1
    const next = enabledTabs[(index + offset + enabledTabs.length) % enabledTabs.length]
    setTab(next)
  }

  function switchDetailsPage(direction) {
    const offset = direction === 'right' ? 1 : -1
    detailsPage = (detailsPage + offset + detailPages.length) % detailPages.length
  }

  async function openSquadCentre() {
    tab = 'squad'
    view = 'centre'
    centreTab = 'status'
    centreAttributePage = 'overview'
    anchorId = null
    benchFocused = false
    focusPlayerId = null
    centrePlayerId = centrePlayers[0]?.id ?? null
    await tick()
    focusFirst()
  }

  async function setCentreTab(next) {
    if (next === centreTab) return
    centreTab = next
    await tick()
    focusFirst()
  }

  function switchCentreTab(direction) {
    const index = centreTabs.findIndex((item) => item.id === centreTab)
    const offset = direction === 'right' ? 1 : -1
    const next = centreTabs[(index + offset + centreTabs.length) % centreTabs.length]
    setCentreTab(next.id)
  }

  function handleCycle(direction) {
    if (tab !== 'squad' || view !== 'centre' || centreTab !== 'attributes') return
    shiftAttributePage(direction === 'right' ? 1 : -1)
  }

  function shiftAttributePage(offset) {
    const index = Math.max(
      0,
      attributePages.findIndex((page) => page.id === centreAttributePage),
    )
    const next = (index + offset + attributePages.length) % attributePages.length
    centreAttributePage = attributePages[next].id
  }

  function starCount(value) {
    const number = Math.round(Number(value))
    if (!Number.isFinite(number)) return 0
    return Math.max(0, Math.min(5, number))
  }

  async function openPlan(playerId = null) {
    tab = 'squad'
    view = 'plan'
    anchorId = null
    benchFocused = false
    focusPlayerId = playerId ?? lineup.slots[0]?.player.id ?? null
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

  function pitchX(x, y) {
    return 50 + (x - 50) * (0.62 + 0.38 * (y / 100))
  }

  function pitchY(y) {
    return 8 + y * 0.84
  }

  function radarPoints(values, radius = 44, centre = 72) {
    if (!values.length) return ''
    return values
      .map((axis, index) => {
        const angle = (Math.PI * 2 * index) / values.length - Math.PI / 2
        const reach = (axis.value / 100) * radius
        return `${(centre + Math.cos(angle) * reach).toFixed(1)},${(centre + Math.sin(angle) * reach).toFixed(1)}`
      })
      .join(' ')
  }

  function radarGrid(values, radius = 44, centre = 72) {
    return values
      .map((_, index) => {
        const angle = (Math.PI * 2 * index) / values.length - Math.PI / 2
        return `${(centre + Math.cos(angle) * radius).toFixed(1)},${(centre + Math.sin(angle) * radius).toFixed(1)}`
      })
      .join(' ')
  }

  function radarLabelPos(index, count, radius = 58, centre = 72) {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2
    return {
      x: centre + Math.cos(angle) * radius,
      y: centre + Math.sin(angle) * radius,
    }
  }
</script>

<div class="app" class:is-simulating={matchSimOpen || matchdayOpen}>
  <header class="topbar hub-topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Карьера</div>
        <div class="brand-sub">{career.manager.name}</div>
      </div>
    </div>

    {#if tab === 'squad' && view === 'centre'}
      <div></div>
    {:else}
      <Tabs {tabs} active={tab} onselect={setTab} />
    {/if}

    <div class="hub-club-strip">
      <img class="strip-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
      <div>
        <div class="strip-club">{career.club.name}</div>
        <div class="strip-meta">{formatDate(career.date)} · {tierLabel(career.club)}</div>
      </div>
    </div>
  </header>

  <main class="screen hub-screen">
    {#snippet radarChart(values, secondary)}
      <svg class="radar" viewBox="0 0 144 144" aria-hidden="true">
        <polygon class="radar-grid" points={radarGrid(values)}></polygon>
        <polygon class="radar-grid inner" points={radarGrid(values, 22)}></polygon>
        {#if secondary?.length}
          <polygon class="radar-compare" points={radarPoints(secondary)}></polygon>
        {/if}
        <polygon class="radar-fill" points={radarPoints(values)}></polygon>
        {#each values as axis, index (axis.label)}
          {@const pos = radarLabelPos(index, values.length)}
          <text class="radar-label" x={pos.x} y={pos.y}>{axis.label}</text>
        {/each}
      </svg>
    {/snippet}

    {#snippet strengthBadge()}
      <div class="team-strength">
        <svg class="team-shield" viewBox="0 0 64 72" aria-hidden="true">
          <path d="M32 2 60 11v25c0 16-12 27-28 34C16 63 4 52 4 36V11z"></path>
        </svg>
        <strong>{teamDisplay}</strong>
        {#if comparing && teamDelta > 0.05}
          <span class="team-delta up" aria-label="Сила состава вырастет">▲</span>
        {/if}
        {#if comparing && teamDelta < -0.05}
          <span class="team-delta down" aria-label="Сила состава упадёт">▼</span>
        {/if}
      </div>
    {/snippet}

    {#snippet centreRow(label, value)}
      <div class="centre-info-row">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    {/snippet}

    {#snippet centreProfile(eyebrow)}
      <div class="centre-profile">
        <span class="centre-photo">
          <img src={centrePlayer.photo} alt="" onerror={hideBrokenImage} />
          {#if centrePlayer.injury || centrePlayer.suspension}
            <span
              class="player-status-flag"
              class:is-injury={Boolean(centrePlayer.injury)}
              title={statusLabel(centrePlayer)}
            >
              {centrePlayer.injury ? '+' : '!'}
            </span>
          {/if}
        </span>
        <div class="centre-profile-info">
          <span class="eyebrow">{eyebrow}</span>
          <strong class="centre-name">{playerInitialName(centrePlayer)}</strong>
          <span class="centre-sub">
            {positionLabel(centrePlayer.position)} · {shortRole(centrePlayer.role)} ·
            {Math.round(centrePlayer.overall)} OVR
          </span>
        </div>
      </div>
    {/snippet}

    {#snippet centreRoster(mode)}
      <section class="centre-list scroll-area" aria-label="Игроки состава">
        {#each centrePlayers as player, index (player.id)}
          <button
            class="centre-player-row"
            class:is-stats={mode === 'stats'}
            class:is-attributes={mode === 'attributes'}
            data-nav
            data-current={player.id === centrePlayerId ? '' : undefined}
            data-autofocus={index === 0 ? '' : undefined}
            onfocus={() => (centrePlayerId = player.id)}
            onclick={() => (centrePlayerId = player.id)}
          >
            <span class="centre-row-photo">
              <img src={player.photo} alt="" onerror={hideBrokenImage} />
              {#if player.injury || player.suspension}
                <span
                  class="player-status-flag"
                  class:is-injury={Boolean(player.injury)}
                  title={statusLabel(player)}
                >
                  {player.injury ? '+' : '!'}
                </span>
              {/if}
            </span>
            <span class="centre-row-main">
              <span class="centre-row-name">{playerInitialName(player)}</span>
              <span class="centre-row-meta">
                <span class="pos-badge {posTone(player.role)}">{shortRole(player.role)}</span>
                <span>{player.squad_role_short}</span>
              </span>
            </span>
            {#if mode === 'stats'}
              <span class="centre-row-totals">
                {player.season_stats?.apps ?? 0} И · {player.season_stats?.goals ?? 0} Г ·
                {player.season_stats?.assists ?? 0} А · {player.season_stats?.minutes ?? 0} мин
              </span>
            {:else}
              <strong class="centre-row-ovr {ovrClass(player.overall)}">
                {Math.round(player.overall)}
              </strong>
              {#if mode === 'status'}
                <span
                  class="centre-row-face"
                  title={player.expected_minutes > 0
                    ? `Настрой ${player.morale}%`
                    : 'Нет данных о настрое'}
                >
                  {player.expected_minutes > 0 ? moraleFace(player.morale) : '—'}
                </span>
              {/if}
            {/if}
          </button>
        {/each}
      </section>
    {/snippet}

    {#snippet playerBlock(player, mirrored)}
      {@const target = targetInfo(player)}
      {@const role = currentRole(player)}
      <div class="head-side" class:mirrored={mirrored}>
        <div class="head-photo-block">
          <span class="player-photo-large">
            <img src={player.photo} alt="" onerror={hideBrokenImage} />
            {#if player.injury || player.suspension}
              <span
                class="player-status-flag"
                class:is-injury={Boolean(player.injury)}
                title={statusLabel(player)}
              >
                {player.injury ? '+' : '!'}
              </span>
            {/if}
          </span>
          <span class="photo-fatigue" title={`Кондиция ${player.fatigue}%`}>
            <span class="fatigue-bar" class:is-low={player.fatigue < 50}>
              <i style={`width:${player.fatigue}%`}></i>
            </span>
          </span>
        </div>
        <div class="head-info" class:right={mirrored}>
          <div class="head-name-row">
            {#if player.shirt_number}
              <span class="head-number">{player.shirt_number}</span>
            {/if}
            <strong class="head-name">{playerInitialName(player)}</strong>
          </div>
          <div class="head-rating-row">
            <span class="pos-badge {posTone(role)}">{shortRole(role)}</span>
            <strong class="head-ovr {ovrClass(ratingAt(player, role))}">{ratingAt(player, role)}</strong>
            <span class="head-shift">›</span>
            {#if target}
              <span class="pos-badge {posTone(target.role)}">{shortRole(target.role)}</span>
              <strong class="head-ovr {ovrClass(target.rating)}">{target.rating}</strong>
              {#if target.delta > 0}
                <span class="rating-delta up">▲</span>
              {:else if target.delta < 0}
                <span class="rating-delta down">▼</span>
              {/if}
            {:else}
              <span class="rating-dash">–</span>
            {/if}
          </div>
          <div class="head-season">
            <span>{player.season_stats?.apps ?? 0} М</span>
            <span>{player.season_stats?.goals ?? 0} Г</span>
            <span>{player.season_stats?.assists ?? 0} А</span>
            <span>{player.season_stats?.minutes ?? 0} мин</span>
          </div>
        </div>
      </div>
    {/snippet}

    {#if saveError}
      <div class="notice error hub-notice">{saveError}</div>
    {:else if saveNotice}
      <div class="notice hub-notice">{saveNotice}</div>
    {/if}

    {#if tab === 'centre'}
      <div class="hub-grid" inert={seasonReview || matchSimOpen || matchdayOpen ? true : undefined}>
        {#if isMatchDay && nextMatch && !simulating && !advancing}
          <div class="match-actions" style="grid-area: next">
            <button class="match-action" data-nav data-autofocus onclick={playMatch}>
              <div class="match-action-head">
                <div>
                  <span class="eyebrow">Матч</span>
                  <strong class="match-action-title">Играть</strong>
                </div>
                <img
                  class="match-action-crest"
                  src={nextMatch.opponent.logo}
                  alt=""
                  onerror={hideBrokenImage}
                />
              </div>
              <span class="match-action-meta">
                Тур {nextMatch.round} · {shortDate(nextMatch.date)} · {nextMatch.home
                  ? 'Дома'
                  : 'В гостях'}
              </span>
              <div class="match-action-foot">
                <span>vs {nextMatch.opponent.name}</span>
                <span>{career.club.league_name}</span>
              </div>
            </button>

            <button class="match-action" data-nav onclick={openMatchSimulation}>
              <div class="match-action-head">
                <div>
                  <span class="eyebrow">Матч</span>
                  <strong class="match-action-title">Симуляция</strong>
                </div>
                <Icon name="clock" size={34} />
              </div>
              <span class="match-action-meta">
                Тур {nextMatch.round} · {shortDate(nextMatch.date)} · {nextMatch.home
                  ? 'Дома'
                  : 'В гостях'}
              </span>
              <div class="match-action-foot">
                <span>vs {nextMatch.opponent.name}</span>
                <span>{career.club.league_name}</span>
              </div>
            </button>
          </div>
        {:else}
        <button
          class="widget widget-next"
          class:is-simulating={simulating}
          style="grid-area: next"
          data-nav
          data-autofocus
          onclick={handleNextWidget}
        >
          <div class="widget-head calendar-head">
            <strong class="widget-title calendar-title" class:is-season={season.complete}>
              {simulating
                ? 'Остановить'
                : season.complete
                  ? 'Перейти в следующий сезон'
                  : 'Далее'}
            </strong>
            <span class="calendar-month">{shortMonthLabel(displayDate)}</span>
          </div>

          <div class="day-window">
            <div
              class="day-track"
              class:is-sliding={simulating}
              style={`width:${trackWidth}%; --cells:${trackDays.length}; --shift:${trackShift}%`}
            >
              {#each trackDays as day (day.key)}
                <div
                  class="day"
                  class:today={day.key === displayDate}
                  class:is-match={nextMatch && day.key === nextMatch.date}
                >
                  <span class="day-week">{day.weekday}</span>
                  <span class="day-num">{day.day}</span>
                  {#if nextMatch && day.key === nextMatch.date}
                    <img
                      class="day-crest"
                      src={nextMatch.opponent.logo}
                      alt=""
                      onerror={hideBrokenImage}
                    />
                  {/if}
                </div>
              {/each}
            </div>
          </div>

          {#if nextMatch}
            {@const homeTeam = nextMatch.home ? career.club : nextMatch.opponent}
            {@const awayTeam = nextMatch.home ? nextMatch.opponent : career.club}
            <div class="next-fixture">
              <div class="fixture-side">
                <img class="fixture-crest" src={homeTeam.logo} alt="" onerror={hideBrokenImage} />
                <span class="fixture-name">{homeTeam.name}</span>
              </div>
              <span class="fixture-vs">VS</span>
              <div class="fixture-side is-away">
                <span class="fixture-name">{awayTeam.name}</span>
                <img class="fixture-crest" src={awayTeam.logo} alt="" onerror={hideBrokenImage} />
              </div>
            </div>
            <div class="calendar-foot">
              <span class="next-meta">
                {seasonLabel(displayDate)} · {competitionLabel(career.club.league_name)} · Тур
                {nextMatch.round} · {nextMatch.home ? 'Дома' : 'В гостях'}
              </span>
              {#if season.form.length}
                <div class="form-pills">
                  {#each season.form as item (item.fixture_id)}
                    <span
                      class="form-pill"
                      class:is-win={item.outcome === 'W'}
                      class:is-draw={item.outcome === 'D'}
                      class:is-loss={item.outcome === 'L'}
                      title={`${item.opponent.name} ${item.goals_for}:${item.goals_against}`}
                    >
                      {item.outcome === 'W' ? 'В' : item.outcome === 'D' ? 'Н' : 'П'}
                    </span>
                  {/each}
                </div>
              {/if}
            </div>
          {:else}
            <div class="season-final">
              <span class="season-final-title">Сезон завершён</span>
              {#if ownRow}
                <span>
                  {ownRow.position}-е место · {ownRow.points}
                  {plural(ownRow.points, 'очко', 'очка', 'очков')} · {ownRow.played}
                  {plural(ownRow.played, 'матч', 'матча', 'матчей')}
                </span>
              {/if}
            </div>
            <div class="widget-action-bar season-cta">
              <span>Перейти в следующий сезон</span>
              <span>A</span>
            </div>
          {/if}
        </button>
        {/if}

        <section class="widget widget-centre is-soon" style="grid-area: centre">
          <div class="widget-head">
            <div>
              <span class="eyebrow">Переговоры</span>
              <strong class="widget-title">Центр трансферов</strong>
            </div>
            <span class="soon-tag">нужен #4</span>
          </div>
          <Icon name="shirt" size={76} />
          <p class="widget-note">Предложения, переговоры и подписания — после трансферного тикета.</p>
          <div class="widget-dots" aria-hidden="true"><i class="active"></i><i></i><i></i></div>
        </section>

        <section class="widget widget-table" style="grid-area: table">
          <div class="widget-head">
            <strong class="widget-title widget-title-sm">Таблицы</strong>
            <span class="soon-tag">{tableRound ? `Тур ${tableRound}` : 'Старт'}</span>
          </div>
          <div class="mini-table">
            <div class="mini-row mini-head">
              <span>#</span>
              <span>Клуб</span>
              <span>И</span>
              <span>Р</span>
              <span>О</span>
            </div>
            {#each tableRows as row (row.club_id)}
              {#if row.gapBefore}
                <div class="mini-gap" aria-hidden="true">⋯</div>
              {/if}
              <div class="mini-row" class:is-club={row.club_id === career.club.id}>
                <span class="mini-pos">{row.position}</span>
                <span class="mini-name">{row.club_name}</span>
                <span>{row.played}</span>
                <span>{row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}</span>
                <span class="mini-pts">{row.points}</span>
              </div>
            {/each}
          </div>
        </section>

        <section class="widget widget-news is-soon" style="grid-area: news">
          <div class="widget-head">
            <strong class="widget-title widget-title-sm">Срочные новости</strong>
            <span class="soon-tag">после #4</span>
          </div>
          <Icon name="news" size={68} />
          <p class="widget-note">Лента новостей и результаты матчей — после календаря и матчей.</p>
        </section>

        <section class="widget widget-training is-soon" style="grid-area: training">
          <div class="widget-head">
            <strong class="widget-title widget-title-sm">Тренировка</strong>
            <span class="soon-tag">после #4</span>
          </div>
          <Icon name="chart" size={56} />
          <p class="widget-note">До пяти тренировок в неделю: характеристики, рейтинг и стоимость.</p>
        </section>
      </div>
    {:else if tab === 'squad' && view === 'overview'}
      <div class="squad-overview">
        <button class="squad-team" data-nav data-autofocus onclick={() => openPlan()}>
          <div class="squad-team-head">
            <img class="squad-team-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
            <div class="squad-team-title">
              <span class="eyebrow">Состав клуба</span>
              <strong>{career.club.name}: по умолч.</strong>
              <span>{lineup.formation} · {career.club.league_name}</span>
            </div>
            <span class="widget-action">A · план игры</span>
          </div>

          <div class="pitch pitch-plan">
            <span class="pitch-surface"></span>
            <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <polygon points="13,2 87,2 98,98 2,98"></polygon>
              <line x1="7" y1="50" x2="93" y2="50"></line>
              <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
              <polygon points="33,2 67,2 70,18 30,18"></polygon>
              <polygon points="25,98 75,98 70,80 30,80"></polygon>
            </svg>
            {#each lineup.slots as slot (slot.position + slot.player.id)}
              <PlayerCard
                player={slot.player}
                role={slot.role}
                preview
                positionStyle={`left:${pitchX(slot.x, slot.y)}%; top:${pitchY(slot.y)}%`}
              />
            {/each}
            {@render strengthBadge()}
          </div>

          <div class="squad-team-foot">
            <span>{summary.squad_size} игроков · средний возраст {summary.average_age ?? '—'}</span>
            <span>{formatValue(summary.total_market_value)}</span>
          </div>
        </button>

        <div class="squad-tiles">
          {#each squadTiles as tile (tile.id)}
            {#if tile.selected}
              <div class="squad-tile is-selected" aria-current="true">
                <span class="squad-tile-label">{tile.label}</span>
                <span class="squad-tile-icon">
                  <img src={career.club.logo} alt="" onerror={hideBrokenImage} />
                  <span class="squad-tile-check"><Icon name="check" size={14} /></span>
                </span>
                <span class="squad-tile-note">{career.club.name}</span>
              </div>
            {:else if tile.id === 'centre'}
              <button class="squad-tile" data-nav onclick={openSquadCentre}>
                <span class="squad-tile-label">{tile.label}</span>
                <span class="squad-tile-icon"><Icon name={tile.icon} size={44} /></span>
                <span class="squad-tile-note">{tile.note}</span>
              </button>
            {:else}
              <div class="squad-tile is-disabled" aria-disabled="true">
                <span class="squad-tile-label">{tile.label}</span>
                <span class="squad-tile-icon"><Icon name={tile.icon} size={44} /></span>
                <span class="squad-tile-note">{tile.note}</span>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {:else if tab === 'squad' && view === 'centre'}
      <div class="centre">
        <nav class="centre-tabs" aria-label="Центр составов">
          {#each centreTabs as item (item.id)}
            <button
              class="centre-tab"
              class:active={centreTab === item.id}
              data-nav
              onclick={() => setCentreTab(item.id)}
            >
              {item.label}
            </button>
          {/each}
        </nav>

        {#if centreTab === 'status'}
          <div class="centre-body">
            {@render centreRoster('status')}

            {#if centrePlayer}
              <aside class="centre-panel scroll-area" aria-label="Карточка игрока">
                {@render centreProfile('Статус игрока')}

                <div class="centre-morale-block">
                  <div class="centre-morale-head">
                    <span>Настрой</span>
                    <span class="centre-morale-value">
                      <span class="centre-morale-face">
                        {centrePlayer.expected_minutes > 0
                          ? moraleFace(centrePlayer.morale)
                          : '—'}
                      </span>
                      <strong
                        class:is-none={centrePlayer.expected_minutes <= 0}
                        class:is-good={centrePlayer.expected_minutes > 0 &&
                          centrePlayer.morale >= 70}
                        class:is-ok={centrePlayer.expected_minutes > 0 &&
                          centrePlayer.morale >= 40 &&
                          centrePlayer.morale < 70}
                        class:is-low={centrePlayer.expected_minutes > 0 &&
                          centrePlayer.morale < 40}
                      >
                        {centrePlayer.expected_minutes > 0 ? `${centrePlayer.morale}%` : ''}
                      </strong>
                    </span>
                  </div>
                  <div class="centre-morale-meta">
                    {#if centrePlayer.expected_minutes > 0}
                      <span>
                        Факт {centrePlayer.actual_minutes} · План {centrePlayer.expected_minutes} мин
                      </span>
                    {:else}
                      <span>Ожидаемые минуты появятся после матчей</span>
                    {/if}
                    <span>
                      Ожидается {Math.round((centrePlayer.expected_share ?? 0) * 100)}% времени
                    </span>
                  </div>
                </div>

                <section class="centre-block">
                  <div class="centre-block-head">Личные данные</div>
                  {@render centreRow('Возраст', centrePlayer.age ?? '—')}
                  {@render centreRow(
                    'Гражданство',
                    centrePlayer.citizenship.join(', ') || '—',
                  )}
                  {@render centreRow(
                    'Рост',
                    centrePlayer.height ? `${centrePlayer.height} см` : '—',
                  )}
                  {@render centreRow(
                    'Вес',
                    centrePlayer.weight ? `${centrePlayer.weight} кг` : '—',
                  )}
                  {@render centreRow('Рабочая нога', centrePlayer.foot || '—')}
                  {@render centreRow('Номер', centrePlayer.shirt_number ?? '—')}
                </section>

                <section class="centre-block">
                  <div class="centre-block-head">Контракт</div>
                  {@render centreRow('Амплуа', centrePlayer.squad_role_label ?? '—')}
                  {@render centreRow(
                    'Срок',
                    `${centrePlayer.contract?.years ?? 1} ${plural(
                      centrePlayer.contract?.years ?? 1,
                      'год',
                      'года',
                      'лет',
                    )}`,
                  )}
                  {@render centreRow(
                    'Зарплата',
                    `${formatValue(centrePlayer.contract?.weekly_wage ?? 0)} / нед.`,
                  )}
                  {@render centreRow(
                    'Отступные',
                    formatValue(centrePlayer.contract?.release_clause ?? 0),
                  )}
                </section>

                <section class="centre-block">
                  <div class="centre-block-head">Доступность</div>
                  {#if centrePlayer.injury}
                    {@render centreRow('Травма', centrePlayer.injury.type)}
                    {@render centreRow('Возвращение', formatDate(centrePlayer.injury.until))}
                  {:else if centrePlayer.suspension}
                    {@render centreRow(
                      'Дисквалификация',
                      `${centrePlayer.suspension.matches} ${plural(
                        centrePlayer.suspension.matches,
                        'матч',
                        'матча',
                        'матчей',
                      )}`,
                    )}
                  {:else}
                    {@render centreRow('Состояние', 'Готов к игре')}
                  {/if}
                  {@render centreRow('Кондиция', `${centrePlayer.fatigue}%`)}
                </section>
              </aside>
            {/if}
          </div>
        {:else if centreTab === 'stats'}
          <div class="centre-body">
            {@render centreRoster('stats')}

            {#if centrePlayer}
              <aside class="centre-panel scroll-area" aria-label="Статистика игрока">
                {@render centreProfile('Статистика игрока')}

                <section class="centre-block">
                  <div class="centre-block-head">Итого в сезоне</div>
                  <div class="centre-total-grid">
                    {#each [
                      ['Игры', centreTotals.apps ?? 0],
                      ['Голы', centreTotals.goals ?? 0],
                      ['Ассисты', centreTotals.assists ?? 0],
                      ['Минуты', centreTotals.minutes ?? 0],
                    ] as [label, value] (label)}
                      <div class="centre-total">
                        <strong>{value}</strong>
                        <span>{label}</span>
                      </div>
                    {/each}
                  </div>
                </section>

                <section class="centre-block">
                  <div class="centre-block-head">По турнирам</div>
                  {#if centreCompetitions.length}
                    {#each centreCompetitions as competition (competition.id)}
                      <div class="competition-card">
                        <div class="competition-head">
                          <strong>{competition.name}</strong>
                          <span>{competition.apps} И · {competition.minutes} мин</span>
                        </div>
                        <div class="competition-metrics">
                          <span><strong>{competition.goals}</strong> голы</span>
                          <span><strong>{competition.assists}</strong> ассисты</span>
                          <span><strong>{competition.yellow}</strong> ЖК</span>
                          <span><strong>{competition.red}</strong> КК</span>
                          {#if centrePlayer.role === 'GK'}
                            <span class="is-clean">
                              <strong>{competition.clean_sheets}</strong> сухие
                            </span>
                          {/if}
                        </div>
                      </div>
                    {/each}
                  {:else}
                    <p class="centre-note">Статистика появится после первых матчей.</p>
                  {/if}
                </section>
              </aside>
            {/if}
          </div>
        {:else if centreTab === 'attributes'}
          <div class="centre-body">
            {@render centreRoster('attributes')}

            {#if centrePlayer}
              <aside class="centre-panel scroll-area" aria-label="Характеристики игрока">
                {@render centreProfile('Характеристики игрока')}

                <div class="attribute-layout">
                  <div class="attribute-radar">
                    {@render radarChart(centreRadar)}
                  </div>
                  <div class="attribute-detail">
                    <div class="centre-pager" role="group" aria-label="Группы характеристик">
                      <button
                        class="pager-arrow"
                        type="button"
                        tabindex="-1"
                        aria-label="Предыдущая страница"
                        onmousedown={(event) => event.preventDefault()}
                        onclick={() => shiftAttributePage(-1)}
                      >
                        ‹
                      </button>
                      <span class="pager-stick">R</span>
                      <button
                        class="pager-arrow"
                        type="button"
                        tabindex="-1"
                        aria-label="Следующая страница"
                        onmousedown={(event) => event.preventDefault()}
                        onclick={() => shiftAttributePage(1)}
                      >
                        ›
                      </button>
                      <span class="pager-dots" aria-hidden="true">
                        {#each attributePages as page (page.id)}
                          <i class:active={centreAttributePage === page.id}></i>
                        {/each}
                      </span>
                    </div>
                    {#if centreAttributePage === 'overview'}
                      <div class="attribute-group-title">Общая информация</div>
                      <div class="attribute-facts">
                        <span class="pos-badge {posTone(centrePlayer.role)}">
                          {shortRole(centrePlayer.role)}
                        </span>
                        <span>{positionLabel(centrePlayer.position)}</span>
                        <span>Возраст {centrePlayer.age ?? '—'}</span>
                        <span>{centrePlayer.squad_role_short}</span>
                      </div>
                      <div class="attribute-trait-grid">
                        <div class="attribute-trait">
                          <span>Настрой</span>
                          <strong>
                            {centrePlayer.expected_minutes > 0
                              ? `${moraleFace(centrePlayer.morale)} ${centrePlayer.morale}%`
                              : '—'}
                          </strong>
                        </div>
                        <div class="attribute-trait">
                          <span>Финты</span>
                          <span class="trait-stars">
                            {#each Array.from({ length: 5 }) as _, index (index)}
                              <i class:filled={index < starCount(centrePlayer.skill_moves)}>★</i>
                            {/each}
                          </span>
                        </div>
                        <div class="attribute-trait">
                          <span>Слабая нога</span>
                          <span class="trait-stars">
                            {#each Array.from({ length: 5 }) as _, index (index)}
                              <i class:filled={index < starCount(centrePlayer.weak_foot)}>★</i>
                            {/each}
                          </span>
                        </div>
                        <div class="attribute-trait">
                          <span>Потенциал</span>
                          <strong>{centrePlayer.pot ?? '—'}</strong>
                        </div>
                        <div class="attribute-trait">
                          <span>Стоимость</span>
                          <strong>{formatValue(centrePlayer.market_value)}</strong>
                        </div>
                        <div class="attribute-trait">
                          <span>Контракт</span>
                          <strong>
                            {centrePlayer.contract?.years ?? 1}
                            {plural(centrePlayer.contract?.years ?? 1, 'год', 'года', 'лет')}
                          </strong>
                        </div>
                      </div>
                      <div class="attribute-group-title">Радар</div>
                      <div class="attribute-axis-grid">
                        {#each centreRadar as axis (axis.label)}
                          <div class="attribute-axis">
                            <span>{axis.label}</span>
                            <strong>{axis.value}</strong>
                          </div>
                        {/each}
                      </div>
                    {:else if centreAttributeGroup}
                      <div class="attribute-group-title">{centreAttributeGroup.label}</div>
                      <div class="attribute-rows">
                        {#each centreAttributeGroup.rows as row (row.key)}
                          <div class="attribute-row">
                            <span>{row.label}</span>
                            <strong class="attribute-value {statTone(row.value)}">{row.value}</strong>
                          </div>
                        {/each}
                      </div>
                    {/if}
                  </div>
                </div>
              </aside>
            {/if}
          </div>
        {:else}
          <div class="centre-finance">
            <div class="finance-summary">
              <div class="finance-stat">
                <span>Баланс клуба</span>
                <strong>{formatValue(finance.balance)}</strong>
              </div>
              <div class="finance-stat">
                <span>Стоимость состава</span>
                <strong>{formatValue(finance.total_market_value)}</strong>
              </div>
              <div class="finance-stat">
                <span>Зарплатная ведомость</span>
                <strong>{formatValue(finance.weekly_wage_bill)} <i>/ нед.</i></strong>
              </div>
            </div>

            <div class="finance-body">
              <section class="finance-table" aria-label="Финансы игроков">
                <div class="finance-head" aria-hidden="true">
                  <span>Поз</span>
                  <span>Игрок</span>
                  <span>Возр.</span>
                  <span>Стоимость</span>
                  <span>Зарплата</span>
                  <span>Контракт</span>
                </div>
                <div class="finance-list scroll-area">
                  {#each centrePlayers as player, index (player.id)}
                    <button
                      class="finance-row"
                      data-nav
                      data-current={player.id === centrePlayerId ? '' : undefined}
                      data-autofocus={index === 0 ? '' : undefined}
                      onfocus={() => (centrePlayerId = player.id)}
                      onclick={() => (centrePlayerId = player.id)}
                    >
                      <span class="pos-badge {posTone(player.role)}">{shortRole(player.role)}</span>
                      <span class="finance-name-cell">
                        <span class="finance-row-photo">
                          <img src={player.photo} alt="" onerror={hideBrokenImage} />
                          {#if player.injury || player.suspension}
                            <span
                              class="player-status-flag"
                              class:is-injury={Boolean(player.injury)}
                              title={statusLabel(player)}
                            >
                              {player.injury ? '+' : '!'}
                            </span>
                          {/if}
                        </span>
                        <span class="finance-name">{playerInitialName(player)}</span>
                      </span>
                      <span class="finance-cell">{player.age ?? '—'}</span>
                      <span class="finance-cell is-value">{formatValue(player.market_value)}</span>
                      <span class="finance-cell">{formatValue(player.contract?.weekly_wage ?? 0)}</span>
                      <span class="finance-cell">
                        {player.contract?.years ?? 1}
                        {plural(player.contract?.years ?? 1, 'год', 'года', 'лет')}
                      </span>
                    </button>
                  {/each}
                </div>
              </section>

              {#if centrePlayer}
                <aside class="centre-panel finance-panel scroll-area" aria-label="Финансы игрока">
                  {@render centreProfile('Финансы игрока')}

                  <div class="finance-player-meta">
                    <span class="pos-badge {posTone(centrePlayer.role)}">
                      {shortRole(centrePlayer.role)}
                    </span>
                    <span>Возраст {centrePlayer.age ?? '—'}</span>
                    <span>{centrePlayer.squad_role_short}</span>
                    <span>
                      Настрой
                      {centrePlayer.expected_minutes > 0
                        ? `${moraleFace(centrePlayer.morale)} ${centrePlayer.morale}%`
                        : '—'}
                    </span>
                  </div>

                  <section class="centre-block">
                    <div class="centre-block-head">Финансы</div>
                    {@render centreRow('Стоимость', formatValue(centrePlayer.market_value))}
                    {@render centreRow(
                      'Зарплата',
                      `${formatValue(centrePlayer.contract?.weekly_wage ?? 0)} / нед.`,
                    )}
                    {@render centreRow(
                      'Отступные',
                      formatValue(centrePlayer.contract?.release_clause ?? 0),
                    )}
                  </section>

                  <section class="centre-block">
                    <div class="centre-block-head">Контракт</div>
                    {@render centreRow(
                      'Срок',
                      `${centrePlayer.contract?.years ?? 1} ${plural(
                        centrePlayer.contract?.years ?? 1,
                        'год',
                        'года',
                        'лет',
                      )}`,
                    )}
                    {@render centreRow('Амплуа', centrePlayer.squad_role_label ?? '—')}
                  </section>

                  <section class="centre-block">
                    <div class="centre-block-head">Статус</div>
                    {#if centrePlayer.injury}
                      {@render centreRow('Травма', centrePlayer.injury.type)}
                      {@render centreRow('Возвращение', formatDate(centrePlayer.injury.until))}
                    {:else if centrePlayer.suspension}
                      {@render centreRow(
                        'Дисквалификация',
                        `${centrePlayer.suspension.matches} ${plural(
                          centrePlayer.suspension.matches,
                          'матч',
                          'матча',
                          'матчей',
                        )}`,
                      )}
                    {:else}
                      {@render centreRow('Доступность', 'Готов к игре')}
                    {/if}
                    {@render centreRow('Кондиция', `${centrePlayer.fatigue}%`)}
                  </section>
                </aside>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    {:else if tab === 'squad' && (view === 'plan' || view === 'details') && focusedPlayer}
      <div class="plan">
        <div class="plan-stage" class:has-drawer={view === 'plan'}>
          <nav class="plan-tabs" aria-label="План игры">
            {#each planTabs as item (item.label)}
              <span class="plan-tab" class:active={item.active}>{item.label}</span>
            {/each}
          </nav>

          {#if comparing}
            <div class="player-head compare-head">
              {@render playerBlock(anchorPlayer, false)}
              {#if radar.length && focusedPlayer.role !== 'GK'}
                {@render radarChart(anchorRadar.length ? anchorRadar : radar, anchorRadar.length ? radar : null)}
              {:else}
                <span class="radar-empty">Вратарский профиль не входит в канон</span>
              {/if}
              {@render playerBlock(focusedPlayer, true)}
            </div>
          {:else}
            <div class="player-head">
              {@render playerBlock(focusedPlayer, false)}
              {#if radar.length && focusedPlayer.role !== 'GK'}
                {@render radarChart(radar)}
              {:else}
                <span class="radar-empty">Вратарский профиль не входит в канон</span>
              {/if}
            </div>
          {/if}

          {#if view === 'details'}
            <section class="details-panel" data-nav tabindex="-1" aria-label="Подробности игрока">
              <strong class="details-title">{detailPages[detailsPage].label}</strong>

              {#if detailsPage === 0}
                <div class="details-list details-info">
                  {#each infoRows as row (row.label)}
                    <div class="details-row info-row" class:is-compare={comparing}>
                      <span class="info-value">{row.left}</span>
                      <span class="details-label">{row.label}</span>
                      {#if comparing}
                        <span class="info-value right">{row.right}</span>
                      {:else}
                        <span class="details-spacer"></span>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else if detailsPage === 3}
                <div class="details-list details-info">
                  {#each seasonRows as row (row.key)}
                    <div class="details-row info-row" class:is-compare={comparing}>
                      <span class="info-value">{row.left}</span>
                      <span class="details-label">{row.label}</span>
                      {#if comparing}
                        <span class="info-value right">{row.right}</span>
                      {:else}
                        <span class="details-spacer"></span>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="details-list">
                  {#each detailGroups as group (group.id)}
                    <div class="details-group">
                      <span class="details-group-label">{group.label}</span>
                      {#each group.rows as row (row.key)}
                        {@const right = comparing ? Math.round(focusedPlayer.stats[row.key] ?? 0) : null}
                        {@const left = comparing ? Math.round(anchorPlayer.stats[row.key] ?? 0) : row.value}
                        <div class="details-row" class:is-compare={comparing}>
                          <span class="details-value {comparing ? compareTone(left, right) : statTone(left)}">
                            {left}
                          </span>
                          <span class="details-label">{row.label}</span>
                          {#if comparing}
                            <span class="details-value {compareTone(right, left)}">{right}</span>
                          {:else}
                            <span class="details-spacer"></span>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {/each}
                </div>
              {/if}

              <div class="details-dots" aria-hidden="true">
                {#each detailPages as page, index (page.id)}
                  <i class:active={index === detailsPage}></i>
                {/each}
              </div>
            </section>
          {:else}
            <div class="pitch pitch-plan-large">
              <span class="pitch-surface"></span>
              <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                <polygon points="13,2 87,2 98,98 2,98"></polygon>
                <line x1="7" y1="50" x2="93" y2="50"></line>
                <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
                <polygon points="33,2 67,2 70,18 30,18"></polygon>
                <polygon points="25,98 75,98 70,80 30,80"></polygon>
              </svg>
              {#each lineup.slots as slot (slot.position + slot.player.id)}
                <PlayerCard
                  player={slot.player}
                  role={slot.role}
                  interactive
                  selected={anchorId === slot.player.id}
                  positionStyle={`left:${pitchX(slot.x, slot.y)}%; top:${pitchY(slot.y)}%`}
                  onfocus={(event) => {
                    focusPlayerId = slot.player.id
                    benchFocused = false
                    revealName(event)
                  }}
                  onmouseenter={revealName}
                  onclick={() => activatePlayer(slot.player)}
                />
              {/each}
              {@render strengthBadge()}
            </div>

          {/if}

          {#if view === 'plan'}
            <BenchDrawer
              bench={lineup.bench}
              reserve={lineup.reserve ?? []}
              open={benchFocused}
              selectedId={anchorId}
              onfocus={(player) => {
                benchFocused = true
                focusPlayerId = player.id
              }}
              onactivate={activatePlayer}
              onleave={() => (benchFocused = false)}
            />
          {/if}
        </div>

        <div class="plan-crest" aria-hidden="true">
          <img src={career.club.logo} alt="" onerror={hideBrokenImage} />
        </div>
      </div>
    {/if}
  </main>


  {#if seasonReview && review}
    <div class="match-result season-review">
      <section class="review-card" aria-label="Итоги сезона">
        <div class="review-head">
          <span class="eyebrow">
            {reviewStep === 0
              ? `Итоги сезона · ${season.season_start.slice(0, 4)}`
              : 'Новый сезон'}
          </span>
          <div class="review-title-row">
            <h2>{reviewStep === 0 ? review.league.name : review.next.league.name}</h2>
            {#if reviewStep === 0 && ownRow}
              <span class="review-place">
                {ownRow.position}-е место · {ownRow.points}
                {plural(ownRow.points, 'очко', 'очка', 'очков')}
              </span>
            {:else if reviewStep === 1}
              <span class="review-place">{nextSeasonLabel()}</span>
            {/if}
          </div>
        </div>

        {#if reviewStep === 0}
          <div class="review-table-wrap">
            <div class="review-table">
              <div class="review-row review-row-head">
                <span>#</span>
                <span>Клуб</span>
                <span>И</span>
                <span>+/-</span>
                <span>О</span>
              </div>
              {#each review.standings as row (row.club_id)}
                <div
                  class="review-row"
                  class:is-club={row.club_id === career.club.id}
                  class:is-up={review.promoted.some((club) => club.id === row.club_id)}
                  class:is-down={review.relegated.some((club) => club.id === row.club_id)}
                >
                  <span class="review-pos">{row.position}</span>
                  <span class="review-club">
                    <img src={row.club_logo} alt="" onerror={hideBrokenImage} />
                    <span>{row.club_name}</span>
                  </span>
                  <span>{row.played}</span>
                  <span>{row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}</span>
                  <span class="review-points">{row.points}</span>
                </div>
              {/each}
            </div>
          </div>

          <div class="review-zones">
            {#if review.promoted.length}
              <div class="review-zone is-up">
                <span class="review-zone-label">
                  Поднялись в {review.promoted_to.name}
                </span>
                <div class="review-chips">
                  {#each review.promoted as club (club.id)}
                    <span class="review-chip">
                      <img src={club.logo} alt="" onerror={hideBrokenImage} />
                      {club.name}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}
            {#if review.relegated.length}
              <div class="review-zone is-down">
                <span class="review-zone-label">
                  Вылетели в {review.relegated_to.name}
                </span>
                <div class="review-chips">
                  {#each review.relegated as club (club.id)}
                    <span class="review-chip">
                      <img src={club.logo} alt="" onerror={hideBrokenImage} />
                      {club.name}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}
          </div>

          <button
            class="result-continue"
            data-nav
            data-autofocus
            onclick={advanceSeasonReview}
          >
            <span>Далее</span>
            <span class="result-key">A</span>
          </button>
        {:else}
          <div
            class="review-transition"
            class:is-up={review.movement === 'up'}
            class:is-down={review.movement === 'down'}
            class:is-stay={review.movement === null}
          >
            <span class="review-move-arrow">
              {review.movement === 'up' ? '↑' : review.movement === 'down' ? '↓' : '→'}
            </span>
            <img class="review-move-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
            <div class="review-move-copy">
              <strong>{career.club.name}</strong>
              <span>
                {review.movement === 'up'
                  ? 'Повышение в'
                  : review.movement === 'down'
                    ? 'Вылет в'
                    : 'Остались в'}
                {review.next.league.name}
              </span>
            </div>
          </div>

          <div class="review-next-grid">
            {#if review.next.from_above.length}
              <div class="review-next-col">
                <span class="review-next-label">
                  Пришли из {review.next.above.name}
                </span>
                {#each review.next.from_above as item (item.club.id)}
                  <div class="review-next-row">
                    <img src={item.club.logo} alt="" onerror={hideBrokenImage} />
                    <span>{item.club.name}</span>
                    <small>{item.league.name}</small>
                  </div>
                {/each}
              </div>
            {/if}
            {#if review.next.from_below.length}
              <div class="review-next-col">
                <span class="review-next-label">
                  Пришли из {review.next.below.name}
                </span>
                {#each review.next.from_below as item (item.club.id)}
                  <div class="review-next-row">
                    <img src={item.club.logo} alt="" onerror={hideBrokenImage} />
                    <span>{item.club.name}</span>
                    <small>{item.league.name}</small>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

          <button
            class="result-continue"
            data-nav
            data-autofocus
            onclick={startNewSeason}
          >
            <span>Начать новый сезон</span>
            <span class="result-key">A</span>
          </button>
        {/if}
      </section>
    </div>
  {/if}

  {#if matchSimOpen && matchSimSetup}
    <MatchScreen
      phase={matchSimPhase}
      minute={matchSimMinute}
      setup={matchSimSetup}
      simulation={matchSimResult}
      loading={matchSimLoading}
      error={matchSimError || saveError}
    />
  {/if}

  {#if matchdayOpen && matchdayData}
    <MatchdayScreen step={matchdayStep} matchday={matchdayData} clubId={career.club.id} />
  {/if}

  <Controls
    {hints}
    showDefaults={false}
    note={matchdayOpen
      ? matchdayStep === 'results'
        ? 'Результаты дня'
        : 'Таблица после тура'
      : matchSimOpen
        ? matchSimPhase === 'live'
          ? 'Симуляция · 1 минута в секунду'
          : 'Симуляция матча'
        : saving
          ? 'Сохранение…'
          : playing
            ? 'Матч идёт…'
            : swapping
              ? 'Обмен…'
              : `${career.club.name} · ${formatTimestamp(career.updated_at)}`}
  />
</div>
