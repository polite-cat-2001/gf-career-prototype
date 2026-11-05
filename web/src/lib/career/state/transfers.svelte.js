import { tick } from 'svelte'

import { api } from '../../api.js'
import { CONTRACT_ROLES, positionLabel } from '../../format.js'
import {
  OFFER_KIND_LABELS,
  OFFER_STATUS_LABELS,
  POSITION_BADGES,
  TRANSFER_AGE,
  TRANSFER_CENTRE_TABS,
  TRANSFER_GROUP_OPTIONS,
  TRANSFER_POSITIONS,
  TRANSFER_STATUS_OPTIONS,
} from '../constants/transfers.js'
import { OSK_LIMIT, OSK_ROWS, REPORT_PAGE_SIZE } from '../constants/scouting.js'
import { buildTransferParams, transferFiltersActive as computeTransferFiltersActive } from '../utils/transfers.js'

export function createTransfersState(ctx) {
  const { getCareer, getFinance, getSquad, setTab, onaction, focusFirst, focusElement } = ctx
  const squad = getSquad()

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
  
    let transferFiltersActive = $derived(computeTransferFiltersActive(transferFilters))
    let transferCentre = $derived(
      getCareer().transfers ?? {
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
            ? [
                ...(transferCentre.listed ?? []),
                ...(transferCentre.loaned ?? []),
              ]
            : (transferCentre.shortlist ?? []),
    )
    let transferCentreIsSent = $derived(transferCentreTab === 'sent')
    let transferCentreIsOffer = $derived(transferCentreTab === 'received')
    let transferCentreIsList = $derived(transferCentreTab === 'shortlist')
    let transferCentreIsOwnList = $derived(transferCentreTab === 'listed')
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
      getCareer().transfers?.contracts?.[transferContractPlayerId] ??
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
      Number(getFinance()?.balance ?? 0) - transferContractFee,
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
            ? 'В списке на трансфер пусто. Отметьте игрока в центре составов.'
            : 'Шортлист пуст. Добавьте игрока из поиска или отчёта скаута.',
    )
    let scouting = $derived(getCareer().scouting ?? null)
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
          getCareer().id,
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
      squad.amountField = null
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
      squad.amountField = null
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
      squad.amountField = field
      squad.amountDigits = String(value).padStart(9, '0')
      const firstDigit = squad.amountDigits.search(/[1-9]/)
      squad.amountIndex = firstDigit === -1 ? 8 : firstDigit
    }
  
    function closeTransferContractAmount() {
      squad.amountField = null
      tick().then(focusFirst)
    }
  
    function finishTransferContractAmount() {
      if (!transferContractDraft || !squad.amountField) return
      const value = Math.max(
        0,
        Math.min(999_999_999, Number.parseInt(squad.amountDigits || '0', 10) || 0),
      )
      if (squad.amountField === 'weekly_wage') {
        transferContractDraft.weekly_wage = Math.max(1_000, Math.min(2_000_000, value))
      } else {
        transferContractDraft.release_clause = Math.max(0, value)
      }
      transferContractDraft = { ...transferContractDraft }
      squad.amountField = null
      tick().then(focusFirst)
    }
  
    async function submitTransferContract() {
      if (!transferContractPlayer || !transferContractDraft || squad.centreActionBusy) return
      if (transferContractState?.status === 'accepted') {
        await signTransferContract()
        return
      }
      squad.centreActionBusy = true
      const updated = await onaction({
        type: 'transfer_contract',
        player_id: transferContractPlayer.id,
        offer_id: transferContractOfferId || undefined,
        ...transferContractDraft,
      })
      squad.centreActionBusy = false
      if (!updated) return
      await tick()
      focusFirst()
    }
  
    async function acceptTransferContractCounter() {
      if (!transferContractPlayer || squad.centreActionBusy) return
      squad.centreActionBusy = true
      const updated = await onaction({
        type: 'transfer_accept_counter',
        player_id: transferContractPlayer.id,
      })
      squad.centreActionBusy = false
      if (!updated) return
      await tick()
      focusFirst()
    }
  
    async function signTransferContract() {
      if (!transferContractPlayer || squad.centreActionBusy) return
      if (transferContractState?.affordable === false) return
      squad.centreActionBusy = true
      const updated = await onaction({
        type: 'transfer_sign',
        player_id: transferContractPlayer.id,
      })
      squad.centreActionBusy = false
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
      squad.amountField = field
      squad.amountDigits = String(value).padStart(9, '0')
      const firstDigit = squad.amountDigits.search(/[1-9]/)
      squad.amountIndex = firstDigit === -1 ? 8 : firstDigit
    }
  
    function closeOfferAmount() {
      squad.amountField = null
      tick().then(focusFirst)
    }
  
    function finishOfferAmount() {
      if (!transferOffer || !squad.amountField) return
      const value = Math.max(
        0,
        Math.min(999_999_999, Number.parseInt(squad.amountDigits || '0', 10) || 0),
      )
      if (squad.amountField === 'loan_fee') transferOffer.loan_fee = value
      else transferOffer.amount = value
      transferOffer = { ...transferOffer }
      squad.amountField = null
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
      if (!transferOffer || squad.centreActionBusy) return
      const payload = offerPayload()
      if (!payload) return
      squad.centreActionBusy = true
      const updated = await onaction(payload)
      squad.centreActionBusy = false
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
      if (!offer || squad.centreActionBusy) return false
      squad.centreActionBusy = true
      const updated = await onaction({
        type: 'accept_offer_counter',
        offer_id: offer.offer_id,
      })
      squad.centreActionBusy = false
      return Boolean(updated)
    }

    function sentOfferCard(offerId) {
      return document.querySelector(`[data-offer-card="${offerId}"]`)
    }

    async function openSentOfferModal(offer) {
      if (!offer) return
      if (transferOfferModalId === offer.offer_id) {
        closeSentOfferModal()
        return
      }
      transferOfferModalId = offer.offer_id
      await tick()
      if (transferOfferModalId !== offer.offer_id) return
      const card = sentOfferCard(offer.offer_id)
      const action = card
        ?.closest('.tf-offer-row')
        ?.querySelector('[data-offer-action]:not([disabled])')
      focusElement(action ?? card)
    }

    function closeSentOfferModal() {
      const offerId = transferOfferModalId
      transferOfferModalId = null
      if (!offerId) return
      tick().then(() => focusElement(sentOfferCard(offerId)))
    }

    function focusSentRow(offerId) {
      const card = sentOfferCard(offerId) ?? document.querySelector('[data-offer-card]')
      if (card) focusElement(card)
      else focusFirst()
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
      const updated = await acceptTransferCounter(offer)
      if (!updated) return
      transferOfferModalId = null
      await tick()
      focusSentRow(offer.offer_id)
    }
  
    function incomingOfferCard(offerId) {
      return document.querySelector(`[data-incoming-card="${offerId}"]`)
    }
  
    async function openIncomingOfferModal(offer) {
      if (!offer) return
      if (incomingOfferModalId === offer.offer_id) {
        closeIncomingOfferModal()
        return
      }
      incomingOfferModalId = offer.offer_id
      if (offer.unread) {
        await onaction({ type: 'incoming_ack', offer_id: offer.offer_id })
      }
      await tick()
      if (incomingOfferModalId !== offer.offer_id) return
      const card = incomingOfferCard(offer.offer_id)
      const action = card
        ?.closest('.tf-offer-row')
        ?.querySelector('[data-incoming-action]:not([disabled])')
      focusElement(action ?? card)
    }

    function closeIncomingOfferModal() {
      const offerId = incomingOfferModalId
      incomingOfferModalId = null
      if (!offerId) return
      tick().then(() => focusElement(incomingOfferCard(offerId)))
    }

    function focusReceivedRow() {
      const card = document.querySelector('[data-incoming-card]')
      if (card) focusElement(card)
      else focusReceivedTab()
    }
  
    function focusReceivedTab() {
      const tabElement = document.querySelector(
        '.centre-tab[data-centre-tab="received"]',
      )
      if (tabElement) focusElement(tabElement)
      else focusFirst()
    }
  
    async function submitIncomingOffer(offer, type) {
      if (!offer || squad.centreActionBusy) return
      squad.centreActionBusy = true
      const updated = await onaction({ type, offer_id: offer.offer_id })
      squad.centreActionBusy = false
      if (!updated) return
      incomingOfferModalId = null
      await tick()
      focusReceivedRow()
    }
  
    function startIncomingCounter(offer) {
      if (!offer) return
      incomingCounterOffer = offer
      incomingCounterPlayer = offer
      incomingOfferModalId = null
      squad.amountField = 'incoming_counter'
      squad.amountDigits = String(value).padStart(9, '0')
      const firstDigit = squad.amountDigits.search(/[1-9]/)
      squad.amountIndex = firstDigit === -1 ? 8 : firstDigit
    }
  
    function closeIncomingCounter() {
      squad.amountField = null
      incomingCounterOffer = null
      incomingCounterPlayer = null
      tick().then(focusReceivedTab)
    }
  
    async function finishIncomingCounterAmount() {
      if (!incomingCounterOffer || squad.centreActionBusy) return
      const value = Math.max(
        0,
        Math.min(999_999_999, Number.parseInt(squad.amountDigits || '0', 10) || 0),
      )
      squad.centreActionBusy = true
      const updated = await onaction({
        type: 'incoming_counter',
        offer_id: incomingCounterOffer.offer_id,
        amount: value,
      })
      squad.centreActionBusy = false
      if (!updated) return
      squad.amountField = null
      incomingCounterOffer = null
      incomingCounterPlayer = null
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
  


  return {
    get transfersView() {
      return transfersView
    },
    set transfersView(value) {
      transfersView = value
    },
    get networkMode() {
      return networkMode
    },
    set networkMode(value) {
      networkMode = value
    },
    get networkEntryId() {
      return networkEntryId
    },
    set networkEntryId(value) {
      networkEntryId = value
    },
    get networkBackToHub() {
      return networkBackToHub
    },
    set networkBackToHub(value) {
      networkBackToHub = value
    },
    get networkHints() {
      return networkHints
    },
    set networkHints(value) {
      networkHints = value
    },
    get historyHints() {
      return historyHints
    },
    set historyHints(value) {
      historyHints = value
    },
    get reportPage() {
      return reportPage
    },
    set reportPage(value) {
      reportPage = value
    },
    get scoutPickerOpen() {
      return scoutPickerOpen
    },
    set scoutPickerOpen(value) {
      scoutPickerOpen = value
    },
    get scoutPickerPlayer() {
      return scoutPickerPlayer
    },
    set scoutPickerPlayer(value) {
      scoutPickerPlayer = value
    },
    get scoutConfirm() {
      return scoutConfirm
    },
    set scoutConfirm(value) {
      scoutConfirm = value
    },
    get transferCentreTab() {
      return transferCentreTab
    },
    set transferCentreTab(value) {
      transferCentreTab = value
    },
    get transferResultView() {
      return transferResultView
    },
    set transferResultView(value) {
      transferResultView = value
    },
    get transferCentreView() {
      return transferCentreView
    },
    set transferCentreView(value) {
      transferCentreView = value
    },
    get transferSearchSelectedId() {
      return transferSearchSelectedId
    },
    set transferSearchSelectedId(value) {
      transferSearchSelectedId = value
    },
    get transferCentreSelectedId() {
      return transferCentreSelectedId
    },
    set transferCentreSelectedId(value) {
      transferCentreSelectedId = value
    },
    get transferSearchActionsOpen() {
      return transferSearchActionsOpen
    },
    set transferSearchActionsOpen(value) {
      transferSearchActionsOpen = value
    },
    get transferCentreActionsOpen() {
      return transferCentreActionsOpen
    },
    set transferCentreActionsOpen(value) {
      transferCentreActionsOpen = value
    },
    get transferFilters() {
      return transferFilters
    },
    set transferFilters(value) {
      transferFilters = value
    },
    get transferEditing() {
      return transferEditing
    },
    set transferEditing(value) {
      transferEditing = value
    },
    get transferRoleRow() {
      return transferRoleRow
    },
    set transferRoleRow(value) {
      transferRoleRow = value
    },
    get transferAgeRow() {
      return transferAgeRow
    },
    set transferAgeRow(value) {
      transferAgeRow = value
    },
    get transferResults() {
      return transferResults
    },
    set transferResults(value) {
      transferResults = value
    },
    get transferTotal() {
      return transferTotal
    },
    set transferTotal(value) {
      transferTotal = value
    },
    get transferHasMore() {
      return transferHasMore
    },
    set transferHasMore(value) {
      transferHasMore = value
    },
    get transferLoading() {
      return transferLoading
    },
    set transferLoading(value) {
      transferLoading = value
    },
    get transferError() {
      return transferError
    },
    set transferError(value) {
      transferError = value
    },
    get transferCountries() {
      return transferCountries
    },
    set transferCountries(value) {
      transferCountries = value
    },
    get transferLeagues() {
      return transferLeagues
    },
    set transferLeagues(value) {
      transferLeagues = value
    },
    get transferClubs() {
      return transferClubs
    },
    set transferClubs(value) {
      transferClubs = value
    },
    get transferOffer() {
      return transferOffer
    },
    set transferOffer(value) {
      transferOffer = value
    },
    get transferOfferPlayer() {
      return transferOfferPlayer
    },
    set transferOfferPlayer(value) {
      transferOfferPlayer = value
    },
    get transferOfferBackView() {
      return transferOfferBackView
    },
    set transferOfferBackView(value) {
      transferOfferBackView = value
    },
    get transferOfferModalId() {
      return transferOfferModalId
    },
    set transferOfferModalId(value) {
      transferOfferModalId = value
    },
    get incomingOfferModalId() {
      return incomingOfferModalId
    },
    set incomingOfferModalId(value) {
      incomingOfferModalId = value
    },
    get incomingCounterOffer() {
      return incomingCounterOffer
    },
    set incomingCounterOffer(value) {
      incomingCounterOffer = value
    },
    get incomingCounterPlayer() {
      return incomingCounterPlayer
    },
    set incomingCounterPlayer(value) {
      incomingCounterPlayer = value
    },
    get transferContractPlayerId() {
      return transferContractPlayerId
    },
    set transferContractPlayerId(value) {
      transferContractPlayerId = value
    },
    get transferContractOfferId() {
      return transferContractOfferId
    },
    set transferContractOfferId(value) {
      transferContractOfferId = value
    },
    get transferContractFallback() {
      return transferContractFallback
    },
    set transferContractFallback(value) {
      transferContractFallback = value
    },
    get transferContractBackView() {
      return transferContractBackView
    },
    set transferContractBackView(value) {
      transferContractBackView = value
    },
    get transferContractDraft() {
      return transferContractDraft
    },
    set transferContractDraft(value) {
      transferContractDraft = value
    },
    get oskOpen() {
      return oskOpen
    },
    set oskOpen(value) {
      oskOpen = value
    },
    get oskText() {
      return oskText
    },
    set oskText(value) {
      oskText = value
    },
    get transferSearchToken() {
      return transferSearchToken
    },
    set transferSearchToken(value) {
      transferSearchToken = value
    },
    get transferFiltersActive() {
      return transferFiltersActive
    },
    get transferCentre() {
      return transferCentre
    },
    get transferCentrePlayers() {
      return transferCentrePlayers
    },
    get transferCentreIsSent() {
      return transferCentreIsSent
    },
    get transferCentreIsOffer() {
      return transferCentreIsOffer
    },
    get transferCentreIsList() {
      return transferCentreIsList
    },
    get transferCentreIsOwnList() {
      return transferCentreIsOwnList
    },
    get sentOffers() {
      return sentOffers
    },
    get receivedOffers() {
      return receivedOffers
    },
    get receivedUnread() {
      return receivedUnread
    },
    get incomingOfferModal() {
      return incomingOfferModal
    },
    get transferOfferModal() {
      return transferOfferModal
    },
    get transferContractOffer() {
      return transferContractOffer
    },
    get transferContractPlayer() {
      return transferContractPlayer
    },
    get transferContractState() {
      return transferContractState
    },
    get transferContractTerms() {
      return transferContractTerms
    },
    get transferContractFee() {
      return transferContractFee
    },
    get transferContractBalanceAfter() {
      return transferContractBalanceAfter
    },
    get transferCentreTitle() {
      return transferCentreTitle
    },
    get transferCentreEmpty() {
      return transferCentreEmpty
    },
    get scouting() {
      return scouting
    },
    get reportFeed() {
      return reportFeed
    },
    get reportPageCount() {
      return reportPageCount
    },
    get reportPageEntries() {
      return reportPageEntries
    },
    get scoutPickerScouts() {
      return scoutPickerScouts
    },
    activeEditField,
    inlineOptions,
    runTransferSearch,
    loadMoreTransfers,
    ensureTransferOptions,
    openTransferFilters,
    startTransferSearch,
    openTransferCentre,
    setTransferCentreTab,
    switchTransferCentreTab,
    offerStatusLabel,
    offerKindLabel,
    contractStatusLabel,
    openTransferOffer,
    closeTransferOffer,
    contractDraftFrom,
    openTransferContractFromOffer,
    openTransferContractFromPlayer,
    closeTransferContract,
    contractWageStep,
    contractClauseStep,
    adjustTransferContractField,
    openTransferContractAmount,
    closeTransferContractAmount,
    finishTransferContractAmount,
    submitTransferContract,
    acceptTransferContractCounter,
    signTransferContract,
    transferOfferBase,
    transferOfferStep,
    loanOfferStep,
    adjustOfferField,
    toggleOfferBuyout,
    openOfferAmount,
    closeOfferAmount,
    finishOfferAmount,
    offerPayload,
    submitTransferOffer,
    acceptTransferCounter,
    sentOfferCard,
    openSentOfferModal,
    closeSentOfferModal,
    reofferSentOffer,
    acceptSentOfferCounter,
    incomingOfferCard,
    openIncomingOfferModal,
    closeIncomingOfferModal,
    focusReceivedTab,
    submitIncomingOffer,
    startIncomingCounter,
    closeIncomingCounter,
    finishIncomingCounterAmount,
    focusTransferTile,
    openTransferHistory,
    closeTransferHistory,
    openTransferNetwork,
    closeTransferNetwork,
    openReportsCenter,
    shiftReport,
    openScoutPicker,
    closeScoutPicker,
    assignScout,
    openTransferHub,
    applyTransferField,
    stepTransferField,
    stepTransferRange,
    stepActive,
    openTransferEdit,
    closeTransferEdit,
    resetTransferFilters,
    openOsk,
    closeOsk,
    oskPress,
    oskBackspace,
    oskClear,
    applyOsk,
  }
}
