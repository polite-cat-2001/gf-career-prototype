<script>
  import { onMount, tick } from 'svelte'
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
  import AppShell from './ui/AppShell.svelte'
  import Breadcrumb from './ui/Breadcrumb.svelte'
  import TabBar from './ui/TabBar.svelte'
  import { focusElement, focusFirst } from './input.js'
  import {
    AMOUNT_PLACES,
    attributePages,
    centreTabs,
    detailPages,
    planTabs,
    squadTiles,
    tabs,
  } from './career/constants/hub.js'
  import { transferHubCards } from './career/constants/transfers.js'
  import {
    ownRow as findOwnRow,
    tableRound as computeTableRound,
    tableRows as computeTableRows,
  } from './career/utils/table.js'
  import { createMatchState } from './career/state/match.svelte.js'
  import { createSquadState } from './career/state/squad.svelte.js'
  import { createTransfersState } from './career/state/transfers.svelte.js'
  import { createNavigationState } from './career/state/navigation.svelte.js'
  import CentreTab from './career/centre/CentreTab.svelte'
  import SquadOverview from './career/squad/SquadOverview.svelte'
  import SquadCentre from './career/squad/SquadCentre.svelte'
  import PlanView from './career/squad/PlanView.svelte'
  import NumberScreen from './career/squad/NumberScreen.svelte'
  import ReleaseScreen from './career/squad/ReleaseScreen.svelte'
  import NegotiationScreen from './career/squad/NegotiationScreen.svelte'
  import AmountModal from './career/shared/AmountModal.svelte'
  import { formatValue } from './format.js'
  import TransfersTab from './career/transfers/TransfersTab.svelte'
  import SeasonReview from './career/match/SeasonReview.svelte'
  import MatchSimulationOverlay from './career/match/MatchSimulationOverlay.svelte'
  import MatchdayOverlay from './career/match/MatchdayOverlay.svelte'


  let {
    career,
    saving = false,
    playing = false,
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

  const squad = createSquadState({
    getCareer: () => career,
    getLineup: () => lineup,
    getSummary: () => summary,
    getDetailsPage: () => nav.detailsPage,
    setTab: (value) => {
      nav.tab = value
    },
    setView: (value) => {
      nav.view = value
    },
    onaction,
    onswap,
    focusFirst,
    focusElement,
  })

  const transfers = createTransfersState({
    getCareer: () => career,
    getFinance: () => squad.finance,
    getSquad: () => squad,
    setTab: (value) => nav.setTab(value),
    onaction,
    focusFirst,
    focusElement,
  })

  const nav = createNavigationState({
    getCareer: () => career,
    getNextMatch: () => nextMatch,
    getSeason: () => season,
    getOwnRow: () => ownRow,
    getPlaying: () => playing,
    getSaving: () => saving,
    getCentreAction: () => centreAction,
    match,
    squad,
    transfers,
    onexit,
    onsave,
    focusFirst,
  })

  onMount(() => {
    const stopBack = registerBack(nav.handleBack)
    const stopTabs = registerTabs(nav.switchTab)
    const stopSave = registerSave(nav.handleSave)
    const stopDetails = registerDetails(nav.handleDetails)
    const stopPrimary = registerPrimary(nav.handlePrimaryAction)
    const stopCycle = registerCycle(nav.handleCycle)
    const stopView = registerView(nav.handleViewToggle)
    const stopStep = registerStep(nav.handleStep)
    const stopReset = registerReset(nav.handleReset)
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
    }
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
  function reportForPlayer(playerId) {
    if (!playerId) return null
    return (
      (transfers.scouting?.scouts ?? []).find(
        (scout) => scout.report?.player_id === playerId,
      )?.report ?? null
    )
  }

  const transferViewLabels = {
    filters: 'Фильтры',
    results: 'Результаты',
    centre: 'Центр трансферов',
    network: 'Сеть поиска',
    history: 'История',
    offer: 'Предложение',
    contract: 'Контракт',
  }

  let subview = $derived(
    (nav.tab === 'squad' &&
      ['centre', 'plan', 'details', 'negotiation'].includes(nav.view)) ||
      (nav.tab === 'transfers' && transfers.transfersView !== 'hub'),
  )
  let crumbs = $derived(
    nav.tab === 'squad'
      ? nav.view === 'negotiation'
        ? ['Карьера', 'Состав', 'Продление контракта']
        : nav.view === 'plan' || nav.view === 'details'
          ? ['Карьера', 'Состав', 'План игры']
          : ['Карьера', 'Состав', 'Центр составов']
      : ['Карьера', 'Трансферы', transferViewLabels[transfers.transfersView] ?? 'Трансферы'],
  )
  let amountModal = $derived.by(() => {
    const field = squad.amountField
    if (!field) return null
    if (nav.tab === 'squad') {
      return {
        label: field === 'weekly_wage' ? 'Зарплата в неделю' : 'Отступные',
        hint: null,
        confirmLabel: 'Готово',
      }
    }
    if (nav.tab !== 'transfers') return null
    if (transfers.incomingCounterOffer) {
      return {
        label: `Контрпредложение · ${transfers.incomingCounterPlayer?.name ?? ''}`,
        hint: `Предложение клуба: ${formatValue(transfers.incomingCounterOffer.amount)}`,
        confirmLabel: 'Отправить',
      }
    }
    if (transfers.transfersView === 'contract') {
      return {
        label: field === 'weekly_wage' ? 'Зарплата в неделю' : 'Отступные',
        hint: null,
        confirmLabel: 'Готово',
      }
    }
    if (transfers.transfersView === 'offer') {
      return {
        label: field === 'loan_fee' ? 'Плата за аренду' : 'Сумма предложения',
        hint: null,
        confirmLabel: 'Готово',
      }
    }
    return null
  })

  function finishActiveAmount() {
    if (nav.tab === 'squad') {
      squad.finishAmount()
      return
    }
    if (transfers.incomingCounterOffer) {
      transfers.finishIncomingCounterAmount()
      return
    }
    if (transfers.transfersView === 'contract') {
      transfers.finishTransferContractAmount()
      return
    }
    transfers.finishOfferAmount()
  }

  let legendNote = $derived(
    match.matchdayOpen
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
            : squad.swapping
              ? 'Обмен…'
              : '',
  )
</script>

<div
  class="app gf-career"
  class:is-simulating={match.matchSimOpen || match.matchdayOpen}
  class:is-plan={nav.tab === 'squad' && (nav.view === 'plan' || nav.view === 'details')}
>
  <AppShell fill hints={nav.hints} note={legendNote}>
    {#snippet header()}
      <div class="hub-head">
        {#if subview}
          <Breadcrumb items={crumbs} />
        {:else}
          <TabBar {tabs} active={nav.tab} onselect={nav.setTab} />
        {/if}
      </div>
    {/snippet}

    <div class="hub-body">
      {#if saveError}
        <p class="gf-notice is-error">{saveError}</p>
      {/if}

      {#key nav.tab}
        <div class="hub-main">

    {#if nav.tab === 'centre'}
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
    {:else if nav.tab === 'transfers'}
      <TransfersTab
        {career}
        view={transfers.transfersView}
        networkMode={transfers.networkMode}
        networkEntryId={transfers.networkEntryId}
        networkBackToHub={transfers.networkBackToHub}
        bind:networkHints={transfers.networkHints}
        bind:historyHints={transfers.historyHints}
        onCloseNetwork={transfers.closeTransferNetwork}
        onCloseHistory={transfers.closeTransferHistory}
        {onaction}
        scouting={transfers.scouting}
        reportPageEntries={transfers.reportPageEntries}
        reportPage={transfers.reportPage}
        reportPageCount={transfers.reportPageCount}
        feedCount={transfers.reportFeed.length}
        {transferHubCards}
        onOpenReports={() => transfers.openReportsCenter()}
        onShiftReport={transfers.shiftReport}
        onOpenHubCard={(card) => {
          if (card.id === 'search') transfers.openTransferFilters()
          else if (card.id === 'centre') transfers.openTransferCentre()
          else if (card.id === 'network') transfers.openTransferNetwork('scouts')
          else if (card.id === 'history') transfers.openTransferHistory()
        }}
        transferFilters={transfers.transferFilters}
        transferEditing={transfers.transferEditing}
        transferRoleRow={transfers.transferRoleRow}
        transferAgeRow={transfers.transferAgeRow}
        transferCountries={transfers.transferCountries}
        transferLeagues={transfers.transferLeagues}
        transferClubs={transfers.transferClubs}
        onOpenOsk={transfers.openOsk}
        onToggleFilterEdit={(field) =>
          transfers.transferEditing === field ? transfers.closeTransferEdit() : transfers.openTransferEdit(field)}
        onStepActive={transfers.stepActive}
        onRoleStep={(row, delta) => {
          transfers.transferRoleRow = row
          transfers.stepActive(delta)
        }}
        onRangeStep={(field, delta) => {
          transfers.transferAgeRow = field
          transfers.stepTransferRange(field, delta)
        }}
        transferCentreTab={transfers.transferCentreTab}
        onSelectCentreTab={transfers.setTransferCentreTab}
        receivedUnread={transfers.receivedUnread}
        sentOffers={transfers.sentOffers}
        receivedOffers={transfers.receivedOffers}
        transferCentreTitle={transfers.transferCentreTitle}
        transferCentreEmpty={transfers.transferCentreEmpty}
        transferCentrePlayers={transfers.transferCentrePlayers}
        bind:transferCentreView={transfers.transferCentreView}
        bind:transferCentreSelectedId={transfers.transferCentreSelectedId}
        bind:transferCentreActionsOpen={transfers.transferCentreActionsOpen}
        scoutPickerScouts={transfers.scoutPickerScouts}
        {reportForPlayer}
        openScoutPicker={transfers.openScoutPicker}
        openTransferOffer={transfers.openTransferOffer}
        openTransferContractFromPlayer={transfers.openTransferContractFromPlayer}
        openSentOfferModal={transfers.openSentOfferModal}
        onCloseSentOffer={transfers.closeSentOfferModal}
        openIncomingOfferModal={transfers.openIncomingOfferModal}
        onCloseIncomingOffer={transfers.closeIncomingOfferModal}
        transferOfferModal={transfers.transferOfferModal}
        incomingOfferModal={transfers.incomingOfferModal}
        acceptSentOfferCounter={transfers.acceptSentOfferCounter}
        reofferSentOffer={transfers.reofferSentOffer}
        openTransferContractFromOffer={transfers.openTransferContractFromOffer}
        submitIncomingOffer={transfers.submitIncomingOffer}
        startIncomingCounter={transfers.startIncomingCounter}
        transferContractPlayer={transfers.transferContractPlayer}
        transferContractState={transfers.transferContractState}
        transferContractTerms={transfers.transferContractTerms}
        transferContractDraft={transfers.transferContractDraft}
        transferContractOffer={transfers.transferContractOffer}
        transferContractFee={transfers.transferContractFee}
        transferContractBalanceAfter={transfers.transferContractBalanceAfter}
        centreActionBusy={squad.centreActionBusy}
        openTransferContractAmount={transfers.openTransferContractAmount}
        adjustTransferContractField={transfers.adjustTransferContractField}
        closeTransferContract={transfers.closeTransferContract}
        signTransferContract={transfers.signTransferContract}
        acceptTransferContractCounter={transfers.acceptTransferContractCounter}
        submitTransferContract={transfers.submitTransferContract}
        transferOffer={transfers.transferOffer}
        transferOfferPlayer={transfers.transferOfferPlayer}
        finance={squad.finance}
        adjustOfferField={transfers.adjustOfferField}
        toggleOfferBuyout={transfers.toggleOfferBuyout}
        openOfferAmount={transfers.openOfferAmount}
        submitTransferOffer={transfers.submitTransferOffer}
        transferResults={transfers.transferResults}
        transferTotal={transfers.transferTotal}
        transferLoading={transfers.transferLoading}
        transferError={transfers.transferError}
        transferHasMore={transfers.transferHasMore}
        bind:transferResultView={transfers.transferResultView}
        bind:transferSearchSelectedId={transfers.transferSearchSelectedId}
        bind:transferSearchActionsOpen={transfers.transferSearchActionsOpen}
        loadMoreTransfers={transfers.loadMoreTransfers}
        scoutPickerOpen={transfers.scoutPickerOpen}
        scoutPickerPlayer={transfers.scoutPickerPlayer}
        closeScoutPicker={transfers.closeScoutPicker}
        assignScout={transfers.assignScout}
        oskOpen={transfers.oskOpen}
        oskText={transfers.oskText}
        oskPress={transfers.oskPress}
        oskBackspace={transfers.oskBackspace}
        oskClear={transfers.oskClear}
        applyOsk={transfers.applyOsk}
        closeOsk={transfers.closeOsk}
      />
    {:else if nav.tab === 'squad' && nav.view === 'overview'}
      <SquadOverview
        {career}
        {lineup}
        {summary}
        {squadTiles}
        teamDisplay={squad.teamDisplay}
        comparing={squad.comparing}
        teamDelta={squad.teamDelta}
        onPlan={() => squad.openPlan()}
        onCentre={squad.openSquadCentre}
      />
    {:else if nav.tab === 'squad' && nav.view === 'centre'}
      <SquadCentre
        tabs={centreTabs}
        activeTab={squad.centreTab}
        onSelectTab={squad.setCentreTab}
        players={squad.centrePlayers}
        player={squad.centrePlayer}
        centrePlayerId={squad.centrePlayerId}
        openId={squad.centreOpenId}
        onFocus={(id) => (squad.centrePlayerId = id)}
        onToggle={squad.toggleCentreActions}
        noticeFor={squad.negotiationNotice}
        onTransferStatus={squad.applyTransferStatus}
        onManageTeam={squad.manageTeamFromCentre}
        onNumber={squad.openNumberScreen}
        onNegotiation={squad.openNegotiationScreen}
        onRelease={squad.openReleaseScreen}
        totals={squad.centreTotals}
        competitions={squad.centreCompetitions}
        radar={squad.centreRadar}
        {attributePages}
        attributePage={squad.centreAttributePage}
        attributeGroup={squad.centreAttributeGroup}
        onShiftAttributePage={squad.shiftAttributePage}
        finance={squad.finance}
      />
    {:else if nav.tab === 'squad' && (nav.view === 'plan' || nav.view === 'details') && (squad.focusedPlayer || (nav.view === 'plan' && squad.planTab === 'schemes'))}
      <PlanView
        view={nav.view}
        planTab={squad.planTab}
        {planTabs}
        currentFormation={squad.currentFormation}
        schemeLineup={squad.schemeLineup}
        visibleFormations={squad.visibleFormations}
        formationPage={squad.formationPage}
        formationPageCount={squad.formationPageCount}
        onSelectPlanTab={squad.openPlanTab}
        onPreviewFormation={squad.previewFormationCard}
        onSelectFormation={squad.selectFormation}
        onFormationScroll={(delta) => squad.setFormationPage(squad.formationPage + (delta > 0 ? 1 : -1))}
        comparing={squad.comparing}
        anchorPlayer={squad.anchorPlayer}
        focusedPlayer={squad.focusedPlayer}
        {lineup}
        radar={squad.radar}
        anchorRadar={squad.anchorRadar}
        detailsPage={nav.detailsPage}
        {detailPages}
        infoRows={squad.infoRows}
        seasonRows={squad.seasonRows}
        detailGroups={squad.detailGroups}
        anchorId={squad.anchorId}
        teamDisplay={squad.teamDisplay}
        teamDelta={squad.teamDelta}
        {career}
        benchFocused={squad.benchFocused}
        onCardFocus={(player, event) => {
          squad.focusPlayerId = player.id
          squad.benchFocused = false
          squad.revealName(event)
        }}
        onCardEnter={squad.revealName}
        onCardActivate={squad.activatePlayer}
        onBenchFocus={(player) => {
          squad.benchFocused = true
          squad.focusPlayerId = player.id
        }}
        onBenchActivate={squad.activatePlayer}
        onBenchLeave={() => (squad.benchFocused = false)}
      />
    {:else if nav.tab === 'squad' && nav.view === 'number' && squad.centrePlayer}
      <NumberScreen
        player={squad.centrePlayer}
        candidate={squad.numberCandidate}
        onConfirm={squad.confirmNumber}
      />
    {:else if nav.tab === 'squad' && nav.view === 'release' && squad.centrePlayer}
      <ReleaseScreen
        player={squad.centrePlayer}
        onConfirm={squad.confirmRelease}
        onCancel={squad.closeReleaseScreen}
      />
    {:else if nav.tab === 'squad' && nav.view === 'negotiation' && squad.centrePlayer && squad.negotiationDraft}
      <NegotiationScreen
        player={squad.centrePlayer}
        state={squad.negotiationState}
        terms={squad.negotiationTerms}
        draft={squad.negotiationDraft}
        onOpenAmount={squad.openAmount}
        onAdjustField={squad.adjustNegotiationField}
        onClose={squad.closeNegotiationScreen}
        onSign={squad.signNegotiation}
        onAcceptCounter={squad.acceptCounterOffer}
        onSubmit={squad.submitNegotiation}
      />
    {/if}
        </div>
      {/key}
    </div>
  </AppShell>

  {#if amountModal}
    <AmountModal
      label={amountModal.label}
      hint={amountModal.hint}
      confirmLabel={amountModal.confirmLabel}
      groups={squad.amountGroups}
      index={squad.amountIndex}
      places={AMOUNT_PLACES}
      finish={finishActiveAmount}
    />
  {/if}

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
</div>
