<script>
  import { formatDate, hideBrokenImage } from './format.js'
  import StandingsTable from './career/shared/StandingsTable.svelte'

  let { step = 'results', matchday, clubId } = $props()
</script>

{#if matchday}
  <div class="matchday-page">
    <section class="matchday-card" aria-label={step === 'results' ? 'Результаты дня' : 'Таблица'}>
      <header class="matchday-head">
        <div>
          <span class="matchday-eyebrow">
            {matchday.competition || 'Турнир'} · Тур {matchday.round} · {formatDate(matchday.date)}
          </span>
          {#if step === 'results'}
            <h2>Результаты дня</h2>
          {/if}
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
        <StandingsTable standings={matchday.standings} {clubId} showDelta />
      {/if}
    </section>
  </div>
{/if}
