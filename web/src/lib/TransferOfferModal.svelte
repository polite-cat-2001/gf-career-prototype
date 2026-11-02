<script>
  import { inputDevice } from './input.js'
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    shortRole,
  } from './format.js'

  let { offer, onaccept = null, onreoffer = null, onnegotiate = null } = $props()

  const STATUS_LABELS = {
    pending: 'Ожидает ответа',
    counter: 'Контрпредложение',
    accepted: 'Принято',
    refused: 'Отказ',
  }

  const KIND_LABELS = {
    transfer: 'Трансфер',
    loan: 'Аренда',
  }

  let statusLabel = $derived(STATUS_LABELS[offer.status] ?? offer.status)
  let kindLabel = $derived(KIND_LABELS[offer.kind] ?? offer.kind)
  let hasActions = $derived(
    offer.status === 'accepted' ||
      offer.status === 'withdrawn' ||
      (offer.status === 'counter' &&
        (offer.can_accept_counter || offer.can_offer_again)) ||
      (offer.status === 'refused' && offer.can_offer_again),
  )
</script>

<div class="sc-modal-layer">
  <div
    class="tf-actions sc-actions tf-offer-modal"
    role="dialog"
    aria-modal="true"
    aria-label="Предложение клубу"
    tabindex="-1"
  >
    <header class="tf-actions-head">
      <span class="tf-actions-photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="tf-actions-title">
        <span class="eyebrow">Предложение клубу</span>
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
        <span>{offer.club_name ?? 'Свободный агент'}</span>
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
      {#if offer.buyout}
        <div class="tf-offer-modal-row">
          <span>Выкуп по отступным</span>
          <strong>Да</strong>
        </div>
      {/if}
      {#if offer.due && offer.status === 'pending'}
        <div class="tf-offer-modal-row">
          <span>Ответ</span>
          <strong>до {formatDate(offer.due)}</strong>
        </div>
      {/if}
      {#if offer.status === 'refused' && offer.retry_after}
        <div class="tf-offer-modal-row">
          <span>Повтор</span>
          <strong>после {formatDate(offer.retry_after)}</strong>
        </div>
      {/if}
      {#if offer.counter}
        <div class="tf-offer-modal-row is-counter">
          <span>Контрпредложение</span>
          <strong>{formatValue(offer.counter.amount)}</strong>
        </div>
        {#if offer.kind === 'loan'}
          <div class="tf-offer-modal-row is-counter">
            <span>Доля зарплаты</span>
            <strong>{offer.counter.wage_share}%</strong>
          </div>
        {/if}
      {/if}
      {#if offer.contract_status === 'accepted'}
        <div class="tf-offer-modal-row is-counter">
          <span>Контракт</span>
          <strong>Согласован</strong>
        </div>
      {:else if offer.contract_status === 'signed'}
        <div class="tf-offer-modal-row is-counter">
          <span>Контракт</span>
          <strong>Подписан</strong>
        </div>
      {/if}
      <p class="tf-offer-modal-message">{offer.message}</p>
    </div>

    <div class="tf-action-list">
      {#if offer.status === 'accepted'}
        {#if offer.signed}
          <p class="tf-action-note">
            Переход завершён
            {#if offer.execute_on}· присоединится {formatDate(offer.execute_on)}{/if}
          </p>
        {:else if onnegotiate}
          <button class="tf-action" data-nav data-autofocus onclick={onnegotiate}>
            <span>Переговоры по контракту</span>
            <span class="tf-action-key">A</span>
          </button>
        {:else}
          <div
            class="tf-action is-disabled"
            data-nav
            data-autofocus
            role="button"
            tabindex="0"
            aria-disabled="true"
          >
            <span>Переговоры по контракту</span>
            <span class="tf-action-ticket">#17</span>
          </div>
        {/if}
      {:else if offer.status === 'counter'}
        {#if offer.can_accept_counter}
          <button class="tf-action" data-nav data-autofocus onclick={onaccept}>
            <span>Принять контрпредложение</span>
            <span class="tf-action-key">A</span>
          </button>
        {:else}
          <p class="tf-offer-modal-note">
            Недостаточно средств для контрпредложения
          </p>
        {/if}
        {#if offer.can_offer_again}
          <button class="tf-action" data-nav onclick={onreoffer}>
            <span>Отправить новое предложение</span>
            <span class="tf-action-key">A</span>
          </button>
        {/if}
      {:else if offer.status === 'refused'}
        {#if offer.can_offer_again}
          <button class="tf-action" data-nav data-autofocus onclick={onreoffer}>
            <span>Отправить повторное предложение</span>
            <span class="tf-action-key">A</span>
          </button>
        {/if}
      {:else if offer.status === 'withdrawn'}
        <button class="tf-action" data-nav data-autofocus onclick={onreoffer}>
          <span>Отправить новое предложение</span>
          <span class="tf-action-key">A</span>
        </button>
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
