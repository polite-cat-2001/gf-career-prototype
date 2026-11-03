<script>
  let { field, groups, index, places, onFinish } = $props()
</script>

<div class="amount-screen">
  <span class="eyebrow">{field === 'weekly_wage' ? 'Зарплата в неделю' : 'Отступные'}</span>
  <button
    class="amount-value"
    data-nav
    data-amount
    data-cycle="amount"
    data-autofocus
    aria-label="Сумма"
    onclick={onFinish}
  >
    {#each groups as group, groupIndex (groupIndex)}
      <span class="amount-group">
        {#each group.digits as digit, digitIndex (digitIndex)}
          <span
            class="amount-digit"
            class:is-selected={group.start + digitIndex === index}
          >
            {digit}
          </span>
        {/each}
      </span>
    {/each}
  </button>
  <span class="amount-place">Разряд: {places[index]}</span>
</div>
