<script>
  import { formatValue, hideBrokenImage, shortRole } from '../../format.js'

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

<div class="gf-step">
  <div class="gf-offer">
    <aside class="gf-offer__player">
      <span class="gf-offer__photo">
        <img src={player.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <strong class="gf-offer__name">{player.name}</strong>
      <div class="gf-offer__facts">
        <span>ЛЕТ <b>{player.age ?? '—'}</b></span>
        <span>АМПЛУА <b>{shortRole(player.role)}</b></span>
        <span>РОСТ <b>{player.height ?? '—'} см</b></span>
      </div>
      <div class="gf-offer__club">
        {#if player.club_logo}
          <img src={player.club_logo} alt="" onerror={hideBrokenImage} />
        {/if}
        <span>{player.club_name ?? 'Свободный агент'}</span>
      </div>
      <div class="gf-offer__stat">
        <span>Баланс клуба</span>
        <strong>{formatValue(finance.balance)}</strong>
      </div>
      <div class="gf-offer__stat">
        <span>Отступные</span>
        <strong>{formatValue(player.release_clause ?? 0)}</strong>
      </div>
    </aside>

    <section class="gf-offer__form">
      <div class="gf-fields">
        {#if offer.kind === 'loan'}
          <button
            class="gf-field"
            data-nav
            data-cycle="offer"
            data-field="loan_fee"
            data-autofocus
            onclick={() => onOpenAmount('loan_fee')}
          >
            <span class="gf-field__label">Плата за аренду</span>
            <strong class="gf-field__value">{formatValue(offer.loan_fee)}</strong>
            <span class="gf-field__hint">← → шаг · A точная сумма</span>
          </button>
          <button
            class="gf-field"
            data-nav
            data-cycle="offer"
            data-field="wage_share"
            onclick={() => onAdjustField('wage_share', 1)}
          >
            <span class="gf-field__label">Доля зарплаты</span>
            <strong class="gf-field__value">{offer.wage_share}%</strong>
            <span class="gf-field__hint">← → шаг 5%</span>
          </button>
        {:else}
          <button
            class="gf-field"
            data-nav
            data-cycle="offer"
            data-field="amount"
            data-autofocus
            onclick={() => onOpenAmount('amount')}
          >
            <span class="gf-field__label">
              {offer.buyout ? 'Выкуп по отступным' : 'Сумма предложения'}
            </span>
            <strong class="gf-field__value">
              {formatValue(offer.buyout ? player.release_clause : offer.amount)}
            </strong>
            <span class="gf-field__hint">
              {offer.buyout ? 'Отступные нельзя изменить' : '← → шаг · A точная сумма'}
            </span>
          </button>
          {#if Number(player.release_clause) > 0}
            <button
              class="gf-field"
              data-nav
              data-cycle="offer"
              data-field="buyout"
              onclick={onToggleBuyout}
            >
              <span class="gf-field__label">Выкуп по отступным</span>
              <strong class="gf-field__value">
                {offer.buyout ? 'Включён' : 'Выключен'}
              </strong>
              <span class="gf-field__hint">A или ← → переключить</span>
            </button>
          {/if}
        {/if}
      </div>

      <div class="gf-step__actions">
        <button
          class="gf-action gf-action--primary"
          data-nav
          onclick={onSubmit}
          disabled={busy}
        >
          <span class="gf-action__label">
            {busy ? 'Отправляем…' : 'Отправить предложение'}
          </span>
          <span class="gf-action__key">A</span>
        </button>
      </div>
      <p class="gf-step__note">
        Ответ клуба придёт через 2–4 дня и появится в «Отправленных предложениях».
      </p>
    </section>
  </div>
</div>
