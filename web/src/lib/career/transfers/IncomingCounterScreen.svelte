<script>
  import { formatValue } from '../../format.js'

  let { playerName, offer, groups, index, places, finish } = $props()
</script>

<div class="gf-amount">
  <div class="gf-amount__card">
    <span class="gf-amount__label">Контрпредложение · {playerName ?? ''}</span>
    <button
      class="gf-amount__value"
      data-nav
      data-amount
      data-cycle="amount"
      data-autofocus
      aria-label="Сумма контрпредложения"
      onclick={finish}
    >
      {#each groups as group, groupIndex (groupIndex)}
        <span class="gf-amount__group">
          {#each group.digits as digit, digitIndex (digitIndex)}
            <span class="gf-amount__digit" class:is-selected={group.start + digitIndex === index}>
              {digit}
            </span>
          {/each}
        </span>
      {/each}
    </button>
    <span class="gf-amount__place">Разряд: {places[index]}</span>
    <span class="gf-amount__hint">Предложение клуба: {formatValue(offer.amount)}</span>
  </div>
</div>
