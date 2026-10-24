<script>
  let { tabs = [], active = '', onselect } = $props()
</script>

<nav class="hub-tabs" aria-label="Разделы карьеры">
  <div class="tabs-list">
    {#each tabs as tab}
      <button
        class="hub-tab"
        class:active={tab.id === active}
        disabled={tab.disabled}
        tabindex="-1"
        onclick={() => !tab.disabled && onselect(tab.id)}
      >
        {tab.label}
        {#if tab.disabled}<span class="tab-soon">скоро</span>{/if}
      </button>
    {/each}
  </div>
</nav>
