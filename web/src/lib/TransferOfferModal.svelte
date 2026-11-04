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

  let { offer, onaccept = null, onreoffer = null, onnegotiate = null } = $props()

  let modalLayer = $state(null)

  onMount(() => trapModalFocus(modalLayer))

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

<div class="gf-modal-layer" bind:this={modalLayer}>
  <div
    class="gf-modal gf-modal--offer tf-offer-modal"
    role="dialog"
    aria-modal="true"
    aria-label="Предложение клубу"
    tabindex="-1"
  >
    <header class="gf-modal__head">
      <span class="gf-modal__photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="gf-modal__title">
        <span class="gf-modal__eyebrow">Предложение клубу</span>
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
        <span>{offer.club_name ?? 'Свободный агент'}</span>
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
        {#if offer.buyout}
          <div class="gf-modal__row">
            <span>Выкуп по отступным</span>
            <strong>Да</strong>
          </div>
        {/if}
        {#if offer.due && offer.status === 'pending'}
          <div class="gf-modal__row">
            <span>Ответ</span>
            <strong>до {formatDate(offer.due)}</strong>
          </div>
        {/if}
        {#if offer.status === 'refused' && offer.retry_after}
          <div class="gf-modal__row">
            <span>Повтор</span>
            <strong>после {formatDate(offer.retry_after)}</strong>
          </div>
        {/if}
        {#if offer.counter}
          <div class="gf-modal__row is-counter">
            <span>Контрпредложение</span>
            <strong>{formatValue(offer.counter.amount)}</strong>
          </div>
          {#if offer.kind === 'loan'}
            <div class="gf-modal__row is-counter">
              <span>Доля зарплаты</span>
              <strong>{offer.counter.wage_share}%</strong>
            </div>
          {/if}
        {/if}
        {#if offer.contract_status === 'accepted'}
          <div class="gf-modal__row is-counter">
            <span>Контракт</span>
            <strong>Согласован</strong>
          </div>
        {:else if offer.contract_status === 'signed'}
          <div class="gf-modal__row is-counter">
            <span>Контракт</span>
            <strong>Подписан</strong>
          </div>
        {/if}
      </div>
      <p class="gf-modal__message">{offer.message}</p>

      <div class="gf-modal__actions">
        {#if offer.status === 'accepted'}
          {#if offer.signed}
            <p class="gf-action-note">
              Переход завершён
              {#if offer.execute_on}· присоединится {formatDate(offer.execute_on)}{/if}
            </p>
          {:else if onnegotiate}
            <button class="gf-action" data-nav data-autofocus onclick={onnegotiate}>
              <span class="gf-action__label">Переговоры по контракту</span>
              <span class="gf-action__key">A</span>
            </button>
          {:else}
            <div
              class="gf-action is-disabled"
              data-nav
              data-autofocus
              role="button"
              tabindex="0"
              aria-disabled="true"
            >
              <span class="gf-action__label">Переговоры по контракту</span>
              <span class="gf-action__ticket">#17</span>
            </div>
          {/if}
        {:else if offer.status === 'counter'}
          {#if offer.can_accept_counter}
            <button class="gf-action" data-nav data-autofocus onclick={onaccept}>
              <span class="gf-action__label">Принять контрпредложение</span>
              <span class="gf-action__key">A</span>
            </button>
          {:else}
            <p class="gf-modal__note">
              Недостаточно средств для контрпредложения
            </p>
          {/if}
          {#if offer.can_offer_again}
            <button class="gf-action" data-nav onclick={onreoffer}>
              <span class="gf-action__label">Отправить новое предложение</span>
              <span class="gf-action__key">A</span>
            </button>
          {/if}
        {:else if offer.status === 'refused'}
          {#if offer.can_offer_again}
            <button class="gf-action" data-nav data-autofocus onclick={onreoffer}>
              <span class="gf-action__label">Отправить повторное предложение</span>
              <span class="gf-action__key">A</span>
            </button>
          {/if}
        {:else if offer.status === 'withdrawn'}
          <button class="gf-action" data-nav data-autofocus onclick={onreoffer}>
            <span class="gf-action__label">Отправить новое предложение</span>
            <span class="gf-action__key">A</span>
          </button>
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
