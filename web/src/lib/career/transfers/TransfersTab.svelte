<script>
  import Scouting from '../../Scouting.svelte'
  import TransferHistory from '../../TransferHistory.svelte'
  import OnScreenKeyboard from './OnScreenKeyboard.svelte'
  import TransferCentre from './TransferCentre.svelte'
  import TransferContractScreen from './TransferContractScreen.svelte'
  import TransferFilters from './TransferFilters.svelte'
  import TransferHub from './TransferHub.svelte'
  import TransferOfferScreen from './TransferOfferScreen.svelte'
  import TransferResults from './TransferResults.svelte'

  let {
    career,
    view,
    networkMode,
    networkEntryId,
    networkBackToHub,
    networkHints = $bindable(),
    historyHints = $bindable(),
    onCloseNetwork,
    onCloseHistory,
    onaction,
    scouting,
    reportPageEntries,
    reportPage,
    reportPageCount,
    feedCount,
    transferHubCards,
    onOpenReports,
    onShiftReport,
    onOpenHubCard,
    transferFilters,
    transferEditing,
    transferRoleRow,
    transferAgeRow,
    transferCountries,
    transferLeagues,
    transferClubs,
    onOpenOsk,
    onToggleFilterEdit,
    onStepActive,
    onRoleStep,
    onRangeStep,
    transferCentreTab,
    onSelectCentreTab,
    receivedUnread,
    sentOffers,
    receivedOffers,
    transferCentreTitle,
    transferCentreEmpty,
    transferCentrePlayers,
    transferCentreView = $bindable(),
    transferCentreSelectedId = $bindable(),
    transferCentreActionsOpen = $bindable(),
    scoutPickerScouts,
    reportForPlayer,
    openScoutPicker,
    openTransferOffer,
    openTransferContractFromPlayer,
    openSentOfferModal,
    openIncomingOfferModal,
    collapseSentOffer,
    collapseIncomingOffer,
    transferOfferModal,
    incomingOfferModal,
    acceptSentOfferCounter,
    reofferSentOffer,
    openTransferContractFromOffer,
    submitIncomingOffer,
    startIncomingCounter,
    transferContractPlayer,
    transferContractState,
    transferContractTerms,
    transferContractDraft,
    transferContractOffer,
    transferContractFee,
    transferContractBalanceAfter,
    centreActionBusy,
    openTransferContractAmount,
    adjustTransferContractField,
    closeTransferContract,
    signTransferContract,
    acceptTransferContractCounter,
    submitTransferContract,
    transferOffer,
    transferOfferPlayer,
    finance,
    adjustOfferField,
    toggleOfferBuyout,
    openOfferAmount,
    submitTransferOffer,
    transferResults,
    transferTotal,
    transferLoading,
    transferError,
    transferHasMore,
    transferResultView = $bindable(),
    transferSearchSelectedId = $bindable(),
    transferSearchActionsOpen = $bindable(),
    loadMoreTransfers,
    scoutPickerOpen,
    scoutPickerPlayer,
    closeScoutPicker,
    assignScout,
    oskOpen,
    oskText,
    oskPress,
    oskBackspace,
    oskClear,
    applyOsk,
    closeOsk,
  } = $props()
</script>

