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

<div class="gf-step gf-contract">
  <aside class="gf-contract__player">
    <div class="gf-contract__profile">
      <span class="gf-contract__photo">
        <img src={player.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="gf-contract__profile-info">
        <span class="gf-contract__eyebrow">
          {isLoan ? 'Аренда' : offer || player.club_id ? 'Трансфер' : 'Свободный агент'}
        </span>
        <strong class="gf-contract__name">{player.name}</strong>
        <span class="gf-contract__sub">
          {positionLabel(player.position)} · {shortRole(player.role)} ·
          {player.overall ? `${Math.round(player.overall)} OVR` : '—'}
        </span>
      </div>
    </div>

    <section class="gf-contract__block">
      <div class="gf-contract__block-head">Условия сделки</div>
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
        <p class="gf-step__note">
          Приблизительная зарплата по отчёту скаута. Точные требования игрок
          раскроет в контрпредложении.
        </p>
      {/if}
    </section>
  </aside>

  <section class="gf-contract__form">
    {#if state?.status === 'pending'}
      <div class="gf-contract__head">
        <span class="gf-contract__eyebrow">Ожидание ответа</span>
        <strong class="gf-contract__title">Игрок думает</strong>
      </div>
      <p class="gf-step__note">
        {state.message}
        {#if state.due}
          Ответ до {formatDate(state.due)}
        {/if}
      </p>
      {#if state.offer}
        <ContractTerms terms={state.offer} />
      {/if}
    {:else if state?.status === 'accepted'}
      <div class="gf-contract__head">
        <span class="gf-contract__eyebrow">Согласовано</span>
        <strong class="gf-contract__title">Условия приняты</strong>
      </div>
      <p class="gf-step__note">{state.message}</p>
      {#if terms}
        <ContractTerms {terms} />
      {/if}
      <p class="gf-step__note">
        Переход вступит в силу сразу, если трансферное окно открыто, иначе — при его
        открытии.
      </p>
    {:else}
      <div class="gf-contract__head">
        <span class="gf-contract__eyebrow">Личный контракт</span>
        <strong class="gf-contract__title">Условия</strong>
      </div>

      {#if draft}
        <div class="gf-fields">
          <button
            class="gf-field"
            data-nav
            data-cycle="contract"
            data-field="weekly_wage"
            data-autofocus
            onclick={() => onOpenAmount('weekly_wage')}
          >
            <span class="gf-field__label">Зарплата в неделю</span>
            <strong class="gf-field__value">{formatValue(draft.weekly_wage)}</strong>
            <span class="gf-field__hint">← → шаг · A точная сумма</span>
          </button>
          <button
            class="gf-field"
            data-nav
            data-cycle="contract"
            data-field="years"
            onclick={() => onAdjustField('years', 1)}
          >
            <span class="gf-field__label">Срок</span>
            <strong class="gf-field__value">
              {draft.years}
              {plural(draft.years, 'год', 'года', 'лет')}
            </strong>
            <span class="gf-field__hint">← → изменить срок</span>
          </button>
          <button
            class="gf-field"
            data-nav
            data-cycle="contract"
            data-field="squad_role"
            onclick={() => onAdjustField('squad_role', 1)}
          >
            <span class="gf-field__label">Амплуа</span>
            <strong class="gf-field__value">{contractRoleLabel(draft.squad_role)}</strong>
            <span class="gf-field__hint">← → выбрать амплуа</span>
          </button>
          <button
            class="gf-field"
            data-nav
            data-cycle="contract"
            data-field="release_clause"
            onclick={() => onOpenAmount('release_clause')}
          >
            <span class="gf-field__label">Отступные</span>
            <strong class="gf-field__value">{formatValue(draft.release_clause)}</strong>
            <span class="gf-field__hint">← → шаг · A точная сумма</span>
          </button>
        </div>

        {#if state?.counter}
          <div class="gf-reply">
            <span class="gf-contract__eyebrow">Контрпредложение игрока</span>
            <p class="gf-step__note">{state.message}</p>
            <ContractTerms terms={state.counter} />
          </div>
        {:else if state?.status === 'refused'}
          <div class="gf-reply is-refused">
            <span class="gf-contract__eyebrow">Отказ</span>
            <p class="gf-step__note">{state.message}</p>
          </div>
        {/if}
      {:else}
        <p class="gf-step__note">Условия контракта недоступны.</p>
      {/if}
    {/if}

    <div class="gf-step__actions">
      {#if state?.status === 'pending'}
        <button class="gf-action gf-action--primary" data-nav data-autofocus onclick={onClose}>
          <span class="gf-action__label">Вернуться</span>
          <span class="gf-action__key">A</span>
        </button>
      {:else if state?.status === 'accepted'}
        {#if state.affordable === false}
          <p class="gf-step__note is-warning">
            Недостаточно средств, чтобы завершить переход.
          </p>
        {/if}
        <button
          class="gf-action gf-action--primary"
          data-nav
          data-autofocus
          disabled={state.affordable === false || busy}
          onclick={onSign}
        >
          <span class="gf-action__label">{busy ? 'Подписываем…' : 'Подписать'}</span>
          <span class="gf-action__key">A</span>
        </button>
      {:else}
        {#if state?.counter}
          {#if state.affordable === false}
            <p class="gf-step__note is-warning">
              Недостаточно средств, чтобы принять условия игрока.
            </p>
          {/if}
          <button
            class="gf-action"
            data-nav
            disabled={state.affordable === false || busy}
            onclick={onAcceptCounter}
          >
            <span class="gf-action__label">Принять условия игрока</span>
            <span class="gf-action__key">A</span>
          </button>
        {/if}
        <button
          class="gf-action gf-action--primary"
          data-nav
          onclick={onSubmit}
          disabled={busy}
        >
          <span class="gf-action__label">
            {state?.status === 'refused' ? 'Предложить снова' : 'Предложить условия'}
          </span>
          <span class="gf-action__key">A</span>
        </button>
      {/if}
    </div>
  </section>
</div>
