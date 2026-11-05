<script>
  import Accordion from '../../ui/Accordion.svelte'
  import { formatValue, hideBrokenImage, shortRole } from '../../format.js'
  import { offerKindLabel } from '../utils/transfers.js'

  let {
    offer,
    open = false,
    onOpen,
    onSelect,
    onAccept,
    onRefuse,
    onCounter,
  } = $props()

  let pending = $derived(offer.status === 'pending')

  function dayMonth(value) {
    if (!value) return '—'
    const parsed = new Date(`${value}T00:00:00`)
    if (Number.isNaN(parsed.getTime())) return value
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
    }).format(parsed)
  }
</script>

<article
  class="tf-offer-row"
  class:is-open={open}
>
  <button
    class="tf-offer-row-main"
    data-nav
    data-incoming-card={offer.offer_id}
    aria-expanded={open}
    onfocus={() => onSelect?.(offer)}
    onclick={onOpen}
  >
    <span class="tf-offer-status">
      {#if pending}
        <i class="tf-offer-flag" title="Требуется ответ" aria-label="Требуется ответ">!</i>
      {/if}
    </span>
    <span class="tf-offer-crest">
      {#if offer.club_logo}
        <img src={offer.club_logo} alt="" onerror={hideBrokenImage} />
      {/if}
    </span>
    <span class="tf-offer-kind">{offerKindLabel(offer.kind)}</span>
    <span class="tf-offer-player">
      <span class="tf-offer-photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <span class="tf-offer-name">{offer.name}</span>
    </span>
    <span class="tf-offer-pos">{shortRole(offer.role)}</span>
    <span class="tf-offer-date">{dayMonth(offer.created_at)}</span>
  </button>

  <Accordion {open}>
    <div class="tf-offer-accordion">
      <div class="tf-offer-accordion-col">
        <span class="tf-offer-accordion-title">Переговоры</span>
        <div class="tf-offer-acc-actions">
          <button
            class="tf-offer-acc-action is-primary"
            data-nav
            data-incoming-action
            disabled={!offer.can_accept}
            onclick={onAccept}
          >
            {offer.can_accept
              ? 'Принять предложение'
              : 'Нельзя продать — в составе мало игроков'}
          </button>
          <button class="tf-offer-acc-action" data-nav data-incoming-action onclick={onRefuse}>
            Отклонить предложение
          </button>
          {#if offer.can_counter}
            <button class="tf-offer-acc-action" data-nav data-incoming-action onclick={onCounter}>
              Начать переговоры
            </button>
          {/if}
        </div>
      </div>

      <div class="tf-offer-accordion-col">
        <span class="tf-offer-accordion-title">Трансферные переговоры</span>
        <div class="tf-offer-acc-club">
          {#if offer.club_logo}
            <img src={offer.club_logo} alt="" onerror={hideBrokenImage} />
          {/if}
          <div class="tf-offer-acc-club-info">
            <span class="tf-offer-acc-club-name">{offer.club_name}</span>
            <span class="tf-offer-acc-club-label">
              {offer.kind === 'loan' ? 'Плата за аренду' : 'Предложение'}
            </span>
            <strong class="tf-offer-acc-club-amount">{formatValue(offer.amount)}</strong>
          </div>
        </div>
      </div>
    </div>
  </Accordion>
</article>
