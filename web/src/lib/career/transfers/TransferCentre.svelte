<script>
  import TransferPlayers from '../../TransferPlayers.svelte'
  import { TRANSFER_CENTRE_TABS } from '../constants/transfers.js'
  import ReceivedOfferCard from './ReceivedOfferCard.svelte'
  import ReceivedOfferDetail from './ReceivedOfferDetail.svelte'
  import SentOfferCard from './SentOfferCard.svelte'
  import SentOfferDetail from './SentOfferDetail.svelte'
  import TransferListed from './TransferListed.svelte'

  let {
    activeTab,
    onSelectTab,
    receivedUnread = 0,
    sentOffers,
    receivedOffers,
    title,
    empty,
    players,
    date,
    view = $bindable(),
    selectedId = $bindable(),
    actionsOpen = $bindable(),
    scouts,
    reportForPlayer,
    onaction,
    onassign,
    onoffer,
    onnegotiate,
    onOpenSentOffer,
    onCloseSentOffer,
    onOpenIncomingOffer,
    onCloseIncomingOffer,
    onAcceptTransferCounter,
    offerModal,
    incomingModal,
    onReofferOffer,
    onNegotiateOffer,
    onSubmitIncoming,
    onStartIncomingCounter,
  } = $props()

  let selectedOfferId = $state(null)
  let selectedOffer = $derived(
    receivedOffers.find((offer) => offer.offer_id === selectedOfferId) ??
      receivedOffers[0] ??
      null,
  )
  let selectedSentOfferId = $state(null)
  let selectedSentOffer = $derived(
    sentOffers.find((offer) => offer.offer_id === selectedSentOfferId) ??
      sentOffers[0] ??
      null,
  )

  $effect(() => {
    if (!receivedOffers.length) {
      selectedOfferId = null
      return
    }
    if (!receivedOffers.some((offer) => offer.offer_id === selectedOfferId)) {
      selectedOfferId = receivedOffers[0].offer_id
    }
  })

  $effect(() => {
    if (!sentOffers.length) {
      selectedSentOfferId = null
      return
    }
    if (!sentOffers.some((offer) => offer.offer_id === selectedSentOfferId)) {
      selectedSentOfferId = sentOffers[0].offer_id
    }
  })

  function selectOffer(offer) {
    selectedOfferId = offer.offer_id
    if (incomingModal && incomingModal.offer_id !== offer.offer_id) {
      onCloseIncomingOffer()
    }
  }

  function openOffer(offer) {
    selectOffer(offer)
    onOpenIncomingOffer(offer)
  }

  function selectSentOffer(offer) {
    selectedSentOfferId = offer.offer_id
    if (offerModal && offerModal.offer_id !== offer.offer_id) {
      onCloseSentOffer()
    }
  }

  function openSentOffer(offer) {
    selectSentOffer(offer)
    onOpenSentOffer(offer)
  }
</script>

<div class="tf-centre">
  <nav class="centre-tabs tf-centre-tabs" aria-label="Центр трансферов">
    {#each TRANSFER_CENTRE_TABS as item (item.id)}
      <button
        class="centre-tab"
        class:active={activeTab === item.id}
        data-nav
        data-centre-tab={item.id}
        onclick={() => onSelectTab(item.id)}
      >
        {item.label}
        {#if item.id === 'received' && receivedUnread}
          <span class="centre-tab-badge">{receivedUnread}</span>
        {/if}
      </button>
    {/each}
  </nav>
  {#if activeTab === 'sent'}
    {#if sentOffers.length}
      <div class="tf-received">
        <section class="tf-received-main">
          <div class="tf-offer-table-head">
            <span>Статус</span>
            <span>Кому</span>
            <span>Тип</span>
            <span>Имя</span>
            <span>Поз</span>
            <span>Дата</span>
          </div>
          <div class="tf-offer-list scroll-area">
            {#each sentOffers as offer (offer.offer_id)}
              <SentOfferCard
                {offer}
                open={offerModal?.offer_id === offer.offer_id}
                onOpen={() => openSentOffer(offer)}
                onClose={onCloseSentOffer}
                onSelect={selectSentOffer}
                onAcceptCounter={() => onAcceptTransferCounter(offer)}
                onReoffer={() => onReofferOffer(offer)}
                onNegotiate={() => onNegotiateOffer(offer)}
              />
            {/each}
          </div>
        </section>
        <SentOfferDetail offer={selectedSentOffer} />
      </div>
    {:else}
      <div class="tf-empty-state">
        <strong>{title}</strong>
        <p>{empty}</p>
      </div>
    {/if}
  {:else if activeTab === 'received'}
    {#if receivedOffers.length}
      <div class="tf-received">
        <section class="tf-received-main">
          <div class="tf-offer-table-head">
            <span>Статус</span>
            <span>От</span>
            <span>Тип</span>
            <span>Имя</span>
            <span>Поз</span>
            <span>Дата</span>
          </div>
          <div class="tf-offer-list scroll-area">
            {#each receivedOffers as offer (offer.offer_id)}
              <ReceivedOfferCard
                {offer}
                open={incomingModal?.offer_id === offer.offer_id}
                onOpen={() => openOffer(offer)}
                onClose={onCloseIncomingOffer}
                onSelect={selectOffer}
                onAccept={() => onSubmitIncoming(offer, 'incoming_accept')}
                onRefuse={() => onSubmitIncoming(offer, 'incoming_refuse')}
                onCounter={() => onStartIncomingCounter(offer)}
              />
            {/each}
          </div>
        </section>
        <ReceivedOfferDetail offer={selectedOffer} />
      </div>
    {:else}
      <div class="tf-empty-state">
        <strong>{title}</strong>
        <p>{empty}</p>
      </div>
    {/if}
  {:else if activeTab === 'listed'}
    <TransferListed
      {players}
      {date}
      emptyText={empty}
      bind:selectedId
      bind:open={actionsOpen}
      {onaction}
    />
  {:else}
    <TransferPlayers
      {players}
      {title}
      emptyText={empty}
      {date}
      bind:view
      bind:selectedId
      bind:actionsOpen
      {scouts}
      {reportForPlayer}
      {onaction}
      {onassign}
      {onoffer}
      {onnegotiate}
    />
  {/if}
</div>
