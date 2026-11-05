<script>
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    shortRole,
  } from '../../format.js'
  import {
    contractStatusLabel,
    offerKindLabel,
    offerStatusLabel,
  } from '../utils/transfers.js'

  let { offer } = $props()

  let overall = $derived(Math.round(offer?.overall ?? 0))
  let citizenship = $derived(
    Array.isArray(offer?.citizenship) ? offer.citizenship.join(', ') : offer?.citizenship,
  )
  let note = $derived.by(() => {
    if (!offer) return ''
    if (offer.status === 'pending') {
      return offer.due
        ? `Клуб ещё не ответил. Ответ до ${formatDate(offer.due)}`
        : 'Клуб ещё не ответил.'
    }
    if (offer.status === 'counter') {
      return offer.message || 'Клуб предложил новые условия.'
    }
    if (offer.status === 'accepted') {
      if (offer.signed) {
        return offer.execute_on
          ? `Переход завершён. Игрок присоединится ${formatDate(offer.execute_on)}.`
          : 'Переход завершён.'
      }
      return offer.message || 'Клуб принял предложение.'
    }
    if (offer.status === 'refused') {
      return offer.retry_after
        ? `Клуб отказал. Повторить можно после ${formatDate(offer.retry_after)}.`
        : 'Клуб отказал.'
    }
    if (offer.status === 'withdrawn') return 'Предложение отозвано.'
    return offer.message
  })
  let contractLabel = $derived.by(() => {
    const label = contractStatusLabel(offer?.contract_status)
    return label ? label[0].toUpperCase() + label.slice(1) : null
  })
  let counterAmount = $derived(
    offer?.counter
      ? offer.kind === 'loan'
        ? (offer.counter.loan_fee ?? offer.counter.amount)
        : offer.counter.amount
      : null,
  )
  let needsAction = $derived(
    Boolean(
      offer?.can_accept_counter ||
        offer?.can_offer_again ||
        (offer?.status === 'accepted' && !offer?.signed),
    ),
  )
</script>

<aside class="tf-received-detail" aria-label="Отправленные предложения">
  <header class="tf-offer-detail-title">Отправленные предложения</header>

  {#if offer}
    <div class="tf-offer-detail-hero">
      <span class="tf-offer-detail-photo">
        <img src={offer.photo} alt="" onerror={hideBrokenImage} />
      </span>
      <div class="tf-offer-detail-info">
        <strong class="tf-offer-detail-name">{offer.name}</strong>
        <span class="tf-offer-detail-facts">
          <span>{shortRole(offer.role)}</span>
          <span>Лет: {offer.age ?? '—'}</span>
          <span>Рост: {offer.height ? `${offer.height} см` : '—'}</span>
          {#if citizenship}
            <span>Гражданство: {citizenship}</span>
          {/if}
        </span>
      </div>
      <span class="tf-offer-detail-rating">
        <b>{overall}</b>
        <small>ОБЩ.</small>
      </span>
    </div>

    <div class="tf-offer-detail-values">
      <div>
        <span>Стоимость</span>
        <b>{formatValue(offer.market_value)}</b>
      </div>
      <div>
        <span>Зарплата в неделю</span>
        <b>{formatValue(offer.weekly_wage)}</b>
      </div>
      <div>
        <span>Отступные</span>
        <b>{formatValue(offer.release_clause)}</b>
      </div>
    </div>

    <div class="tf-offer-detail-note">
      <i>{needsAction ? '!' : '·'}</i>
      <p>{note}</p>
    </div>

    <div class="tf-offer-detail-table">
      <span class="tf-offer-detail-th">Кому</span>
      <span class="tf-offer-detail-th">Предложение</span>
      <span class="tf-offer-detail-th">Статус переговоров</span>
      <span class="tf-offer-detail-th">Тип предложения</span>

      <span class="tf-offer-detail-club">
        {#if offer.club_logo}
          <img src={offer.club_logo} alt="" onerror={hideBrokenImage} />
        {/if}
      </span>
      <span class="tf-offer-detail-amount">{formatValue(offer.amount)}</span>
      <span class="tf-offer-detail-status">
        {#if needsAction}<i>!</i>{/if}
        {offerStatusLabel(offer.status)}
      </span>
      <span class="tf-offer-detail-kind">{offerKindLabel(offer.kind)}</span>
    </div>

    <div class="tf-offer-detail-extra">
      {#if offer.kind === 'loan'}
        <div>
          <span>Доля зарплаты</span>
          <b>{offer.wage_share}%</b>
        </div>
      {/if}
      {#if offer.counter}
        <div>
          <span>Контрпредложение клуба</span>
          <b>{formatValue(counterAmount)}</b>
        </div>
        {#if offer.kind === 'loan'}
          <div>
            <span>Доля зарплаты в контрпредложении</span>
            <b>{offer.counter.wage_share}%</b>
          </div>
        {/if}
      {/if}
      {#if offer.due && offer.status === 'pending'}
        <div>
          <span>Ответ до</span>
          <b>{formatDate(offer.due)}</b>
        </div>
      {/if}
      {#if offer.status === 'refused' && offer.retry_after}
        <div>
          <span>Повтор после</span>
          <b>{formatDate(offer.retry_after)}</b>
        </div>
      {/if}
      {#if contractLabel}
        <div>
          <span>Контракт</span>
          <b>{contractLabel}</b>
        </div>
      {/if}
      {#if offer.execute_on}
        <div>
          <span>Переход</span>
          <b>{formatDate(offer.execute_on)}</b>
        </div>
      {/if}
    </div>
  {:else}
    <p class="tf-offer-detail-empty">Выберите предложение в списке.</p>
  {/if}
</aside>