{#if view === 'hub'}
  <TransferHub
    {scouting}
    {reportPageEntries}
    {reportPage}
    {reportPageCount}
    {feedCount}
    cards={transferHubCards}
    {onOpenReports}
    {onShiftReport}
    onOpenCard={onOpenHubCard}
  />
{:else if view === 'filters'}
  <TransferFilters
    filters={transferFilters}
    editing={transferEditing}
    roleRow={transferRoleRow}
    ageRow={transferAgeRow}
    countries={transferCountries}
    leagues={transferLeagues}
    clubs={transferClubs}
    {oskOpen}
    {onOpenOsk}
    onToggle={onToggleFilterEdit}
    {onStepActive}
    {onRoleStep}
    {onRangeStep}
  />
{:else if view === 'network'}
  <Scouting
    {career}
    mode={networkMode}
    initialEntryId={networkEntryId}
    backToHub={networkBackToHub}
    bind:hints={networkHints}
    onclose={onCloseNetwork}
    {onaction}
    onoffer={openTransferOffer}
    onnegotiate={openTransferContractFromPlayer}
  />
{:else if view === 'history'}
  <TransferHistory {career} bind:hints={historyHints} onclose={onCloseHistory} />
{:else if view === 'centre'}
  <TransferCentre
    activeTab={transferCentreTab}
    onSelectTab={onSelectCentreTab}
    {receivedUnread}
    {sentOffers}
    {receivedOffers}
    title={transferCentreTitle}
    empty={transferCentreEmpty}
    players={transferCentrePlayers}
    date={career.date}
    bind:view={transferCentreView}
    bind:selectedId={transferCentreSelectedId}
    bind:actionsOpen={transferCentreActionsOpen}
    scouts={scoutPickerScouts}
    {reportForPlayer}
    {onaction}
    onassign={openScoutPicker}
    onoffer={openTransferOffer}
    onnegotiate={openTransferContractFromPlayer}
    onOpenSentOffer={openSentOfferModal}
    onCloseSentOffer={collapseSentOffer}
    onOpenIncomingOffer={openIncomingOfferModal}
    onCloseIncomingOffer={collapseIncomingOffer}
    onAcceptTransferCounter={acceptSentOfferCounter}
    offerModal={transferOfferModal}
    incomingModal={incomingOfferModal}
    onReofferOffer={reofferSentOffer}
    onNegotiateOffer={openTransferContractFromOffer}
    onSubmitIncoming={submitIncomingOffer}
    onStartIncomingCounter={startIncomingCounter}
  />
{:else if view === 'contract' && transferContractPlayer}
  <TransferContractScreen
    player={transferContractPlayer}
    state={transferContractState}
    terms={transferContractTerms}
    draft={transferContractDraft}
    offer={transferContractOffer}
    fee={transferContractFee}
    balanceAfter={transferContractBalanceAfter}
    busy={centreActionBusy}
    kind={transferContractState?.kind ?? transferContractOffer?.kind}
    wageShare={transferContractState?.wage_share ?? transferContractOffer?.wage_share ?? 100}
    onOpenAmount={openTransferContractAmount}
    onAdjustField={adjustTransferContractField}
    onClose={closeTransferContract}
    onSign={signTransferContract}
    onAcceptCounter={acceptTransferContractCounter}
    onSubmit={submitTransferContract}
  />
{:else if view === 'offer' && transferOffer && transferOfferPlayer}
  <TransferOfferScreen
    offer={transferOffer}
    player={transferOfferPlayer}
    {finance}
    busy={centreActionBusy}
    onOpenAmount={openOfferAmount}
    onAdjustField={adjustOfferField}
    onToggleBuyout={toggleOfferBuyout}
    onSubmit={submitTransferOffer}
  />
{:else}
  <TransferResults
    players={transferResults}
    total={transferTotal}
    loading={transferLoading}
    error={transferError}
    hasMore={transferHasMore}
    date={career.date}
    bind:view={transferResultView}
    bind:selectedId={transferSearchSelectedId}
    bind:actionsOpen={transferSearchActionsOpen}
    scouts={scoutPickerScouts}
    {reportForPlayer}
    onloadmore={loadMoreTransfers}
    {onaction}
    onassign={openScoutPicker}
    onoffer={openTransferOffer}
    onnegotiate={openTransferContractFromPlayer}
    {scoutPickerOpen}
    {scoutPickerPlayer}
    {closeScoutPicker}
    onAssignScout={assignScout}
  />
{/if}

{#if oskOpen}
  <OnScreenKeyboard
    text={oskText}
    onPress={oskPress}
    onBackspace={oskBackspace}
    onClear={oskClear}
    onApply={applyOsk}
    onClose={closeOsk}
  />
{/if}
