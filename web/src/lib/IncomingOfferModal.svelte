<script>
  import { onMount } from 'svelte'
  import { inputDevice } from './input.js'
  import { trapModalFocus } from './ui/modalFocus.js'
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    shortRole,
  } from './format.js'

  let { offer, onaccept = null, onrefuse = null, oncounter = null } = $props()

  let modalLayer = $state(null)

  onMount(() => trapModalFocus(modalLayer))

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

<div class="gf-modal-layer" bind:this={modalLayer}>
  <div
    class="gf-modal gf-modal--offer tf-offer-modal tf-incoming-modal"
    role="dialog"
    aria-modal="true"
    aria-label="Полученное предложение"
    tabindex="-1"
  >
    <header class="gf-modal__head">
      <span class="gf-modal__photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="gf-modal__title">
        <span class="gf-modal__eyebrow">Полученное предложение</span>
        <strong class="gf-modal__name">{offer.name}</strong>
        <div class="gf-modal__facts">
          <span>ЛЕТ <b>{offer.age ?? '—'}</b></span>
          <span>АМПЛУА <b>{shortRole(offer.role)}</b></span>
          <span>РОСТ <b>{offer.height ? `${offer.height} см` : '—'}</b></span>
          <span>СТАТУС <b>{statusLabel}</b></span>
        </div>
      </div>
      <span class="gf-modal__club">
        {#if offer.club_logo}
          <img src={offer.club_logo} alt="" />
        {/if}
        <span>{offer.club_name || 'Клуб'}</span>
      </span>
    </header>

    <div class="gf-modal__body">
      <div class="gf-modal__rows">
        <div class="gf-modal__row">
          <span>Тип</span>
          <strong>{kindLabel}</strong>
        </div>
        <div class="gf-modal__row">
          <span>{offer.kind === 'loan' ? 'Плата за аренду' : 'Сумма'}</span>
          <strong>{formatValue(offer.amount)}</strong>
        </div>
        {#if offer.kind === 'loan'}
          <div class="gf-modal__row">
            <span>Доля зарплаты</span>
            <strong>{offer.wage_share}%</strong>
          </div>
        {/if}
        {#if offer.status === 'pending' && offer.expires_at}
          <div class="gf-modal__row">
            <span>Предложение действует до</span>
            <strong>{formatDate(offer.expires_at)}</strong>
          </div>
        {/if}
        {#if offer.status === 'counter' && offer.due}
          <div class="gf-modal__row">
            <span>Ответ клуба</span>
            <strong>до {formatDate(offer.due)}</strong>
          </div>
        {/if}
        {#if offer.counter}
          <div class="gf-modal__row is-counter">
            <span>Контрпредложение</span>
            <strong>{formatValue(offer.counter.amount)}</strong>
          </div>
        {/if}
        {#if acceptedNote}
          <div class="gf-modal__row is-counter">
            <span>Переход</span>
            <strong>{acceptedNote}</strong>
          </div>
        {/if}
      </div>
      <p class="gf-modal__message">{offer.message}</p>

      <div class="gf-modal__actions">
        {#if offer.status === 'pending'}
          <button class="gf-action" data-nav data-autofocus onclick={onaccept} disabled={!offer.can_accept}>
            <span class="gf-action__label">
              {offer.can_accept ? 'Принять предложение' : 'Нельзя продать — в составе мало игроков'}
            </span>
            {#if offer.can_accept}
              <span class="gf-action__key">A</span>
            {/if}
          </button>
          <button class="gf-action" data-nav onclick={oncounter}>
            <span class="gf-action__label">Контрпредложение</span>
            <span class="gf-action__key">A</span>
          </button>
          <button class="gf-action is-danger" data-nav onclick={onrefuse}>
            <span class="gf-action__label">Отказать</span>
            <span class="gf-action__key">A</span>
          </button>
        {:else if offer.status === 'counter'}
          <p class="gf-modal__note">
            Клуб ответит в течение 2–4 дней.
          </p>
        {:else if offer.status === 'accepted'}
          <p class="gf-action-note">{acceptedNote}</p>
        {:else if offer.status === 'refused'}
          <p class="gf-modal__note">Предложение отклонено.</p>
        {:else if offer.status === 'expired'}
          <p class="gf-modal__note">Срок предложения истёк.</p>
        {/if}
      </div>
    </div>

    <footer class="gf-modal__foot">
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
