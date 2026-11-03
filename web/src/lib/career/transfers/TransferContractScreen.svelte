<script>
  import ContractTerms from '../shared/ContractTerms.svelte'
  import CentreInfoRow from '../shared/CentreInfoRow.svelte'
  import {
    contractRoleLabel,
    formatDate,
    formatValue,
    hideBrokenImage,
    plural,
    positionLabel,
    shortRole,
  } from '../../format.js'

  let {
    player,
    state,
    terms,
    draft,
    offer,
    fee,
    balanceAfter,
    busy = false,
    kind,
    wageShare = 100,
    onOpenAmount,
    onAdjustField,
    onClose,
    onSign,
    onAcceptCounter,
    onSubmit,
  } = $props()

  const isLoan = $derived(kind === 'loan')
</script>

<div class="negotiation tf-contract">
  <aside class="negotiation-player scroll-area">
    <div class="centre-profile">
      <span class="centre-photo">
        <img src={player.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="centre-profile-info">
        <span class="eyebrow">
          {isLoan ? 'Аренда' : offer || player.club_id ? 'Трансфер' : 'Свободный агент'}
        </span>
        <strong class="centre-name">{player.name}</strong>
        <span class="centre-sub">
          {positionLabel(player.position)} · {shortRole(player.role)} ·
          {player.overall ? `${Math.round(player.overall)} OVR` : '—'}
        </span>
      </div>
    </div>

    <section class="centre-block">
      <div class="centre-block-head">Условия сделки</div>
      <CentreInfoRow
        label={isLoan ? 'Плата за аренду' : 'Согласованный fee'}
        value={fee > 0 ? formatValue(fee) : 'Без компенсации'}
      />
      <CentreInfoRow label={'Баланс после сделки'} value={formatValue(balanceAfter)} />
      <CentreInfoRow
        label={player.club_id ? 'Текущая зарплата' : 'Зарплата по отчёту'}
        value={player.weekly_wage != null ? formatValue(player.weekly_wage) : '—'}
      />
      {#if isLoan}
        <CentreInfoRow label={'Доля зарплаты'} value={`${wageShare}%`} />
      {/if}
      <CentreInfoRow label={'Клуб'} value={player.club_name ?? 'Свободный агент'} />
      {#if !player.club_id}
        <p class="negotiation-note">
          Приблизительная зарплата по отчёту скаута. Точные требования игрок
          раскроет в контрпредложении.
        </p>
      {/if}
    </section>
  </aside>

  <section class="negotiation-form scroll-area">
    {#if state?.status === 'pending'}
      <div class="negotiation-head">
        <span class="eyebrow">Ожидание ответа</span>
        <strong class="negotiation-title">Игрок думает</strong>
      </div>
      <p class="negotiation-note">
        {state.message}
        {#if state.due}
          Ответ до {formatDate(state.due)}
        {/if}
      </p>
      {#if state.offer}
        <ContractTerms terms={state.offer} />
      {/if}
    {:else if state?.status === 'accepted'}
      <div class="negotiation-head">
        <span class="eyebrow">Согласовано</span>
        <strong class="negotiation-title">Условия приняты</strong>
      </div>
      <p class="negotiation-note">{state.message}</p>
      {#if terms}
        <ContractTerms {terms} />
      {/if}
      <p class="negotiation-note">
        Переход вступит в силу сразу, если трансферное окно открыто, иначе — при его
        открытии.
      </p>
    {:else}
      <div class="negotiation-head">
        <span class="eyebrow">Личный контракт</span>
        <strong class="negotiation-title">Условия</strong>
      </div>

      {#if draft}
        <div class="negotiation-fields">
          <button
            class="neg-field"
            data-nav
            data-cycle="contract"
            data-field="weekly_wage"
            data-autofocus
            onclick={() => onOpenAmount('weekly_wage')}
          >
            <span class="neg-field-label">Зарплата в неделю</span>
            <strong class="neg-field-value">{formatValue(draft.weekly_wage)}</strong>
            <span class="neg-field-hint">← → шаг · A точная сумма</span>
          </button>
          <button
            class="neg-field"
            data-nav
            data-cycle="contract"
            data-field="years"
            onclick={() => onAdjustField('years', 1)}
          >
            <span class="neg-field-label">Срок</span>
            <strong class="neg-field-value">
              {draft.years}
              {plural(draft.years, 'год', 'года', 'лет')}
            </strong>
            <span class="neg-field-hint">← → изменить срок</span>
          </button>
          <button
            class="neg-field"
            data-nav
            data-cycle="contract"
            data-field="squad_role"
            onclick={() => onAdjustField('squad_role', 1)}
          >
            <span class="neg-field-label">Амплуа</span>
            <strong class="neg-field-value">{contractRoleLabel(draft.squad_role)}</strong>
            <span class="neg-field-hint">← → выбрать амплуа</span>
          </button>
          <button
            class="neg-field"
            data-nav
            data-cycle="contract"
            data-field="release_clause"
            onclick={() => onOpenAmount('release_clause')}
          >
            <span class="neg-field-label">Отступные</span>
            <strong class="neg-field-value">{formatValue(draft.release_clause)}</strong>
            <span class="neg-field-hint">← → шаг · A точная сумма</span>
          </button>
        </div>

        {#if state?.counter}
          <div class="neg-reply">
            <span class="eyebrow">Контрпредложение игрока</span>
            <p class="negotiation-note">{state.message}</p>
            <ContractTerms terms={state.counter} />
          </div>
        {:else if state?.status === 'refused'}
          <div class="neg-reply is-refused">
            <span class="eyebrow">Отказ</span>
            <p class="negotiation-note">{state.message}</p>
          </div>
        {/if}
      {:else}
        <p class="negotiation-note">Условия контракта недоступны.</p>
      {/if}
    {/if}

    <div class="negotiation-actions">
      {#if state?.status === 'pending'}
        <button class="shelf-action is-primary" data-nav data-autofocus onclick={onClose}>
          Вернуться
        </button>
      {:else if state?.status === 'accepted'}
        {#if state.affordable === false}
          <p class="negotiation-note is-warning">
            Недостаточно средств, чтобы завершить переход.
          </p>
        {/if}
        <button
          class="shelf-action is-primary"
          data-nav
          data-autofocus
          disabled={state.affordable === false || busy}
          onclick={onSign}
        >
          {busy ? 'Подписываем…' : 'Подписать'}
        </button>
      {:else}
        {#if state?.counter}
          {#if state.affordable === false}
            <p class="negotiation-note is-warning">
              Недостаточно средств, чтобы принять условия игрока.
            </p>
          {/if}
          <button
            class="shelf-action"
            data-nav
            disabled={state.affordable === false || busy}
            onclick={onAcceptCounter}
          >
            Принять условия игрока
          </button>
        {/if}
        <button
          class="shelf-action is-primary"
          data-nav
          onclick={onSubmit}
          disabled={busy}
        >
          {state?.status === 'refused' ? 'Предложить снова' : 'Предложить условия'}
        </button>
      {/if}
    </div>
  </section>
</div>
