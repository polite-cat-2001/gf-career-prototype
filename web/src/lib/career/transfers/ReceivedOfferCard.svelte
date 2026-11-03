<script>
  import { formatDate, formatValue, hideBrokenImage } from '../../format.js'
  import { offerKindLabel, offerStatusLabel } from '../utils/transfers.js'

  let { offer, onOpen } = $props()
</script>

<article class="tf-offer-card is-{offer.status}" class:is-unread={offer.unread}>
  <button
    class="tf-offer-card-main is-clickable"
    data-nav
    data-incoming-card={offer.offer_id}
    onclick={onOpen}
  >
    <span class="tf-offer-card-photo">
      <img src={offer.photo} alt="" onerror={hideBrokenImage} />
    </span>
    <div class="tf-offer-card-info">
      <span class="tf-offer-card-name">{offer.name}</span>
      <span class="tf-offer-card-meta">
        {offer.club_name} · {offerKindLabel(offer.kind)} ·
        {formatValue(offer.amount)}
        {#if offer.kind === 'loan'}
          · зарплата {offer.wage_share}%
        {/if}
      </span>
      <span class="tf-offer-card-status">
        {offerStatusLabel(offer.status)}
        {#if offer.status === 'pending' && offer.expires_at}
          · до {formatDate(offer.expires_at)}
        {/if}
        {#if offer.status === 'counter' && offer.due}
          · ответ до {formatDate(offer.due)}
        {/if}
        {#if offer.executed_at}
          · переход завершён
        {:else if offer.execute_on && offer.status === 'accepted'}
          · переход {formatDate(offer.execute_on)}
        {/if}
      </span>
      <span class="tf-offer-card-message">{offer.message}</span>
      {#if offer.counter}
        <span class="tf-offer-card-counter">
          Контрпредложение: {formatValue(offer.counter.amount)}
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
</article>
