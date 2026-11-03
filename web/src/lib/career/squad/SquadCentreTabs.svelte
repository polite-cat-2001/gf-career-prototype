<script>
  let { tabs, active, onSelect } = $props()
</script>

<nav class="centre-tabs" aria-label="Центр составов">
  {#each tabs as item (item.id)}
    <button
      class="centre-tab"
      class:active={active === item.id}
      data-nav
      onclick={() => onSelect(item.id)}
    >
      {item.label}
    </button>
  {/each}
</nav>
