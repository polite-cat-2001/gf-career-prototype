<script>
  import { inputDevice } from './input.js'
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    shortRole,
  } from './format.js'

  let { offer, onaccept = null, onrefuse = null, oncounter = null } = $props()

  const STATUS_LABELS = {
    pending: 'Ожидает ответа',
    counter: 'Ждём ответ клуба',
    accepted: 'Принято',
    refused: 'Отказ',
    expired: 'Истекло',
  }

  const KIND_LABELS = {
    transfer: 'Трансфер',
    loan: 'Аренда',
  }

  let statusLabel = $derived(STATUS_LABELS[offer.status] ?? offer.status)
  let kindLabel = $derived(KIND_LABELS[offer.kind] ?? offer.kind)
  let hasActions = $derived(offer.status === 'pending')
  let acceptedNote = $derived.by(() => {
    if (offer.status !== 'accepted') return ''
    if (offer.executed_at) return 'Переход завершён'
    if (offer.execute_on) return `Переход состоится ${formatDate(offer.execute_on)}`
    return 'Переход согласован'
  })
</script>

<div class="sc-modal-layer">
  <div
    class="tf-actions sc-actions tf-offer-modal tf-incoming-modal"
    role="dialog"
    aria-modal="true"
    aria-label="Полученное предложение"
    tabindex="-1"
  >
    <header class="tf-actions-head">
      <span class="tf-actions-photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="tf-actions-title">
        <span class="eyebrow">Полученное предложение</span>
        <strong class="tf-actions-name">{offer.name}</strong>
        <div class="tf-actions-facts">
          <span>ЛЕТ <b>{offer.age ?? '—'}</b></span>
          <span>АМПЛУА <b>{shortRole(offer.role)}</b></span>
          <span>РОСТ <b>{offer.height ? `${offer.height} см` : '—'}</b></span>
          <span>СТАТУС <b>{statusLabel}</b></span>
        </div>
      </div>
      <span class="tf-actions-club">
        {#if offer.club_logo}
          <img src={offer.club_logo} alt="" />
        {/if}
        <span>{offer.club_name || 'Клуб'}</span>
      </span>
    </header>

    <div class="tf-offer-modal-summary">
      <div class="tf-offer-modal-row">
        <span>Тип</span>
        <strong>{kindLabel}</strong>
      </div>
      <div class="tf-offer-modal-row">
        <span>{offer.kind === 'loan' ? 'Плата за аренду' : 'Сумма'}</span>
        <strong>{formatValue(offer.amount)}</strong>
      </div>
      {#if offer.kind === 'loan'}
        <div class="tf-offer-modal-row">
          <span>Доля зарплаты</span>
          <strong>{offer.wage_share}%</strong>
        </div>
      {/if}
      {#if offer.status === 'pending' && offer.expires_at}
        <div class="tf-offer-modal-row">
          <span>Предложение действует до</span>
          <strong>{formatDate(offer.expires_at)}</strong>
        </div>
      {/if}
      {#if offer.status === 'counter' && offer.due}
        <div class="tf-offer-modal-row">
          <span>Ответ клуба</span>
          <strong>до {formatDate(offer.due)}</strong>
        </div>
      {/if}
      {#if offer.counter}
        <div class="tf-offer-modal-row is-counter">
          <span>Контрпредложение</span>
          <strong>{formatValue(offer.counter.amount)}</strong>
        </div>
      {/if}
      {#if acceptedNote}
        <div class="tf-offer-modal-row is-counter">
          <span>Переход</span>
          <strong>{acceptedNote}</strong>
        </div>
      {/if}
      <p class="tf-offer-modal-message">{offer.message}</p>
    </div>

    <div class="tf-action-list">
      {#if offer.status === 'pending'}
        <button class="tf-action" data-nav data-autofocus onclick={onaccept} disabled={!offer.can_accept}>
          <span>{offer.can_accept ? 'Принять предложение' : 'Нельзя продать — в составе мало игроков'}</span>
          {#if offer.can_accept}
            <span class="tf-action-key">A</span>
          {/if}
        </button>
        <button class="tf-action" data-nav onclick={oncounter}>
          <span>Контрпредложение</span>
          <span class="tf-action-key">A</span>
        </button>
        <button class="tf-action" data-nav onclick={onrefuse}>
          <span>Отказать</span>
          <span class="tf-action-key">A</span>
        </button>
      {:else if offer.status === 'counter'}
        <p class="tf-offer-modal-note">
          Клуб ответит в течение 2–4 дней.
        </p>
      {:else if offer.status === 'accepted'}
        <p class="tf-action-note">{acceptedNote}</p>
      {:else if offer.status === 'refused'}
        <p class="tf-offer-modal-note">Предложение отклонено.</p>
      {:else if offer.status === 'expired'}
        <p class="tf-offer-modal-note">Срок предложения истёк.</p>
      {/if}
    </div>

    <footer class="tf-actions-foot">
      {#if hasActions}
        {#if $inputDevice === 'gamepad'}
          <span><kbd>A</kbd> Выбор</span>
        {:else}
          <span><kbd>Enter</kbd> Выбор</span>
        {/if}
      {/if}
      {#if $inputDevice === 'gamepad'}
        <span><kbd>B</kbd> Назад</span>
      {:else}
        <span><kbd>Esc</kbd> Назад</span>
      {/if}
    </footer>
  </div>
</div>
