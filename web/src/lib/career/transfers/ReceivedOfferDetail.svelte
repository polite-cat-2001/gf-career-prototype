<script>
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    shortRole,
  } from '../../format.js'
  import { offerKindLabel, offerStatusLabel } from '../utils/transfers.js'

  let { offer } = $props()

  let overall = $derived(Math.round(offer?.overall ?? 0))
  let citizenship = $derived(
    Array.isArray(offer?.citizenship) ? offer.citizenship.join(', ') : offer?.citizenship,
  )
  let note = $derived.by(() => {
    if (!offer) return ''
    const deadline = offer.expires_at ? ` Ответьте до ${formatDate(offer.expires_at)}` : ''
    const intro = offer.unread
      ? `Новое предложение от ${offer.club_name}.`
      : offer.message || `Предложение от ${offer.club_name}.`
    return `${intro}${deadline}`
  })
</script>

<aside class="tf-received-detail" aria-label="Предложения трансферов">
  <header class="tf-offer-detail-title">Предложения трансферов</header>

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
      <i>!</i>
      <p>{note}</p>
    </div>

    <div class="tf-offer-detail-table">
      <span class="tf-offer-detail-th">От</span>
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
        <i>!</i>
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
      <div>
        <span>Действует до</span>
        <b>{formatDate(offer.expires_at)}</b>
      </div>
    </div>
  {:else}
    <p class="tf-offer-detail-empty">Выберите предложение в списке.</p>
  {/if}
</aside>
