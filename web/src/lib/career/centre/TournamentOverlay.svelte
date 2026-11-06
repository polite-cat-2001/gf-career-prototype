<script>
  import AppShell from '../../ui/AppShell.svelte'
  import StandingsTable from '../shared/StandingsTable.svelte'
  import { OVERVIEW_SECTIONS } from '../utils/tournaments.js'

  let { tournament, tournaments = [], index = 0, clubId, section = 'table' } = $props()

  const current = $derived(
    OVERVIEW_SECTIONS.find((item) => item.id === section) ?? OVERVIEW_SECTIONS[0],
  )
  const title = $derived(
    section === 'table' && tournament?.kind === 'playoff' ? 'Раунд' : current.label,
  )

  let hints = $derived.by(() => {
    const list = []
    if (section === 'table') {
      list.push({ gamepad: ['L-stick'], keyboard: ['↑', '↓'], label: 'Прокрутка' })
    }
    if (tournaments.length > 1) {
      list.push({ gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Турниры' })
    }
    list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
    return list
  })
</script>

{#if tournament}
  <div class="overview-overlay">
    <AppShell fill {hints}>
      <section class="overview-card" aria-label={tournament.name}>
        <header class="overview-head">
          <div>
            <span class="overview-eyebrow">
              {tournament.name}{tournament.round ? ` · Тур ${tournament.round}` : ''}
            </span>
            {#if title !== 'Таблица'}
              <h2>{title}</h2>
            {/if}
          </div>
          {#if tournaments.length > 1}
            <span class="overview-count">{index + 1} / {tournaments.length}</span>
          {/if}
        </header>

        {#if section === 'table' && tournament.standings?.length}
          <StandingsTable standings={tournament.standings} {clubId} />
        {:else if section === 'table'}
          <div class="overview-round">
            <strong>Раунд турнира</strong>
            <span>Сетка плей-офф появится здесь.</span>
          </div>
        {:else}
          <div class="overview-round">
            <span>Скоро</span>
          </div>
        {/if}
      </section>
    </AppShell>
  </div>
{/if}
