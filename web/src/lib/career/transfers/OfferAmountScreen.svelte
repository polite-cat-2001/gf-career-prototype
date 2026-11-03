<script>
  let { label, groups, index, places, finish, hint = null } = $props()
</script>

<div class="amount-screen">
  <span class="eyebrow">{label}</span>
  <button
    class="amount-value"
    data-nav
    data-amount
    data-cycle="amount"
    data-autofocus
    aria-label="Сумма"
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
  {#if hint}
    <span class="amount-hint">{hint}</span>
  {/if}
</div>
