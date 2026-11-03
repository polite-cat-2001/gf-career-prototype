<script>
  let { rows, clubId, round } = $props()
</script>

<section class="widget widget-table" style="grid-area: table">
  <div class="widget-head">
    <strong class="widget-title widget-title-sm">Таблицы</strong>
    <span class="soon-tag">{round ? `Тур ${round}` : 'Старт'}</span>
  </div>
  <div class="mini-table">
    <div class="mini-row mini-head">
      <span>#</span>
      <span>Клуб</span>
      <span>И</span>
      <span>Р</span>
      <span>О</span>
    </div>
    {#each rows as row (row.club_id)}
      {#if row.gapBefore}
        <div class="mini-gap" aria-hidden="true">⋯</div>
      {/if}
      <div class="mini-row" class:is-club={row.club_id === clubId}>
        <span class="mini-pos">{row.position}</span>
        <span class="mini-name">{row.club_name}</span>
        <span>{row.played}</span>
        <span>{row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}</span>
        <span class="mini-pts">{row.points}</span>
      </div>
    {/each}
  </div>
</section>
