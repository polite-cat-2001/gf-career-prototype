<script>
  import { onMount } from 'svelte'

  let { rows = [], standings = [], clubId, round } = $props()

  let tall = $state(false)

  onMount(() => {
    const query = window.matchMedia('(min-width: 1500px) and (min-height: 900px)')
    const sync = () => {
      tall = query.matches
    }
    sync()
    query.addEventListener('change', sync)
    return () => query.removeEventListener('change', sync)
  })

  const limit = $derived(tall ? 8 : 6)

  const displayRows = $derived.by(() => {
    const list = standings.length ? standings : rows
    if (!list.length) return []
    const top = list.slice(0, limit)
    if (clubId == null || top.some((row) => row.club_id === clubId)) return top
    const own = list.find((row) => row.club_id === clubId)
    if (!own) return top
    return [...top.slice(0, limit - 1), { ...own, gapBefore: true }]
  })
</script>

<section class="gf-tile home-tile home-table">
  <div class="home-table__head">
    <h2 class="gf-tile__title home-table__title">Таблица</h2>
    <span class="home-table__round">{round ? `Тур ${round}` : 'Старт'}</span>
  </div>
  <div class="home-table__rows">
    <div class="home-table__row is-head">
      <span>#</span>
      <span>Клуб</span>
      <span>И</span>
      <span>Р</span>
      <span>О</span>
    </div>
    {#each displayRows as row (row.club_id)}
      {#if row.gapBefore}
        <div class="home-table__gap" aria-hidden="true">⋯</div>
      {/if}
      <div class="home-table__row" class:is-club={row.club_id === clubId}>
        <span class="home-table__pos">{row.position}</span>
        <span class="home-table__name">{row.club_name}</span>
        <span>{row.played}</span>
        <span>{row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}</span>
        <span class="home-table__pts">{row.points}</span>
      </div>
    {/each}
  </div>
</section>
