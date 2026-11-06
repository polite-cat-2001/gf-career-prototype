<script>
  import { onMount } from 'svelte'

  import { hideBrokenImage } from '../../format.js'
  import { OVERVIEW_SECTIONS, tableWindow } from '../utils/tournaments.js'

  let {
    tournament = null,
    section = 'table',
    clubId,
    onopen,
    onselectsection,
    onfocus,
    onblur,
  } = $props()

  let tall = $state(false)

  onMount(() => {
    const query = window.matchMedia('(min-height: 1200px)')
    const sync = () => {
      tall = query.matches
    }
    sync()
    query.addEventListener('change', sync)
    return () => query.removeEventListener('change', sync)
  })

  const limit = $derived(tall ? 8 : 6)
  const current = $derived(
    OVERVIEW_SECTIONS.find((item) => item.id === section) ?? OVERVIEW_SECTIONS[0],
  )
  const currentIndex = $derived(
    Math.max(0, OVERVIEW_SECTIONS.findIndex((item) => item.id === section)),
  )
  const title = $derived(
    section === 'table' && tournament?.kind === 'playoff' ? 'Раунд' : current.label,
  )
  const rows = $derived(
    tournament?.standings?.length
      ? tableWindow(tournament.standings, clubId, limit)
      : [],
  )
</script>

<div
  class="gf-tile home-tile home-table"
  role="button"
  tabindex="0"
  data-nav
  data-overview
  onclick={onopen}
  {onfocus}
  {onblur}
>
  <div class="home-table__head">
    <div class="home-table__titles">
      <h2 class="gf-tile__title home-table__title">{title}</h2>
      {#if tournament}
        <span class="home-table__competition">{tournament.name}</span>
      {/if}
    </div>
    {#if tournament?.round}
      <span class="home-table__round">Тур {tournament.round}</span>
    {/if}
  </div>

  {#if section === 'table' && rows.length}
    <div class="home-table__board">
      <div class="home-table__row is-head">
        <span>#</span>
        <span></span>
        <span>Клуб</span>
        <span>И</span>
        <span>О</span>
      </div>
      {#each rows as row (row.club_id)}
        <div class="home-table__row" class:is-club={row.club_id === clubId}>
          <span class="home-table__pos">{row.position}</span>
          <img
            class="home-table__crest"
            src={row.club_logo}
            alt=""
            onerror={hideBrokenImage}
          />
          <span class="home-table__name">{row.club_name}</span>
          <span>{row.played}</span>
          <span class="home-table__pts">{row.points}</span>
        </div>
      {/each}
    </div>
  {:else if section === 'table'}
    <div class="home-table__empty">Нет данных турнира</div>
  {:else}
    <div class="home-table__placeholder">
      <span>Скоро</span>
    </div>
  {/if}

  <span class="home-table__dots">
    {#each OVERVIEW_SECTIONS as item, index (item.id)}
      <button
        type="button"
        class="home-table__dot"
        class:is-active={index === currentIndex}
        tabindex="-1"
        aria-label={item.label}
        title={item.label}
        onclick={(event) => {
          event.stopPropagation()
          onselectsection?.(item.id)
        }}
      >
        <span></span>
      </button>
    {/each}
  </span>
</div>
