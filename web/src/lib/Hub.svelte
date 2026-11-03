<script>
  import { onMount, tick } from 'svelte'
  import { slide } from 'svelte/transition'
  import {
    registerBack,
    registerCycle,
    registerDetails,
    registerPrimary,
    registerReset,
    registerSave,
    registerStep,
    registerTabs,
    registerView,
  } from './actions.js'
  import { api } from './api.js'
  import BenchDrawer from './BenchDrawer.svelte'
  import Controls from './Controls.svelte'
  import Icon from './Icon.svelte'
  import PlayerCard from './PlayerCard.svelte'
  import Scouting from './Scouting.svelte'
  import Tabs from './Tabs.svelte'
  import TransferHistory from './TransferHistory.svelte'
  import TransferPlayers from './TransferPlayers.svelte'
  import TransferOfferModal from './TransferOfferModal.svelte'
  import IncomingOfferModal from './IncomingOfferModal.svelte'
  import { focusElement, focusFirst, inputDevice } from './input.js'
  import {
    AMOUNT_PLACES,
    INFO_LABELS,
    attributePages,
    centreTabs,
    detailPages,
    planTabs,
    squadTiles,
    tabs,
  } from './career/constants/hub.js'
  import {
    OFFER_KIND_LABELS,
    OFFER_STATUS_LABELS,
    POSITION_BADGES,
    TRANSFER_AGE,
    TRANSFER_CENTRE_TABS,
    TRANSFER_GROUP_OPTIONS,
    TRANSFER_POSITIONS,
    TRANSFER_STATUS_OPTIONS,
    transferHubCards,
  } from './career/constants/transfers.js'
  import { OSK_LIMIT, OSK_ROWS, REPORT_PAGE_SIZE } from './career/constants/scouting.js'
  import { pitchX, pitchY } from './career/utils/pitch.js'
  import { addDay, daysBetween, nextSeasonLabel } from './career/utils/dates.js'
  import {
    average,
    currentRole,
    infoValues,
    ratingAt,
    starCount,
    targetInfo,
    teamAfterSwap,
  } from './career/utils/squad.js'
  import {
    ownRow as findOwnRow,
    tableRound as computeTableRound,
    tableRows as computeTableRows,
  } from './career/utils/table.js'
  import {
    trackDays as computeTrackDays,
    trackIndex as computeTrackIndex,
    trackShift as computeTrackShift,
    trackWidth as computeTrackWidth,
  } from './career/utils/calendar.js'
  import {
    buildTransferParams,
    transferFieldLabel,
    transferFiltersActive as computeTransferFiltersActive,
    transferPositionShort,
    transferValueMeta,
  } from './career/utils/transfers.js'
  import { createMatchState } from './career/state/match.svelte.js'
  import ContractTerms from './career/shared/ContractTerms.svelte'
  import RadarChart from './career/shared/RadarChart.svelte'
  import StrengthBadge from './career/shared/StrengthBadge.svelte'
  import CentreInfoRow from './career/shared/CentreInfoRow.svelte'
  import CentreProfile from './career/shared/CentreProfile.svelte'
  import SquadActions from './career/shared/SquadActions.svelte'
  import CentreRoster from './career/shared/CentreRoster.svelte'
  import PlayerBlock from './career/shared/PlayerBlock.svelte'
  import CentreTab from './career/centre/CentreTab.svelte'
  import SquadOverview from './career/squad/SquadOverview.svelte'
  import SquadCentre from './career/squad/SquadCentre.svelte'
  import PlanView from './career/squad/PlanView.svelte'
  import NumberScreen from './career/squad/NumberScreen.svelte'
  import ReleaseScreen from './career/squad/ReleaseScreen.svelte'
  import AmountKeypad from './career/squad/AmountKeypad.svelte'
  import NegotiationScreen from './career/squad/NegotiationScreen.svelte'
  import TransfersTab from './career/transfers/TransfersTab.svelte'
  import SeasonReview from './career/match/SeasonReview.svelte'
  import MatchSimulationOverlay from './career/match/MatchSimulationOverlay.svelte'
  import MatchdayOverlay from './career/match/MatchdayOverlay.svelte'
  import {
    CONTRACT_ROLES,
    attributeGroups,
    compareTone,
    competitionLabel,
    contractRoleLabel,
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
    onaction,
    onexit,
  } = $props()

  const enabledTabs = tabs.filter((tab) => !tab.disabled).map((tab) => tab.id)

  let tab = $state('centre')
  let view = $state('overview')
  let detailsPage = $state(0)
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
  let transfersView = $state('hub')
  let networkMode = $state('scouts')
  let networkEntryId = $state(null)
  let networkBackToHub = $state(false)
  let networkHints = $state([])
  let historyHints = $state([])
  let reportPage = $state(0)
  let scoutPickerOpen = $state(false)
  let scoutPickerPlayer = $state(null)
  let scoutConfirm = $state(null)
  let transferCentreTab = $state('shortlist')
  let transferResultView = $state('grid')
  let transferCentreView = $state('grid')
  let transferSearchSelectedId = $state(null)
  let transferCentreSelectedId = $state(null)
  let transferSearchActionsOpen = $state(false)
  let transferCentreActionsOpen = $state(false)
  let transferFilters = $state({
    name: '',
    group: '',
    position: '',
    ageMin: null,
    ageMax: null,
    citizenship: '',
    country: '',
    league: '',
    club: '',
    status: '',
  })
  let transferEditing = $state(null)
  let transferRoleRow = $state('group')
  let transferAgeRow = $state('ageMin')
  let transferResults = $state([])
  let transferTotal = $state(0)
  let transferHasMore = $state(false)
  let transferLoading = $state(false)
  let transferError = $state('')
  let transferCountries = $state([])
  let transferLeagues = $state([])
  let transferClubs = $state([])
  let transferSearchToken = 0
  let transferOffer = $state(null)
  let transferOfferPlayer = $state(null)
  let transferOfferBackView = $state('results')
  let transferOfferModalId = $state(null)
  let incomingOfferModalId = $state(null)
  let incomingCounterOffer = $state(null)
  let incomingCounterPlayer = $state(null)
  let transferContractPlayerId = $state(null)
  let transferContractOfferId = $state(null)
  let transferContractFallback = $state(null)
  let transferContractBackView = $state('centre')
  let transferContractDraft = $state(null)
  let oskOpen = $state(false)
  let oskText = $state('')

  let summary = $derived(career.squad.summary)
  let lineup = $derived(career.squad.lineup)
  let season = $derived(career.season)
  let review = $derived(season?.review ?? null)
  let nextMatch = $derived(season?.next ?? null)
  let ownRow = $derived(findOwnRow(season?.standings, career.club.id))
  let tableRows = $derived(computeTableRows(season?.standings, ownRow))
  let tableRound = $derived(computeTableRound(season))
  const match = createMatchState({
    getCareer: () => career,
    getNextMatch: () => nextMatch,
    getSeason: () => season,
    getReview: () => review,
    getPlaying: () => playing,
    getSaveError: () => saveError,
    onpreview,
    onsimulate,
    onplay,
    onadvance,
    onnextseason,
    focusFirst,
  })

  let centreAction = $derived(
    match.advancing
      ? 'Сохраняем дату…'
      : match.simulating
        ? 'Остановить'
        : playing
          ? 'Матч идёт…'
          : !nextMatch
            ? 'Перейти в следующий сезон'
            : match.isMatchDay
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
  let negotiationState = $derived(centrePlayer?.negotiation ?? null)
  let negotiationTerms = $derived(
    negotiationState?.offer ?? negotiationState?.counter ?? null,
  )
  let amountGroups = $derived.by(() => {
    const digits = amountDigits.padStart(9, '0').slice(-9)
    return [
      { digits: digits.slice(0, 3), start: 0 },
      { digits: digits.slice(3, 6), start: 3 },
      { digits: digits.slice(6, 9), start: 6 },
    ]
  })
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
  let projectedTeamAverage = $derived(
    teamAfterSwap(comparing, teamAverage, lineup, anchorPlayer, focusedPlayer),
  )
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

  let transferFiltersActive = $derived(computeTransferFiltersActive(transferFilters))
  let transferCentre = $derived(
    career.transfers ?? {
      shortlist: [],
      sent_offers: [],
      received_offers: [],
      listed: [],
      loaned: [],
    },
  )
  let transferCentrePlayers = $derived(
    transferCentreTab === 'sent'
      ? (transferCentre.sent_offers ?? [])
      : transferCentreTab === 'received'
        ? (transferCentre.received_offers ?? [])
        : transferCentreTab === 'listed'
          ? (transferCentre.listed ?? [])
          : transferCentreTab === 'loaned'
            ? (transferCentre.loaned ?? [])
            : (transferCentre.shortlist ?? []),
  )
  let transferCentreIsSent = $derived(transferCentreTab === 'sent')
  let transferCentreIsOffer = $derived(transferCentreTab === 'received')
  let transferCentreIsList = $derived(
    ['shortlist', 'listed', 'loaned'].includes(transferCentreTab),
  )
  let sentOffers = $derived(transferCentre.sent_offers ?? [])
  let receivedOffers = $derived(transferCentre.received_offers ?? [])
  let receivedUnread = $derived(
    receivedOffers.filter((offer) => offer.unread).length,
  )
  let incomingOfferModal = $derived(
    receivedOffers.find((offer) => offer.offer_id === incomingOfferModalId) ?? null,
  )
  let transferOfferModal = $derived(
    sentOffers.find((offer) => offer.offer_id === transferOfferModalId) ?? null,
  )
  let transferContractOffer = $derived(
    sentOffers.find((offer) => offer.offer_id === transferContractOfferId) ?? null,
  )
  let transferContractPlayer = $derived.by(() => {
    if (!transferContractPlayerId) return null
    const lists = [
      sentOffers,
      transferResults,
      transferCentre.shortlist ?? [],
      transferCentre.listed ?? [],
      transferCentre.loaned ?? [],
    ]
    for (const list of lists) {
      const found = list.find((player) => player.id === transferContractPlayerId)
      if (found) return found
    }
    return transferContractFallback
  })
  let transferContractState = $derived(
    career.transfers?.contracts?.[transferContractPlayerId] ??
      transferContractPlayer?.transfer_contract ??
      null,
  )
  let transferContractTerms = $derived(
    transferContractState?.agreed ??
      transferContractState?.counter ??
      transferContractState?.offer ??
      transferContractDraft,
  )
  let transferContractFee = $derived(
    Number(transferContractOffer?.amount ?? transferContractState?.fee ?? 0),
  )
  let transferContractBalanceAfter = $derived(
    Number(finance?.balance ?? 0) - transferContractFee,
  )
  let transferCentreTitle = $derived(
    TRANSFER_CENTRE_TABS.find((item) => item.id === transferCentreTab)?.label ?? 'Список',
  )
  let transferCentreEmpty = $derived(
    transferCentreTab === 'sent'
      ? 'Отправленных предложений пока нет.'
      : transferCentreTab === 'received'
        ? 'Полученных предложений пока нет.'
        : transferCentreTab === 'listed'
          ? 'Никого нет на трансфере. Отметьте игрока в центре составов.'
          : transferCentreTab === 'loaned'
            ? 'Никто не выставлен в аренду. Отметьте игрока в центре составов.'
            : 'Шортлист пуст. Добавьте игрока из поиска или отчёта скаута.',
  )
  let scouting = $derived(career.scouting ?? null)
  let reportFeed = $derived([
    ...(scouting?.reports ?? []),
    ...(scouting?.recommendations ?? []),
  ])
  let reportPageCount = $derived(
    Math.max(1, Math.ceil(reportFeed.length / REPORT_PAGE_SIZE)),
  )
  let reportPageEntries = $derived(
    reportFeed.slice(
      reportPage * REPORT_PAGE_SIZE,
      reportPage * REPORT_PAGE_SIZE + REPORT_PAGE_SIZE,
    ),
  )
  let scoutPickerScouts = $derived(scouting?.scouts ?? [])

  let hints = $derived.by(() => {
    const start = { gamepad: ['Start'], keyboard: ['S'], label: 'Сохранить' }
    const sections = { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Разделы' }
    if (match.matchdayOpen) {
      return match.matchdayStep === 'results'
        ? [
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Таблица' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'В хаб' },
          ]
        : [
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Продолжить' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'К результатам' },
          ]
    }
    if (match.matchSimOpen) {
      if (match.matchSimPhase === 'live') {
        return [
          {
            gamepad: ['Y'],
            keyboard: ['R'],
            label: match.matchSimLoading ? 'Симуляция…' : 'Пропустить',
          },
        ]
      }
      if (match.matchSimPhase === 'done') {
        return [{ gamepad: ['A'], keyboard: ['Enter'], label: 'Далее' }]
      }
      return [
        {
          gamepad: ['A'],
          keyboard: ['Enter'],
          label: match.matchSimLoading ? 'Загрузка…' : 'Начать симуляцию',
        },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
      ]
    }
    if (match.seasonReview) {
      return [
        {
          gamepad: ['A'],
          keyboard: ['Enter'],
          label: match.reviewStep === 0 ? 'Далее' : 'Начать новый сезон',
        },
        {
          gamepad: ['B'],
          keyboard: ['Esc'],
          label: match.reviewStep === 1 ? 'К таблице' : 'Закрыть',
        },
      ]
    }
    if (match.simulating || match.advancing) {
      return [{ gamepad: ['A'], keyboard: ['Enter'], label: centreAction }]
    }
    if (tab === 'transfers') {
      if (transfersView === 'incomingCounter') {
        return [
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
          { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Отправить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'contractAmount') {
        return [
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
          { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'contract') {
        if (transferContractState?.status === 'pending') {
          return [
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Вернуться' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transferContractState?.status === 'accepted') {
          return [
            {
              gamepad: ['A'],
              keyboard: ['Enter'],
              label:
                transferContractState.affordable === false
                  ? 'Недостаточно средств'
                  : 'Подписать',
            },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        return [
          { gamepad: ['D-pad'], keyboard: ['↑', '↓'], label: 'Условие' },
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Изменить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'offerAmount') {
        return [
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
          { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'offer') {
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Условие' },
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Изменить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'network') {
        return networkHints
      }
      if (transfersView === 'history') {
        return historyHints
      }
      if (scoutPickerOpen) {
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Скаут' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Поручить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (oskOpen) {
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Буква' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Ввод' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'hub') {
        return [
          sections,
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Открыть' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'В меню' },
        ]
      }
      if (transfersView === 'filters') {
        if (transferEditing) {
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Значение' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Готово' },
          ]
        }
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Фильтр' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Изменить' },
          { gamepad: ['X'], keyboard: ['X'], label: 'Сброс' },
          { gamepad: ['Y'], keyboard: ['Y'], label: 'Начать поиск' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (transfersView === 'centre') {
        if (incomingOfferModalId) {
          const offer = incomingOfferModal
          const hasAction =
            offer && ['pending'].includes(offer.status)
          if (!hasAction) {
            return [{ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' }]
          }
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transferOfferModalId) {
          const offer = transferOfferModal
          const hasAction =
            offer &&
            offer.status !== 'pending' &&
            !offer.signed &&
            !(offer.status === 'refused' && !offer.can_offer_again)
          if (!hasAction) {
            return [{ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' }]
          }
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transferCentreActionsOpen) {
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        const list = [
          { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Вкладки' },
        ]
        if (transferCentreIsSent || transferCentreTab === 'received') {
          list.push({ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' })
          list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' })
        } else if (transferCentreIsList) {
          list.push({ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' })
          list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' })
          list.push({ gamepad: ['Y'], keyboard: ['Y'], label: 'Вид' })
        }
        list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
        return list
      }
      if (transfersView === 'results') {
        if (transferSearchActionsOpen) {
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
          { gamepad: ['Y'], keyboard: ['Y'], label: 'Вид' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      return [
        { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
        { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
      ]
    }
    if (tab === 'squad' && view === 'amount') {
      return [
        { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
        { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
        { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
      ]
    }
    if (tab === 'squad' && view === 'negotiation') {
      if (negotiationState?.status === 'pending') {
        return [
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Вернуться' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          start,
        ]
      }
      if (negotiationState?.status === 'accepted') {
        return [
          {
            gamepad: ['A'],
            keyboard: ['Enter'],
            label:
              negotiationState.affordable === false
                ? 'Недостаточно средств'
                : 'Подписать',
          },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          start,
        ]
      }
      return [
        { gamepad: ['D-pad'], keyboard: ['↑', '↓'], label: 'Условие' },
        { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
        { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        start,
      ]
    }
    if (tab === 'squad' && view === 'number') {
      return [
        { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Номер' },
        { gamepad: ['A'], keyboard: ['Enter'], label: 'Сохранить' },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
      ]
    }
    if (tab === 'squad' && view === 'release') {
      return [
        { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Выбор' },
        { gamepad: ['A'], keyboard: ['Enter'], label: 'Подтвердить' },
        { gamepad: ['B'], keyboard: ['Esc'], label: 'Отмена' },
      ]
    }
    if (tab === 'squad' && view === 'centre') {
      const list = [{ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' }]
      if (centreOpenId) {
        list[0].label = 'Пункт'
        list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Действие' })
        list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Закрыть' })
        list.push(start)
        return list
      }
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
        label: match.isMatchDay ? 'Выбрать' : centreAction,
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
    const stopView = registerView(handleViewToggle)
    const stopStep = registerStep(handleStep)
    const stopReset = registerReset(handleReset)
    tick().then(focusFirst)
    return () => {
      stopBack()
      stopTabs()
      stopSave()
      stopDetails()
      stopPrimary()
      stopCycle()
      stopView()
      stopStep()
      stopReset()
      match.dispose()
      if (oskTimer) clearTimeout(oskTimer)
    }
  })

  function handleSave() {
    if (
      !saving &&
      !match.seasonReview &&
      !match.simulating &&
      !match.advancing &&
      !match.matchSimOpen &&
      !match.matchdayOpen
    ) {
      onsave()
    }
  }

  function activeEditField() {
    return transferEditing === 'positionRole' ? transferRoleRow : transferEditing
  }

  function inlineOptions() {
    const field = activeEditField()
    if (field === 'group') return TRANSFER_GROUP_OPTIONS
    if (field === 'position') {
      return [
        { value: '', label: 'Любое' },
        ...TRANSFER_POSITIONS.map((position) => ({
          value: position,
          label: positionLabel(position),
          badge: POSITION_BADGES[position] ?? '—',
        })),
      ]
    }
    if (field === 'citizenship') {
      return [
        { value: '', label: 'Любое' },
        ...transferCountries.map((country) => ({
          value: country.name,
          label: country.name,
          logo: country.flag,
        })),
      ]
    }
    if (field === 'country') {
      return [
        { value: '', label: 'Любая' },
        ...transferCountries.map((country) => ({
          value: country.id,
          label: country.name,
          logo: country.flag,
        })),
      ]
    }
    if (field === 'league') {
      const leagues = transferFilters.country
        ? transferLeagues.filter((league) => league.country_id === transferFilters.country)
        : transferLeagues
      return [
        { value: '', label: 'Любая' },
        ...leagues.map((league) => ({
          value: league.id,
          label: league.name,
          logo: league.logo,
        })),
      ]
    }
    if (field === 'club') {
      if (!transferFilters.league) {
        return [{ value: '', label: 'Сначала выберите лигу' }]
      }
      return [
        { value: '', label: 'Любой' },
        ...transferClubs.map((club) => ({
          value: club.id,
          label: club.name,
          logo: club.logo,
        })),
      ]
    }
    if (field === 'status') return TRANSFER_STATUS_OPTIONS
    return []
  }

  async function runTransferSearch(reset = true) {
    const token = ++transferSearchToken
    transferError = ''
    if (reset) {
      transferResults = []
      transferTotal = 0
      transferHasMore = false
    }
    transferLoading = true
    try {
      const data = await api.transferSearch(
        career.id,
        buildTransferParams(transferFilters, reset ? 0 : transferResults.length),
      )
      if (token !== transferSearchToken) return
      transferResults = reset ? data.items : [...transferResults, ...data.items]
      transferTotal = data.total
      transferHasMore = data.has_more
    } catch (caught) {
      if (token === transferSearchToken) transferError = caught.message
    } finally {
      if (token === transferSearchToken) transferLoading = false
    }
  }

  function loadMoreTransfers() {
    if (!transferLoading && transferHasMore) runTransferSearch(false)
  }

  async function ensureTransferOptions() {
    if (transferCountries.length && transferLeagues.length) return
    try {
      const [countries, leagues] = await Promise.all([api.countries(), api.leagues()])
      transferCountries = countries
      transferLeagues = leagues
    } catch (caught) {
      transferError = caught.message
    }
  }

  async function openTransferFilters() {
    transfersView = 'filters'
    transferEditing = null
    transferSearchActionsOpen = false
    oskOpen = false
    await ensureTransferOptions()
    await tick()
    focusFirst()
  }

  async function startTransferSearch() {
    if (transfersView !== 'filters') return
    transferEditing = null
    transfersView = 'results'
    transferSearchSelectedId = null
    transferSearchActionsOpen = false
    await ensureTransferOptions()
    await runTransferSearch(true)
    await tick()
    focusFirst()
  }

  async function openTransferCentre() {
    transfersView = 'centre'
    transferCentreTab = 'shortlist'
    transferCentreSelectedId = transferCentre.shortlist?.[0]?.id ?? null
    transferCentreActionsOpen = false
    transferOfferModalId = null
    incomingOfferModalId = null
    transferError = ''
    await tick()
    focusFirst()
  }

  function setTransferCentreTab(next, focus = 'tab') {
    if (transferCentreTab === next) return
    transferCentreTab = next
    transferCentreSelectedId = null
    transferCentreActionsOpen = false
    transferOfferModalId = null
    incomingOfferModalId = null
    tick().then(() => {
      if (focus === 'tab') {
        const tabElement = document.querySelector(
          `.centre-tab[data-centre-tab="${transferCentreTab}"]`,
        )
        if (tabElement) {
          focusElement(tabElement)
          return
        }
      }
      focusFirst()
    })
  }

  function switchTransferCentreTab(direction) {
    const index = TRANSFER_CENTRE_TABS.findIndex((item) => item.id === transferCentreTab)
    const offset = direction === 'right' ? 1 : -1
    const next =
      TRANSFER_CENTRE_TABS[
        (index + offset + TRANSFER_CENTRE_TABS.length) % TRANSFER_CENTRE_TABS.length
      ]
    setTransferCentreTab(next.id, 'tab')
  }

  function offerStatusLabel(status) {
    return OFFER_STATUS_LABELS[status] ?? status
  }

  function offerKindLabel(kind) {
    return OFFER_KIND_LABELS[kind] ?? kind
  }

  function contractStatusLabel(status) {
    if (status === 'pending') return 'переговоры'
    if (status === 'counter') return 'контрпредложение'
    if (status === 'accepted') return 'согласован'
    if (status === 'signed') return 'подписан'
    return null
  }

  function openTransferOffer(player, kind = 'transfer', preset = null) {
    if (!player) return
    const clause = Number(player.release_clause) || 0
    const value = Number(player.market_value) || clause || 1_000_000
    const loanFee = Math.max(
      10_000,
      Math.round((value * 0.05) / 10_000) * 10_000,
    )
    transferOfferPlayer = player
    transferOfferBackView = transfersView
    transferOffer = {
      playerId: player.id,
      kind,
      amount: preset?.amount ?? (clause || value),
      loan_fee: preset?.loan_fee ?? loanFee,
      wage_share: preset?.wage_share ?? 50,
      buyout: Boolean(preset?.buyout),
    }
    transferOfferModalId = null
    transferSearchActionsOpen = false
    transferCentreActionsOpen = false
    scoutPickerOpen = false
    scoutPickerPlayer = null
    transfersView = 'offer'
    tick().then(focusFirst)
  }

  function closeTransferOffer() {
    transferOffer = null
    transferOfferPlayer = null
    amountField = null
    transfersView = transferOfferBackView || 'centre'
    tick().then(focusFirst)
  }

  function contractDraftFrom(player) {
    if (!player) return null
    const state = player.transfer_contract
    const source =
      state?.offer ??
      state?.counter ??
      player.contract_defaults ?? {
        years: 3,
        weekly_wage: player.weekly_wage ?? 1_000,
        squad_role: 'rotation',
        release_clause: Math.round((player.market_value ?? 1_000_000) * 1.2),
      }
    return { ...source }
  }

  function openTransferContractFromOffer(offer) {
    if (!offer) return
    transferContractPlayerId = offer.id
    transferContractOfferId = offer.offer_id
    transferContractFallback = offer
    transferContractBackView = transfersView
    transferContractDraft = contractDraftFrom(offer)
    transferOfferModalId = null
    transferSearchActionsOpen = false
    transferCentreActionsOpen = false
    transfersView = 'contract'
    tick().then(focusFirst)
  }

  function openTransferContractFromPlayer(player) {
    if (!player) return
    transferContractPlayerId = player.id
    transferContractOfferId = player.latest_offer?.can_negotiate
      ? player.latest_offer.offer_id
      : null
    transferContractFallback = player
    transferContractBackView = transfersView
    transferContractDraft = contractDraftFrom(player)
    transferSearchActionsOpen = false
    transferCentreActionsOpen = false
    transfersView = 'contract'
    tick().then(focusFirst)
  }

  function closeTransferContract() {
    transferContractPlayerId = null
    transferContractOfferId = null
    transferContractFallback = null
    transferContractDraft = null
    amountField = null
    transfersView = transferContractBackView || 'centre'
    tick().then(focusFirst)
  }

  function contractWageStep() {
    const base =
      transferContractState?.terms?.weekly_wage ??
      transferContractPlayer?.contract_defaults?.weekly_wage ??
      transferContractPlayer?.weekly_wage ??
      1_000
    return Math.max(1_000, Math.round((base * 0.1) / 100) * 100)
  }

  function contractClauseStep() {
    const base = transferContractPlayer?.market_value ?? 1_000_000
    return Math.max(100_000, Math.round((base * 0.05) / 100_000) * 100_000)
  }

  function adjustTransferContractField(field, step) {
    if (!transferContractDraft) return
    if (field === 'years') {
      transferContractDraft.years = Math.min(
        5,
        Math.max(1, transferContractDraft.years + step),
      )
    } else if (field === 'weekly_wage') {
      transferContractDraft.weekly_wage = Math.max(
        1_000,
        Math.min(2_000_000, transferContractDraft.weekly_wage + step * contractWageStep()),
      )
    } else if (field === 'release_clause') {
      transferContractDraft.release_clause = Math.max(
        0,
        transferContractDraft.release_clause + step * contractClauseStep(),
      )
    } else if (field === 'squad_role') {
      const index = Math.max(
        0,
        CONTRACT_ROLES.findIndex((role) => role.id === transferContractDraft.squad_role),
      )
      const next = (index + step + CONTRACT_ROLES.length) % CONTRACT_ROLES.length
      transferContractDraft.squad_role = CONTRACT_ROLES[next].id
    }
    transferContractDraft = { ...transferContractDraft }
  }

  function openTransferContractAmount(field) {
    if (!transferContractDraft || !field) return
    const value = Math.max(
      0,
      Math.min(999_999_999, Math.round(Number(transferContractDraft[field]) || 0)),
    )
    amountField = field
    amountDigits = String(value).padStart(9, '0')
    const firstDigit = amountDigits.search(/[1-9]/)
    amountIndex = firstDigit === -1 ? 8 : firstDigit
    transfersView = 'contractAmount'
    tick().then(focusFirst)
  }

  function closeTransferContractAmount() {
    amountField = null
    transfersView = 'contract'
    tick().then(focusFirst)
  }

  function finishTransferContractAmount() {
    if (!transferContractDraft || !amountField) return
    const value = Math.max(
      0,
      Math.min(999_999_999, Number.parseInt(amountDigits || '0', 10) || 0),
    )
    if (amountField === 'weekly_wage') {
      transferContractDraft.weekly_wage = Math.max(1_000, Math.min(2_000_000, value))
    } else {
      transferContractDraft.release_clause = Math.max(0, value)
    }
    transferContractDraft = { ...transferContractDraft }
    amountField = null
    transfersView = 'contract'
    tick().then(focusFirst)
  }

  async function submitTransferContract() {
    if (!transferContractPlayer || !transferContractDraft || centreActionBusy) return
    if (transferContractState?.status === 'accepted') {
      await signTransferContract()
      return
    }
    centreActionBusy = true
    const updated = await onaction({
      type: 'transfer_contract',
      player_id: transferContractPlayer.id,
      offer_id: transferContractOfferId || undefined,
      ...transferContractDraft,
    })
    centreActionBusy = false
    if (!updated) return
    await tick()
    focusFirst()
  }

  async function acceptTransferContractCounter() {
    if (!transferContractPlayer || centreActionBusy) return
    centreActionBusy = true
    const updated = await onaction({
      type: 'transfer_accept_counter',
      player_id: transferContractPlayer.id,
    })
    centreActionBusy = false
    if (!updated) return
    await tick()
    focusFirst()
  }

  async function signTransferContract() {
    if (!transferContractPlayer || centreActionBusy) return
    if (transferContractState?.affordable === false) return
    centreActionBusy = true
    const updated = await onaction({
      type: 'transfer_sign',
      player_id: transferContractPlayer.id,
    })
    centreActionBusy = false
    if (!updated) return
    closeTransferContract()
  }

  function transferOfferBase() {
    return Math.max(
      Number(transferOfferPlayer?.release_clause) || 0,
      Number(transferOfferPlayer?.market_value) || 0,
      1_000_000,
    )
  }

  function transferOfferStep() {
    return Math.max(
      100_000,
      Math.round((transferOfferBase() * 0.05) / 100_000) * 100_000,
    )
  }

  function loanOfferStep() {
    return Math.max(
      10_000,
      Math.round((transferOfferBase() * 0.005) / 10_000) * 10_000,
    )
  }

  function adjustOfferField(field, step) {
    if (!transferOffer) return
    if (field === 'amount') {
      if (transferOffer.buyout) return
      transferOffer.amount = Math.max(
        0,
        Math.min(999_999_999, transferOffer.amount + step * transferOfferStep()),
      )
    } else if (field === 'loan_fee') {
      transferOffer.loan_fee = Math.max(
        0,
        Math.min(999_999_999, transferOffer.loan_fee + step * loanOfferStep()),
      )
    } else if (field === 'wage_share') {
      transferOffer.wage_share = Math.max(
        0,
        Math.min(100, transferOffer.wage_share + step * 5),
      )
    }
    transferOffer = { ...transferOffer }
  }

  function toggleOfferBuyout() {
    if (!transferOffer || transferOffer.kind !== 'transfer') return
    if (!(Number(transferOfferPlayer?.release_clause) > 0)) return
    transferOffer.buyout = !transferOffer.buyout
    transferOffer = { ...transferOffer }
  }

  function openOfferAmount(field) {
    if (!transferOffer || !field) return
    if (transferOffer.buyout && field === 'amount') return
    const current =
      field === 'loan_fee' ? transferOffer.loan_fee : transferOffer.amount
    const value = Math.max(
      0,
      Math.min(999_999_999, Math.round(Number(current) || 0)),
    )
    amountField = field
    amountDigits = String(value).padStart(9, '0')
    const firstDigit = amountDigits.search(/[1-9]/)
    amountIndex = firstDigit === -1 ? 8 : firstDigit
    transfersView = 'offerAmount'
    tick().then(focusFirst)
  }

  function closeOfferAmount() {
    amountField = null
    transfersView = 'offer'
    tick().then(focusFirst)
  }

  function finishOfferAmount() {
    if (!transferOffer || !amountField) return
    const value = Math.max(
      0,
      Math.min(999_999_999, Number.parseInt(amountDigits || '0', 10) || 0),
    )
    if (amountField === 'loan_fee') transferOffer.loan_fee = value
    else transferOffer.amount = value
    transferOffer = { ...transferOffer }
    amountField = null
    transfersView = 'offer'
    tick().then(focusFirst)
  }

  function offerPayload() {
    const offer = transferOffer
    if (!offer) return null
    if (offer.kind === 'loan') {
      return {
        type: 'loan_offer',
        player_id: offer.playerId,
        amount: offer.loan_fee,
        loan_fee: offer.loan_fee,
        wage_share: offer.wage_share,
      }
    }
    const release = Number(transferOfferPlayer?.release_clause) || 0
    return {
      type: 'transfer_offer',
      player_id: offer.playerId,
      amount: offer.buyout ? release : offer.amount,
      buyout: offer.buyout,
    }
  }

  async function submitTransferOffer() {
    if (!transferOffer || centreActionBusy) return
    const payload = offerPayload()
    if (!payload) return
    centreActionBusy = true
    const updated = await onaction(payload)
    centreActionBusy = false
    if (!updated) return
    transferOffer = null
    transferOfferPlayer = null
    transferSearchActionsOpen = false
    transferCentreActionsOpen = false
    transfersView = 'centre'
    transferCentreTab = 'sent'
    transferCentreSelectedId = null
    await tick()
    focusFirst()
  }

  async function acceptTransferCounter(offer) {
    if (!offer || centreActionBusy) return
    centreActionBusy = true
    const updated = await onaction({
      type: 'accept_offer_counter',
      offer_id: offer.offer_id,
    })
    centreActionBusy = false
    if (!updated) return
    await tick()
    focusFirst()
  }

  function sentOfferCard(offerId) {
    return document.querySelector(`[data-offer-card="${offerId}"]`)
  }

  function openSentOfferModal(offer) {
    if (!offer) return
    transferOfferModalId = offer.offer_id
    tick().then(() => {
      const modal = document.querySelector('.tf-offer-modal')
      const action = modal?.querySelector('[data-nav]')
      focusElement(action ?? modal)
    })
  }

  function closeSentOfferModal() {
    const offerId = transferOfferModalId
    transferOfferModalId = null
    if (!offerId) return
    tick().then(() => focusElement(sentOfferCard(offerId)))
  }

  function reofferSentOffer(offer) {
    if (!offer) return
    const preset =
      offer.kind === 'loan'
        ? {
            loan_fee: offer.counter?.loan_fee ?? offer.loan_fee ?? offer.amount,
            wage_share: offer.counter?.wage_share ?? offer.wage_share,
          }
        : { amount: offer.counter?.amount ?? offer.amount }
    transferOfferModalId = null
    openTransferOffer(offer, offer.kind, preset)
  }

  async function acceptSentOfferCounter(offer) {
    if (!offer) return
    await acceptTransferCounter(offer)
    closeSentOfferModal()
  }

  function incomingOfferCard(offerId) {
    return document.querySelector(`[data-incoming-card="${offerId}"]`)
  }

  function openIncomingOfferModal(offer) {
    if (!offer) return
    incomingOfferModalId = offer.offer_id
    if (offer.unread) {
      onaction({ type: 'incoming_ack', offer_id: offer.offer_id })
    }
    tick().then(() => {
      const modal = document.querySelector('.tf-incoming-modal')
      const action = modal?.querySelector('[data-nav]')
      focusElement(action ?? modal)
    })
  }

  function closeIncomingOfferModal() {
    const offerId = incomingOfferModalId
    incomingOfferModalId = null
    if (!offerId) return
    tick().then(() => focusElement(incomingOfferCard(offerId)))
  }

  function focusReceivedTab() {
    const tabElement = document.querySelector(
      '.centre-tab[data-centre-tab="received"]',
    )
    if (tabElement) focusElement(tabElement)
    else focusFirst()
  }

  async function submitIncomingOffer(offer, type) {
    if (!offer || centreActionBusy) return
    centreActionBusy = true
    const updated = await onaction({ type, offer_id: offer.offer_id })
    centreActionBusy = false
    if (!updated) return
    incomingOfferModalId = null
    await tick()
    focusReceivedTab()
  }

  function startIncomingCounter(offer) {
    if (!offer) return
    incomingCounterOffer = offer
    incomingCounterPlayer = offer
    incomingOfferModalId = null
    const value = Math.max(
      0,
      Math.min(999_999_999, Math.round((Number(offer.amount) || 0) * 1.15)),
    )
    amountDigits = String(value).padStart(9, '0')
    const firstDigit = amountDigits.search(/[1-9]/)
    amountIndex = firstDigit === -1 ? 8 : firstDigit
    transfersView = 'incomingCounter'
    tick().then(focusFirst)
  }

  function closeIncomingCounter() {
    incomingCounterOffer = null
    incomingCounterPlayer = null
    transfersView = 'centre'
    tick().then(focusReceivedTab)
  }

  async function finishIncomingCounterAmount() {
    if (!incomingCounterOffer || centreActionBusy) return
    const value = Math.max(
      0,
      Math.min(999_999_999, Number.parseInt(amountDigits || '0', 10) || 0),
    )
    centreActionBusy = true
    const updated = await onaction({
      type: 'incoming_counter',
      offer_id: incomingCounterOffer.offer_id,
      amount: value,
    })
    centreActionBusy = false
    if (!updated) return
    incomingCounterOffer = null
    incomingCounterPlayer = null
    transfersView = 'centre'
    transferCentreTab = 'received'
    await tick()
    focusReceivedTab()
  }

  function focusTransferTile(field) {
    const target = field ? document.querySelector(`[data-filter="${field}"]`) : null
    if (target) focusElement(target)
    else focusFirst()
  }

  function openTransferHistory() {
    transfersView = 'history'
    historyHints = []
    tick().then(focusFirst)
  }

  function closeTransferHistory() {
    transfersView = 'hub'
    historyHints = []
    tick().then(focusFirst)
  }

  function openTransferNetwork(mode = 'scouts', entryId = null, backToHub = false) {
    transfersView = 'network'
    networkMode = mode
    networkEntryId = entryId
    networkBackToHub = backToHub
    networkHints = []
    tick().then(focusFirst)
  }

  function closeTransferNetwork() {
    transfersView = 'hub'
    networkMode = 'scouts'
    networkEntryId = null
    networkBackToHub = false
    networkHints = []
    transferError = ''
    tick().then(focusFirst)
  }

  function openReportsCenter(entry = null) {
    openTransferNetwork('reports', entry?.player?.id ?? null, true)
  }

  function shiftReport(direction) {
    if (reportPageCount <= 1) return
    const offset = direction === 'right' ? 1 : -1
    reportPage = (reportPage + offset + reportPageCount) % reportPageCount
    tick().then(focusFirst)
  }

  function openScoutPicker(player = null) {
    if (!player) return
    scoutPickerPlayer = player
    scoutPickerOpen = true
    tick().then(focusFirst)
  }

  function closeScoutPicker() {
    scoutPickerOpen = false
    scoutPickerPlayer = null
    tick().then(() => {
      const card = document.querySelector(
        `.tf-action[data-scout-action="assign"]`,
      )
      if (card) focusElement(card)
      else focusFirst()
    })
  }

  async function assignScout(scout) {
    if (!scoutPickerPlayer || scout.report) return
    const updated = await onaction({
      type: 'scout_assign',
      scout_id: scout.id,
      player_id: scoutPickerPlayer.id,
    })
    if (!updated) return
    closeScoutPicker()
    transferSearchActionsOpen = false
    transferCentreActionsOpen = false
  }

  function openTransferHub() {
    if (oskOpen) {
      closeOsk()
      return
    }
    if (transferEditing) {
      closeTransferEdit()
      return
    }
    if (transfersView === 'results') {
      transfersView = 'filters'
      tick().then(focusFirst)
      return
    }
    if (
      transfersView === 'filters' ||
      transfersView === 'centre' ||
      transfersView === 'history'
    ) {
      transfersView = 'hub'
      historyHints = []
      tick().then(focusFirst)
      return
    }
    setTab('centre')
  }

  function applyTransferField(field, value) {
    transferFilters[field] = value
    if (field === 'country') {
      transferFilters.league = ''
      transferFilters.club = ''
      transferClubs = []
    }
    if (field === 'league') {
      transferFilters.club = ''
      transferClubs = []
      if (value) {
        api
          .clubs(value)
          .then((clubs) => {
            if (transferFilters.league === value) transferClubs = clubs
          })
          .catch(() => {
            transferClubs = []
          })
      }
    }
  }

  function stepTransferField(field, delta) {
    const options = inlineOptions()
    if (!options.length) return
    const current = transferFilters[field]
    let index = options.findIndex((option) => option.value === current)
    if (index < 0) index = 0
    const next = options[(index + delta + options.length) % options.length]
    applyTransferField(field, next.value)
  }

  function stepTransferRange(field, delta) {
    const config = TRANSFER_AGE
    const minKey = 'ageMin'
    const maxKey = 'ageMax'
    const current = transferFilters[field]
    let next
    if (current === null) {
      next = delta > 0 ? config.min : config.max
    } else {
      next = current + delta
      if (next < config.min || next > config.max) next = null
    }
    transferFilters[field] = next
    if (
      transferFilters[minKey] !== null &&
      transferFilters[maxKey] !== null &&
      transferFilters[minKey] > transferFilters[maxKey]
    ) {
      if (field === minKey) transferFilters[maxKey] = transferFilters[minKey]
      else transferFilters[minKey] = transferFilters[maxKey]
    }
  }

  function stepActive(delta) {
    if (transferEditing === 'age') stepTransferRange(transferAgeRow, delta)
    else if (transferEditing === 'positionRole') stepTransferField(transferRoleRow, delta)
    else if (transferEditing) stepTransferField(transferEditing, delta)
  }

  function openTransferEdit(field) {
    if (field === 'name') {
      openOsk()
      return
    }
    transferEditing = field
    if (field === 'positionRole') transferRoleRow = 'group'
    if (field === 'age') transferAgeRow = 'ageMin'
  }

  function closeTransferEdit() {
    const field = transferEditing
    transferEditing = null
    tick().then(() => focusTransferTile(field))
  }

  function handleStep(direction) {
    if (tab !== 'transfers' || transfersView !== 'filters') return false
    if (oskOpen || !transferEditing) return false
    if (transferEditing === 'age') {
      if (direction === 'up' || direction === 'down') {
        transferAgeRow = transferAgeRow === 'ageMin' ? 'ageMax' : 'ageMin'
      } else {
        stepActive(direction === 'right' ? 1 : -1)
      }
      return true
    }
    if (transferEditing === 'positionRole') {
      if (direction === 'up' || direction === 'down') {
        transferRoleRow = transferRoleRow === 'group' ? 'position' : 'group'
          } else {
        stepActive(direction === 'right' ? 1 : -1)
      }
      return true
    }
    if (direction === 'left' || direction === 'right') stepActive(direction === 'right' ? 1 : -1)
    return true
  }

  function handleViewToggle() {
    if (tab !== 'transfers' || oskOpen) return false
    if (transfersView === 'filters') {
      startTransferSearch()
      return true
    }
    if (transfersView === 'results') {
      if (transferSearchActionsOpen) return true
      transferResultView = transferResultView === 'grid' ? 'list' : 'grid'
      return true
    }
    if (transfersView === 'centre') {
      if (
        transferCentreActionsOpen ||
        transferCentreIsOffer ||
        transferCentreIsSent
      ) {
        return true
      }
      transferCentreView = transferCentreView === 'grid' ? 'list' : 'grid'
      return true
    }
    return false
  }

  function handleReset() {
    if (tab !== 'transfers' || transfersView !== 'filters' || oskOpen) return false
    transferEditing = null
    resetTransferFilters()
    return true
  }

  function resetTransferFilters() {
    transferFilters = {
      name: '',
      group: '',
      position: '',
      ageMin: null,
      ageMax: null,
      citizenship: '',
      country: '',
      league: '',
      club: '',
      status: '',
    }
    transferClubs = []
    transferEditing = null
  }

  function openOsk() {
    if (oskOpen) return
    transferEditing = null
    oskText = transferFilters.name
    oskOpen = true
    tick().then(() => {
      const key = document.querySelector('.osk-key')
      if (key) focusElement(key)
    })
  }

  function closeOsk() {
    oskOpen = false
    tick().then(() => focusTransferTile('name'))
  }

  function oskPress(character) {
    if (oskText.length >= OSK_LIMIT) return
    oskText += character
  }

  function oskBackspace() {
    oskText = oskText.slice(0, -1)
  }

  function oskClear() {
    oskText = ''
  }

  function applyOsk() {
    transferFilters.name = oskText.trim()
    closeOsk()
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
    if (tab === 'transfers' && transfersView === 'incomingCounter') {
      closeIncomingCounter()
      return
    }
    if (tab === 'transfers' && incomingOfferModalId) {
      closeIncomingOfferModal()
      return
    }
    if (tab === 'transfers' && transfersView === 'contractAmount') {
      closeTransferContractAmount()
      return
    }
    if (tab === 'transfers' && transfersView === 'contract') {
      closeTransferContract()
      return
    }
    if (tab === 'transfers' && transfersView === 'offerAmount') {
      closeOfferAmount()
      return
    }
    if (tab === 'transfers' && transfersView === 'offer') {
      closeTransferOffer()
      return
    }
    if (tab === 'transfers' && transferOfferModalId) {
      closeSentOfferModal()
      return
    }
    if (tab === 'squad' && view === 'amount') {
      closeAmountScreen()
      return
    }
    if (tab === 'squad' && view === 'negotiation') {
      closeNegotiationScreen()
      return
    }
    if (tab === 'squad' && view === 'number') {
      closeNumberScreen()
      return
    }
    if (tab === 'squad' && view === 'release') {
      closeReleaseScreen()
      return
    }
    if (match.matchdayOpen) {
      if (match.matchdayStep === 'table') {
        match.matchdayStep = 'results'
      } else {
        match.closeMatchday()
      }
      return
    }
    if (match.matchSimOpen) {
      if (match.matchSimLoading || match.matchSimPhase !== 'setup') return
      match.closeMatchSimulation()
      return
    }
    if (match.simulating) {
      match.stopSimulation()
      return
    }
    if (match.advancing) return
    if (match.seasonReview) {
      if (match.reviewStep === 1) {
        match.reviewStep = 0
        tick().then(focusFirst)
      } else {
        match.closeSeasonReview()
      }
      return
    }
    if (tab === 'transfers') {
      if (scoutPickerOpen) {
        closeScoutPicker()
        return
      }
      if (transfersView === 'network') {
        closeTransferNetwork()
        return
      }
      if (transfersView === 'centre' && transferCentreActionsOpen) {
        transferCentreActionsOpen = false
        return
      }
      if (transfersView === 'results' && transferSearchActionsOpen) {
        transferSearchActionsOpen = false
        return
      }
      openTransferHub()
      return
    }
    if (tab === 'squad') {
      if (view === 'centre') {
        if (centreOpenId) {
          closeCentreActions()
          return
        }
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
    if (tab === 'squad' && view === 'number') {
      confirmNumber()
      return true
    }
    if (match.matchdayOpen) {
      match.advanceMatchday()
      return true
    }
    if (!match.matchSimOpen) return false
    match.activateMatchSimulation()
    return true
  }

  function handleDetails() {
    if (match.matchdayOpen) return
    if (match.matchSimOpen) {
      if (match.matchSimPhase === 'live') match.finishMatchSimulation()
      return
    }
    if (tab === 'squad' && view === 'centre') return
    toggleDetails()
  }

  function toggleDetails() {
    if (match.matchdayOpen || match.seasonReview) return
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
    centreOpenId = null
    await tick()
    focusFirst()
  }

  async function setTab(next) {
    if (match.simulating || match.advancing || match.matchSimOpen || match.matchdayOpen) return
    if (!enabledTabs.includes(next)) return
    tab = next
    view = 'overview'
    anchorId = null
    benchFocused = false
    focusPlayerId = null
    centrePlayerId = null
    centreOpenId = null
    centreTab = 'status'
    transfersView = 'hub'
    networkMode = 'scouts'
    networkEntryId = null
    networkBackToHub = false
    networkHints = []
    scoutPickerOpen = false
    scoutPickerPlayer = null
    transferEditing = null
    transferOffer = null
    transferOfferPlayer = null
    oskOpen = false
    transferResults = []
    transferTotal = 0
    transferSearchSelectedId = null
    transferSearchActionsOpen = false
    transferCentreTab = 'shortlist'
    transferCentreSelectedId = null
    transferCentreActionsOpen = false
    transferOfferModalId = null
    incomingOfferModalId = null
    incomingCounterOffer = null
    incomingCounterPlayer = null
    transferError = ''
    await tick()
    focusFirst()
  }

  function switchTab(direction) {
    if (tab === 'transfers' && transfersView !== 'hub') {
      if (
        transfersView === 'centre' &&
        !transferCentreActionsOpen &&
        !scoutPickerOpen &&
        !transferOfferModalId &&
        !incomingOfferModalId
      ) {
        switchTransferCentreTab(direction)
      }
      return
    }
    if (tab === 'squad' && ['negotiation', 'amount', 'number', 'release'].includes(view)) return
    if (transferEditing || oskOpen) return
    if (match.simulating || match.advancing || match.seasonReview || match.matchSimOpen || match.matchdayOpen) return
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
      centrePlayers
        .filter((other) => other.id !== player.id)
        .map((other) => other.shirt_number),
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
    view = 'number'
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
    view = 'centre'
    await tick()
    focusActions(playerId, 'number')
    revealRow(playerId)
  }

  function closeNumberScreen() {
    const playerId = centrePlayer?.id
    view = 'centre'
    tick().then(() => focusActions(playerId, 'number'))
  }

  function openReleaseScreen() {
    if (!centrePlayer) return
    view = 'release'
    tick().then(focusFirst)
  }

  function closeReleaseScreen() {
    const playerId = centrePlayer?.id
    view = 'centre'
    tick().then(() => focusActions(playerId, 'release'))
  }

  async function confirmRelease() {
    if (!centrePlayer || centreActionBusy) return
    centreActionBusy = true
    const updated = await onaction({ type: 'release_player', player_id: centrePlayer.id })
    centreActionBusy = false
    if (!updated) return
    view = 'centre'
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
    view = 'negotiation'
    if (negotiationNotice(centrePlayer)) {
      onaction({ type: 'ack_negotiation', player_id: centrePlayer.id })
    }
    tick().then(focusFirst)
  }

  function closeNegotiationScreen() {
    const playerId = centrePlayer?.id
    view = 'centre'
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
    view = 'amount'
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
    view = 'negotiation'
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
    view = 'negotiation'
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
    view = 'centre'
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
    view = 'centre'
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

  function handleCycle(direction) {
    if (tab === 'transfers') {
      if (transfersView === 'incomingCounter') {
        adjustAmount(direction)
        return
      }
      if (transfersView === 'contractAmount') {
        adjustAmount(direction)
        return
      }
      if (transfersView === 'contract') {
        const field = document.activeElement?.dataset?.field
        if (field) adjustTransferContractField(field, direction === 'right' ? 1 : -1)
        return
      }
      if (transfersView === 'offerAmount') {
        adjustAmount(direction)
        return
      }
      if (transfersView === 'offer') {
        const field = document.activeElement?.dataset?.field
        if (field === 'buyout') {
          if (direction === 'left' || direction === 'right') toggleOfferBuyout()
          return
        }
        if (field) adjustOfferField(field, direction === 'right' ? 1 : -1)
        return
      }
      if (transfersView === 'hub' && reportFeed.length) {
        shiftReport(direction)
        return
      }
      if (transfersView === 'filters' && !oskOpen) {
        handleStep(direction === 'right' ? 'right' : 'left')
      }
      return
    }
    if (tab === 'squad' && view === 'number') {
      cycleNumber(direction)
      return
    }
    if (tab === 'squad' && view === 'amount') {
      adjustAmount(direction)
      return
    }
    const field = document.activeElement?.dataset?.field
    if (tab === 'squad' && view === 'negotiation' && field) {
      adjustNegotiationField(field, direction === 'right' ? 1 : -1)
      return
    }
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

  function reportForPlayer(playerId) {
    if (!playerId) return null
    return (
      (scouting?.scouts ?? []).find(
        (scout) => scout.report?.player_id === playerId,
      )?.report ?? null
    )
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

</script>

<div class="app" class:is-simulating={match.matchSimOpen || match.matchdayOpen}>
  <header class="topbar hub-topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Карьера</div>
        <div class="brand-sub">{career.manager.name}</div>
      </div>
    </div>

    {#if (tab === 'squad' && view === 'centre') || (tab === 'transfers' && transfersView !== 'hub')}
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


    {#if saveError}
      <div class="notice error hub-notice">{saveError}</div>
    {:else if saveNotice}
      <div class="notice hub-notice">{saveNotice}</div>
    {/if}

    {#if tab === 'centre'}
      <CentreTab
        {career}
        {season}
        {nextMatch}
        displayDate={match.displayDate}
        trackDays={match.trackDays}
        trackWidth={match.trackWidth}
        trackShift={match.trackShift}
        isMatchDay={match.isMatchDay}
        simulating={match.simulating}
        advancing={match.advancing}
        {ownRow}
        {tableRows}
        {tableRound}
        inert={match.seasonReview || match.matchSimOpen || match.matchdayOpen}
        onPlay={match.playMatch}
        onOpenSimulation={match.openMatchSimulation}
        onNext={match.handleNextWidget}
      />
    {:else if tab === 'transfers'}
      <TransfersTab
        {career}
        view={transfersView}
        {networkMode}
        {networkEntryId}
        {networkBackToHub}
        bind:networkHints
        bind:historyHints
        onCloseNetwork={closeTransferNetwork}
        onCloseHistory={closeTransferHistory}
        {onaction}
        {scouting}
        {reportPageEntries}
        {reportPage}
        {reportPageCount}
        feedCount={reportFeed.length}
        {transferHubCards}
        onOpenReports={() => openReportsCenter()}
        onShiftReport={shiftReport}
        onOpenHubCard={(card) => {
          if (card.id === 'search') openTransferFilters()
          else if (card.id === 'centre') openTransferCentre()
          else if (card.id === 'network') openTransferNetwork('scouts')
          else if (card.id === 'history') openTransferHistory()
        }}
        {transferFilters}
        {transferEditing}
        {transferRoleRow}
        {transferAgeRow}
        {transferCountries}
        {transferLeagues}
        {transferClubs}
        onOpenOsk={openOsk}
        onToggleFilterEdit={(field) =>
          transferEditing === field ? closeTransferEdit() : openTransferEdit(field)}
        {onStepActive}
        onRoleStep={(row, delta) => {
          transferRoleRow = row
          stepActive(delta)
        }}
        onRangeStep={(field, delta) => {
          transferAgeRow = field
          stepTransferRange(field, delta)
        }}
        {transferCentreTab}
        onSelectCentreTab={setTransferCentreTab}
        {receivedUnread}
        {sentOffers}
        {receivedOffers}
        {transferCentreTitle}
        {transferCentreEmpty}
        {transferCentrePlayers}
        bind:transferCentreView
        bind:transferCentreSelectedId
        bind:transferCentreActionsOpen
        {scoutPickerScouts}
        {reportForPlayer}
        {openScoutPicker}
        {openTransferOffer}
        {openTransferContractFromPlayer}
        {openSentOfferModal}
        {openIncomingOfferModal}
        {acceptTransferCounter}
        {transferOfferModal}
        {incomingOfferModal}
        {acceptSentOfferCounter}
        {reofferSentOffer}
        {openTransferContractFromOffer}
        {submitIncomingOffer}
        {startIncomingCounter}
        {amountField}
        {amountGroups}
        {amountIndex}
        {finishTransferContractAmount}
        {finishOfferAmount}
        {finishIncomingCounterAmount}
        {transferContractPlayer}
        {transferContractState}
        {transferContractTerms}
        {transferContractDraft}
        {transferContractOffer}
        {transferContractFee}
        {transferContractBalanceAfter}
        {centreActionBusy}
        {openTransferContractAmount}
        {adjustTransferContractField}
        {closeTransferContract}
        {signTransferContract}
        {acceptTransferContractCounter}
        {submitTransferContract}
        {incomingCounterOffer}
        {incomingCounterPlayer}
        {transferOffer}
        {transferOfferPlayer}
        {finance}
        {adjustOfferField}
        {toggleOfferBuyout}
        {openOfferAmount}
        {submitTransferOffer}
        {transferResults}
        {transferTotal}
        {transferLoading}
        {transferError}
        {transferHasMore}
        bind:transferResultView
        bind:transferSearchSelectedId
        bind:transferSearchActionsOpen
        {loadMoreTransfers}
        {scoutPickerOpen}
        {scoutPickerPlayer}
        {closeScoutPicker}
        {assignScout}
        {oskOpen}
        {oskText}
        {oskPress}
        {oskBackspace}
        {oskClear}
        {applyOsk}
        {closeOsk}
        places={AMOUNT_PLACES}
      />
    {:else if tab === 'squad' && view === 'overview'}
      <SquadOverview
        {career}
        {lineup}
        {summary}
        {squadTiles}
        {teamDisplay}
        {comparing}
        {teamDelta}
        onPlan={() => openPlan()}
        onCentre={openSquadCentre}
      />
    {:else if tab === 'squad' && view === 'centre'}
      <SquadCentre
        tabs={centreTabs}
        activeTab={centreTab}
        onSelectTab={setCentreTab}
        players={centrePlayers}
        player={centrePlayer}
        {centrePlayerId}
        openId={centreOpenId}
        onFocus={(id) => (centrePlayerId = id)}
        onToggle={toggleCentreActions}
        noticeFor={negotiationNotice}
        onTransferStatus={applyTransferStatus}
        onManageTeam={manageTeamFromCentre}
        onNumber={openNumberScreen}
        onNegotiation={openNegotiationScreen}
        onRelease={openReleaseScreen}
        totals={centreTotals}
        competitions={centreCompetitions}
        radar={centreRadar}
        {attributePages}
        attributePage={centreAttributePage}
        attributeGroup={centreAttributeGroup}
        onShiftAttributePage={shiftAttributePage}
        {finance}
      />
    {:else if tab === 'squad' && (view === 'plan' || view === 'details') && focusedPlayer}
      <PlanView
        {view}
        {planTabs}
        {comparing}
        {anchorPlayer}
        {focusedPlayer}
        {lineup}
        {radar}
        {anchorRadar}
        {detailsPage}
        {detailPages}
        {infoRows}
        {seasonRows}
        {detailGroups}
        {anchorId}
        {teamDisplay}
        {teamDelta}
        {career}
        {benchFocused}
        onCardFocus={(player, event) => {
          focusPlayerId = player.id
          benchFocused = false
          revealName(event)
        }}
        onCardEnter={revealName}
        onCardActivate={activatePlayer}
        onBenchFocus={(player) => {
          benchFocused = true
          focusPlayerId = player.id
        }}
        onBenchActivate={activatePlayer}
        onBenchLeave={() => (benchFocused = false)}
      />
    {:else if tab === 'squad' && view === 'number' && centrePlayer}
      <NumberScreen
        player={centrePlayer}
        candidate={numberCandidate}
        onConfirm={confirmNumber}
      />
    {:else if tab === 'squad' && view === 'release' && centrePlayer}
      <ReleaseScreen
        player={centrePlayer}
        onConfirm={confirmRelease}
        onCancel={closeReleaseScreen}
      />
    {:else if tab === 'squad' && view === 'amount' && centrePlayer && amountField}
      <AmountKeypad
        field={amountField}
        groups={amountGroups}
        index={amountIndex}
        places={AMOUNT_PLACES}
        onFinish={finishAmount}
      />
    {:else if tab === 'squad' && view === 'negotiation' && centrePlayer && negotiationDraft}
      <NegotiationScreen
        player={centrePlayer}
        state={negotiationState}
        terms={negotiationTerms}
        draft={negotiationDraft}
        onOpenAmount={openAmount}
        onAdjustField={adjustNegotiationField}
        onClose={closeNegotiationScreen}
        onSign={signNegotiation}
        onAcceptCounter={acceptCounterOffer}
        onSubmit={submitNegotiation}
      />
    {/if}
  </main>


  {#if match.seasonReview && review}
    <SeasonReview
      {review}
      {season}
      reviewStep={match.reviewStep}
      {ownRow}
      {career}
      onAdvance={match.advanceSeasonReview}
      onStartNewSeason={match.startNewSeason}
    />
  {/if}

  {#if match.matchSimOpen && match.matchSimSetup}
    <MatchSimulationOverlay
      setup={match.matchSimSetup}
      phase={match.matchSimPhase}
      minute={match.matchSimMinute}
      result={match.matchSimResult}
      loading={match.matchSimLoading}
      error={match.matchSimError || saveError}
    />
  {/if}

  {#if match.matchdayOpen && match.matchdayData}
    <MatchdayOverlay data={match.matchdayData} step={match.matchdayStep} clubId={career.club.id} />
  {/if}

  <Controls
    {hints}
    showDefaults={false}
    note={match.matchdayOpen
      ? match.matchdayStep === 'results'
        ? 'Результаты дня'
        : 'Таблица после тура'
      : match.matchSimOpen
        ? match.matchSimPhase === 'live'
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
