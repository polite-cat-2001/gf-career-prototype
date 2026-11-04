<script>
  import { tick } from 'svelte'
  import { formatDate, hideBrokenImage } from './format.js'

  let { step = 'results', matchday, clubId } = $props()

  let tableWrap = $state(null)

  $effect(() => {
    if (step !== 'table' || !tableWrap) return
    const wrap = tableWrap
    tick().then(() => {
      if (!wrap.isConnected) return
      const row = wrap.querySelector('tr.is-own')
      if (!row) return
      const wrapRect = wrap.getBoundingClientRect()
      const rowRect = row.getBoundingClientRect()
      const header = wrap.querySelector('thead')?.getBoundingClientRect().height ?? 0
      const visibleTop = wrapRect.top + header
      if (rowRect.top >= visibleTop && rowRect.bottom <= wrapRect.bottom) return
      const max = wrap.scrollHeight - wrap.clientHeight
      const offset = rowRect.top - visibleTop - (wrap.clientHeight - header - rowRect.height) / 2
      wrap.scrollTop = Math.max(0, Math.min(wrap.scrollTop + offset, max))
    })
  })

  function deltaLabel(row) {
    if (row.delta > 0) return `Поднялся на ${row.position}-е место`
    if (row.delta < 0) return `Опустился на ${row.position}-е место`
    return 'Позиция не изменилась'
  }

  function difference(value) {
    return value > 0 ? `+${value}` : `${value}`
  }
</script>

{#if matchday}
  <div class="matchday-page">
    <section class="matchday-card" aria-label={step === 'results' ? 'Результаты дня' : 'Таблица'}>
      <header class="matchday-head">
        <div>
          <span class="matchday-eyebrow">
            {matchday.competition || 'Турнир'} · Тур {matchday.round} · {formatDate(matchday.date)}
          </span>
          <h2>{step === 'results' ? 'Результаты дня' : 'Таблица'}</h2>
        </div>
        <span class="matchday-step">{step === 'results' ? '1 / 2' : '2 / 2'}</span>
      </header>

      {#if step === 'results'}
        <div class="matchday-results">
          {#each matchday.results as result (result.fixture_id)}
            <div class="matchday-result" class:is-own={result.own}>
              <div class="matchday-club is-home">
                <img src={result.home.logo} alt="" onerror={hideBrokenImage} />
                <span>{result.home.name}</span>
              </div>
              <strong class="matchday-score">{result.score.home} : {result.score.away}</strong>
              <div class="matchday-club is-away">
                <span>{result.away.name}</span>
                <img src={result.away.logo} alt="" onerror={hideBrokenImage} />
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="matchday-table-wrap" bind:this={tableWrap}>
          <table class="matchday-table">
            <thead>
              <tr>
                <th class="is-pos">#</th>
                <th class="is-delta"></th>
                <th class="is-club">Клуб</th>
                <th>И</th>
                <th>В</th>
                <th>Н</th>
                <th>П</th>
                <th>ГЗ</th>
                <th>ГП</th>
                <th>РГ</th>
                <th class="is-points">О</th>
              </tr>
            </thead>
            <tbody>
              {#each matchday.standings as row (row.club_id)}
                <tr class:is-own={row.club_id === clubId}>
                  <td class="is-pos">{row.position}</td>
                  <td class="is-delta">
                    {#if row.delta > 0}
                      <span class="position-delta up" title={deltaLabel(row)}>↑</span>
                    {:else if row.delta < 0}
                      <span class="position-delta down" title={deltaLabel(row)}>↓</span>
                    {:else}
                      <span class="position-delta same" title={deltaLabel(row)}>—</span>
                    {/if}
                  </td>
                  <td class="is-club">
                    <img src={row.club_logo} alt="" onerror={hideBrokenImage} />
                    <span>{row.club_name}</span>
                  </td>
                  <td>{row.played}</td>
                  <td>{row.won}</td>
                  <td>{row.drawn}</td>
                  <td>{row.lost}</td>
                  <td>{row.goals_for}</td>
                  <td>{row.goals_against}</td>
                  <td>{difference(row.goal_difference)}</td>
                  <td class="is-points">{row.points}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </section>
  </div>
{/if}
