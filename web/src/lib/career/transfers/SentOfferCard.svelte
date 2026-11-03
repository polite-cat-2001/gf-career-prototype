<script>
  import { formatDate, formatValue, hideBrokenImage } from '../../format.js'
  import {
    contractStatusLabel,
    offerKindLabel,
    offerStatusLabel,
  } from '../utils/transfers.js'

  let { offer, onOpen, onAcceptCounter } = $props()
</script>

<article class="tf-offer-card is-{offer.status}">
  <div class="tf-offer-card-row">
    <button
      class="tf-offer-card-main is-clickable"
      data-nav
      data-offer-card={offer.offer_id}
      onclick={onOpen}
    >
      <span class="tf-offer-card-photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="tf-offer-card-info">
        <span class="tf-offer-card-name">{offer.name}</span>
        <span class="tf-offer-card-meta">
          {offerKindLabel(offer.kind)} · {formatValue(offer.amount)}
          {#if offer.kind === 'loan'}
            · зарплата {offer.wage_share}%
          {/if}
        </span>
        <span class="tf-offer-card-status">
          {offerStatusLabel(offer.status)}
          {#if offer.due && offer.status === 'pending'}
            · ответ до {formatDate(offer.due)}
          {/if}
          {#if offer.status === 'refused' && offer.retry_after}
            · повтор после {formatDate(offer.retry_after)}
          {/if}
          {#if contractStatusLabel(offer.contract_status)}
            · контракт: {contractStatusLabel(offer.contract_status)}
          {/if}
        </span>
        <span class="tf-offer-card-message">{offer.message}</span>
        {#if offer.counter}
          <span class="tf-offer-card-counter">
            Новые условия: {formatValue(offer.counter.amount)}
            {#if offer.kind === 'loan'}
              · зарплата {offer.counter.wage_share}%
            {/if}
          </span>
        {/if}
      </div>
      {#if offer.club_logo}
        <img
          class="tf-offer-card-crest"
          src={offer.club_logo}
          alt=""
          onerror={hideBrokenImage}
        />
      {/if}
    </button>
    {#if offer.can_accept_counter}
      <div class="tf-offer-card-actions">
        <button
          class="tf-offer-action is-primary"
          data-nav
          onclick={onAcceptCounter}
        >
          Принять контрпредложение
        </button>
      </div>
    {/if}
  </div>
</article>
