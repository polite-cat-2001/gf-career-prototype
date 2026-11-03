<script>
  import { formatValue } from '../../format.js'

  let { playerName, offer, groups, index, places, finish } = $props()
</script>

<div class="amount-screen">
  <span class="eyebrow">Контрпредложение · {playerName ?? ''}</span>
  <button
    class="amount-value"
    data-nav
    data-amount
    data-cycle="amount"
    data-autofocus
    aria-label="Сумма контрпредложения"
    onclick={finish}
  >
    {#each groups as group, groupIndex (groupIndex)}
      <span class="amount-group">
        {#each group.digits as digit, digitIndex (digitIndex)}
          <span class="amount-digit" class:is-selected={group.start + digitIndex === index}>
            {digit}
          </span>
        {/each}
      </span>
    {/each}
  </button>
  <span class="amount-place">Разряд: {places[index]}</span>
  <span class="amount-hint">Предложение клуба: {formatValue(offer.amount)}</span>
</div>
