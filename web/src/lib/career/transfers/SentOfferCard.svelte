<script>
  import Accordion from '../../ui/Accordion.svelte'
  import { formatDate, formatValue, hideBrokenImage, shortRole } from '../../format.js'
  import { offerKindLabel, offerStatusLabel } from '../utils/transfers.js'

  let {
    offer,
    open = false,
    onOpen,
    onClose,
    onSelect,
    onAcceptCounter,
    onReoffer,
    onNegotiate,
  } = $props()

  let statusTone = $derived(
    offer.status === 'accepted'
      ? 'is-win'
      : ['refused', 'expired', 'withdrawn'].includes(offer.status)
        ? 'is-loss'
        : 'is-warn',
  )
  let needsAction = $derived(
    Boolean(
      offer.can_accept_counter ||
        offer.can_offer_again ||
        (offer.status === 'accepted' && !offer.signed),
    ),
  )
  let accordionAmount = $derived(
    offer.counter
      ? (offer.kind === 'loan' ? offer.counter.loan_fee : offer.counter.amount)
      : offer.amount,
  )
  let accordionLabel = $derived(offer.counter ? 'Контрпредложение клуба' : 'Предложение')
  let pendingNote = $derived(
    offer.due
      ? `Клуб ещё не ответил. Ответ до ${formatDate(offer.due)}`
      : 'Клуб ещё не ответил.',
  )
  let signedNote = $derived(
    offer.execute_on
      ? `Переход завершён · присоединится ${formatDate(offer.execute_on)}`
      : 'Переход завершён.',
  )

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

<article class="tf-offer-row" class:is-open={open}>
  <button
    class="tf-offer-row-main"
    data-nav
    data-offer-card={offer.offer_id}
    aria-expanded={open}
    onfocus={() => onSelect?.(offer)}
    onclick={onOpen}
  >
    <span class="tf-offer-status">
      {#if needsAction}
        <i class="tf-offer-flag" title="Требуется ответ" aria-label="Требуется ответ">!</i>
      {:else}
        <i
          class="tf-offer-dot {statusTone}"
          title={offerStatusLabel(offer.status)}
          aria-label={offerStatusLabel(offer.status)}
        ></i>
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

  <Accordion {open} onclose={onClose}>
    <div class="tf-offer-accordion">
      <div class="tf-offer-accordion-col">
        <span class="tf-offer-accordion-title">Переговоры</span>
        <div class="tf-offer-acc-actions">
          {#if offer.status === 'pending'}
            <span class="tf-offer-acc-note">{pendingNote}</span>
          {:else if offer.status === 'accepted'}
            {#if offer.signed}
              <span class="tf-offer-acc-note">{signedNote}</span>
            {:else}
              <button
                class="tf-offer-acc-action is-primary"
                data-nav
                data-offer-action
                onclick={onNegotiate}
              >
                Переговоры по контракту
              </button>
            {/if}
          {:else}
            {#if offer.can_accept_counter}
              <button
                class="tf-offer-acc-action is-primary"
                data-nav
                data-offer-action
                onclick={onAcceptCounter}
              >
                Принять контрпредложение
              </button>
            {:else if offer.status === 'counter'}
              <span class="tf-offer-acc-note">
                Недостаточно средств для контрпредложения.
              </span>
            {/if}
            {#if offer.can_offer_again}
              <button class="tf-offer-acc-action" data-nav data-offer-action onclick={onReoffer}>
                {offer.status === 'refused'
                  ? 'Отправить повторное предложение'
                  : 'Отправить новое предложение'}
              </button>
            {/if}
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
            <span class="tf-offer-acc-club-label">{accordionLabel}</span>
            <strong class="tf-offer-acc-club-amount">{formatValue(accordionAmount)}</strong>
          </div>
        </div>
      </div>
    </div>
  </Accordion>
</article>
