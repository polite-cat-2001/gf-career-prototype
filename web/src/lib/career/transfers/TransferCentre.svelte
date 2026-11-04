<script>
  import TransferPlayers from '../../TransferPlayers.svelte'
  import TransferOfferModal from '../../TransferOfferModal.svelte'
  import IncomingOfferModal from '../../IncomingOfferModal.svelte'
  import { TRANSFER_CENTRE_TABS } from '../constants/transfers.js'
  import ReceivedOfferCard from './ReceivedOfferCard.svelte'
  import SentOfferCard from './SentOfferCard.svelte'

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
    onOpenIncomingOffer,
    onAcceptTransferCounter,
    offerModal,
    incomingModal,
    onAcceptOfferCounter,
    onReofferOffer,
    onNegotiateOffer,
    onSubmitIncoming,
    onStartIncomingCounter,
    inert = false,
  } = $props()
</script>

<div class="tf-centre" {inert}>
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
      <div class="tf-offers scroll-area">
        {#each sentOffers as offer (offer.offer_id)}
          <SentOfferCard
            {offer}
            onOpen={() => onOpenSentOffer(offer)}
            onAcceptCounter={() => onAcceptTransferCounter(offer)}
          />
        {/each}
      </div>
    {:else}
      <div class="tf-empty-state">
        <strong>{title}</strong>
        <p>{empty}</p>
      </div>
    {/if}
  {:else if activeTab === 'received'}
    {#if receivedOffers.length}
      <div class="tf-offers scroll-area">
        {#each receivedOffers as offer (offer.offer_id)}
          <ReceivedOfferCard {offer} onOpen={() => onOpenIncomingOffer(offer)} />
        {/each}
      </div>
    {:else}
      <div class="tf-empty-state">
        <strong>{title}</strong>
        <p>{empty}</p>
      </div>
    {/if}
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
{#if offerModal}
  <TransferOfferModal
    offer={offerModal}
    onaccept={() => onAcceptOfferCounter(offerModal)}
    onreoffer={() => onReofferOffer(offerModal)}
    onnegotiate={() => onNegotiateOffer(offerModal)}
  />
{/if}
{#if incomingModal}
  <IncomingOfferModal
    offer={incomingModal}
    onaccept={() => onSubmitIncoming(incomingModal, 'incoming_accept')}
    onrefuse={() => onSubmitIncoming(incomingModal, 'incoming_refuse')}
    oncounter={() => onStartIncomingCounter(incomingModal)}
  />
{/if}
