<script>
  import { formatValue, hideBrokenImage, shortRole } from '../../format.js'
  import { offerKindLabel } from '../utils/transfers.js'

  let {
    offer,
    player,
    finance,
    busy = false,
    onOpenAmount,
    onAdjustField,
    onToggleBuyout,
    onSubmit,
  } = $props()
</script>

<div class="tf-offer">
  <header class="tf-filters-head">
    <span class="tf-crumbs">Трансферы <i>›</i> Предложение клубу</span>
    <span class="tf-crumbs-note">{offerKindLabel(offer.kind)}</span>
  </header>
  <div class="tf-offer-body">
    <aside class="tf-offer-player">
      <span class="tf-offer-photo">
        <img src={player.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <strong class="tf-offer-name">{player.name}</strong>
      <div class="tf-offer-facts">
        <span>ЛЕТ <b>{player.age ?? '—'}</b></span>
        <span>АМПЛУА <b>{shortRole(player.role)}</b></span>
        <span>РОСТ <b>{player.height ?? '—'} см</b></span>
      </div>
      <div class="tf-offer-club">
        {#if player.club_logo}
          <img src={player.club_logo} alt="" onerror={hideBrokenImage} />
        {/if}
        <span>{player.club_name ?? 'Свободный агент'}</span>
      </div>
      <div class="tf-offer-balance">
        <span>Баланс клуба</span>
        <strong>{formatValue(finance.balance)}</strong>
      </div>
      <div class="tf-offer-clause">
        <span>Отступные</span>
        <strong>{formatValue(player.release_clause ?? 0)}</strong>
      </div>
    </aside>

    <section class="tf-offer-form scroll-area">
      <div class="negotiation-fields">
        {#if offer.kind === 'loan'}
          <button
            class="neg-field"
            data-nav
            data-cycle="offer"
            data-field="loan_fee"
            data-autofocus
            onclick={() => onOpenAmount('loan_fee')}
          >
            <span class="neg-field-label">Плата за аренду</span>
            <strong class="neg-field-value">{formatValue(offer.loan_fee)}</strong>
            <span class="neg-field-hint">← → шаг · A точная сумма</span>
          </button>
          <button
            class="neg-field"
            data-nav
            data-cycle="offer"
            data-field="wage_share"
            onclick={() => onAdjustField('wage_share', 1)}
          >
            <span class="neg-field-label">Доля зарплаты</span>
            <strong class="neg-field-value">{offer.wage_share}%</strong>
            <span class="neg-field-hint">← → шаг 5%</span>
          </button>
        {:else}
          <button
            class="neg-field"
            data-nav
            data-cycle="offer"
            data-field="amount"
            data-autofocus
            onclick={() => onOpenAmount('amount')}
          >
            <span class="neg-field-label">
              {offer.buyout ? 'Выкуп по отступным' : 'Сумма предложения'}
            </span>
            <strong class="neg-field-value">
              {formatValue(offer.buyout ? player.release_clause : offer.amount)}
            </strong>
            <span class="neg-field-hint">
              {offer.buyout ? 'Отступные нельзя изменить' : '← → шаг · A точная сумма'}
            </span>
          </button>
          {#if Number(player.release_clause) > 0}
            <button
              class="neg-field"
              data-nav
              data-cycle="offer"
              data-field="buyout"
              onclick={onToggleBuyout}
            >
              <span class="neg-field-label">Выкуп по отступным</span>
              <strong class="neg-field-value">
                {offer.buyout ? 'Включён' : 'Выключен'}
              </strong>
              <span class="neg-field-hint">A или ← → переключить</span>
            </button>
          {/if}
        {/if}
      </div>

      <button
        class="shelf-action is-primary tf-offer-send"
        class:is-disabled={busy}
        data-nav
        onclick={onSubmit}
        disabled={busy}
      >
        {busy ? 'Отправляем…' : 'Отправить предложение'}
      </button>
      <p class="tf-offer-note">
        Ответ клуба придёт через 2–4 дня и появится в «Отправленных предложениях».
      </p>
    </section>
  </div>
</div>
