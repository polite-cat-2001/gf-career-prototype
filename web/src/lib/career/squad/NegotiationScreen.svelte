<script>
  import ContractTerms from '../shared/ContractTerms.svelte'
  import CentreInfoRow from '../shared/CentreInfoRow.svelte'
  import CentreProfile from '../shared/CentreProfile.svelte'
  import { contractRoleLabel, formatDate, formatValue, plural } from '../../format.js'

  let {
    player,
    state,
    terms,
    draft,
    onOpenAmount,
    onAdjustField,
    onClose,
    onSign,
    onAcceptCounter,
    onSubmit,
  } = $props()
</script>

<div class="negotiation">
  <aside class="negotiation-player scroll-area">
    <CentreProfile {player} eyebrow={'Продление контракта'} />
    <section class="centre-block">
      <div class="centre-block-head">Текущий контракт</div>
      <CentreInfoRow label={'Амплуа'} value={player.squad_role_label ?? '—'} />
      <CentreInfoRow label={'Срок'} value={`${player.contract?.years ?? 1} ${plural(
          player.contract?.years ?? 1,
          'год',
          'года',
          'лет',
        )}`} />
      <CentreInfoRow
        label={'Зарплата'}
        value={`${formatValue(player.contract?.weekly_wage ?? 0)} / нед.`}
      />
      <CentreInfoRow
        label={'Отступные'}
        value={formatValue(player.contract?.release_clause ?? 0)}
      />
    </section>
  </aside>

  <section class="negotiation-form scroll-area">
    {#if state?.status === 'pending'}
      <div class="negotiation-head">
        <span class="squad-kicker">Ожидание ответа</span>
        <strong class="negotiation-title">Игрок думает</strong>
      </div>
      <p class="negotiation-note">
        {state.message}
        {#if state.due}
          Ответ до {formatDate(state.due)}
        {/if}
      </p>
      <ContractTerms terms={state.offer} />
    {:else if state?.status === 'accepted'}
      <div class="negotiation-head">
        <span class="squad-kicker">Согласовано</span>
        <strong class="negotiation-title">Условия приняты</strong>
      </div>
      <p class="negotiation-note">{state.message}</p>
      <ContractTerms terms={terms} />
    {:else}
      <div class="negotiation-head">
        <span class="squad-kicker">Новый контракт</span>
        <strong class="negotiation-title">Условия</strong>
      </div>

      <div class="negotiation-fields">
        <button
          class="neg-field"
          data-nav
          data-cycle="negotiation"
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
          data-cycle="negotiation"
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
          data-cycle="negotiation"
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
          data-cycle="negotiation"
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
          <span class="squad-kicker">Контрпредложение игрока</span>
          <p class="negotiation-note">{state.message}</p>
          <ContractTerms terms={state.counter} />
        </div>
      {:else if state?.status === 'refused'}
        <div class="neg-reply is-refused">
          <span class="squad-kicker">Отказ</span>
          <p class="negotiation-note">{state.message}</p>
        </div>
      {/if}
    {/if}

    <div class="negotiation-actions">
      {#if state?.status === 'pending'}
        <button
          class="shelf-action is-primary"
          data-nav
          data-autofocus
          onclick={onClose}
        >
          Вернуться
        </button>
      {:else if state?.status === 'accepted'}
        {#if state.affordable === false}
          <p class="negotiation-note is-warning">
            Недостаточно средств, чтобы подписать контракт.
          </p>
        {/if}
        <button
          class="shelf-action is-primary"
          data-nav
          data-autofocus
          disabled={state.affordable === false}
          onclick={onSign}
        >
          Подписать контракт
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
            disabled={state.affordable === false}
            onclick={onAcceptCounter}
          >
            Принять условия игрока
          </button>
        {/if}
        <button class="shelf-action is-primary" data-nav onclick={onSubmit}>
          {state?.status === 'refused' ? 'Предложить снова' : 'Предложить условия'}
        </button>
      {/if}
    </div>
  </section>
</div>
