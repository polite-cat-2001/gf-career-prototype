<script>
  import ScoutCard from './ScoutCard.svelte'

  let { scouts, emptySlots, selectedId, statusFor, onFocus, onOpen, onHire } = $props()
</script>

<section class="sc-grid" aria-label="Скауты">
  {#each scouts as scout, index (scout.id)}
    <ScoutCard
      {scout}
      status={statusFor(scout)}
      selected={selectedId === scout.id}
      autofocus={index === 0}
      onFocus={() => onFocus(scout.id)}
      onOpen={() => onOpen(scout)}
    />
  {/each}
  {#each Array(emptySlots) as _, index (index)}
    <button class="sc-tile is-empty" data-nav onclick={onHire}>
      <span class="sc-tile-empty">Нанять скаута</span>
    </button>
  {/each}
</section>
