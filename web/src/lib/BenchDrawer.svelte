<script>
  import BenchPlayerCard from './BenchPlayerCard.svelte'

  let {
    bench = [],
    reserve = [],
    open = false,
    selectedId = null,
    onfocus = undefined,
    onactivate = undefined,
    onleave = undefined,
  } = $props()

  function handleFocusOut(event) {
    if (!event.currentTarget.contains(event.relatedTarget)) onleave?.()
  }
</script>

<aside
  class="bench-drawer"
  class:is-open={open}
  aria-label="Запасные"
  onfocusout={handleFocusOut}
>
  <div class="bench-drawer-scroll scroll-area" data-nav-grid>
    <div class="bench-drawer-section">Запас · {bench.length}</div>
    <div class="bench-grid">
      {#each bench as player (player.id)}
        <BenchPlayerCard
          {player}
          selected={selectedId === player.id}
          onfocus={() => onfocus?.(player)}
          onclick={() => onactivate?.(player)}
        />
      {/each}
    </div>

    {#if reserve.length}
      <div class="bench-drawer-section is-reserve">Резервные игроки · {reserve.length}</div>
      <div class="bench-grid">
        {#each reserve as player (player.id)}
          <BenchPlayerCard
            {player}
            selected={selectedId === player.id}
            onfocus={() => onfocus?.(player)}
            onclick={() => onactivate?.(player)}
          />
        {/each}
      </div>
    {/if}
  </div>
</aside>
