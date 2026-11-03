<script>
  import CentreProfile from '../shared/CentreProfile.svelte'

  let { player, totals, competitions } = $props()
</script>

<aside class="centre-panel scroll-area" aria-label="Статистика игрока">
  <CentreProfile {player} eyebrow={'Статистика игрока'} />

  <section class="centre-block">
    <div class="centre-block-head">Итого в сезоне</div>
    <div class="centre-total-grid">
      {#each [
        ['Игры', totals.apps ?? 0],
        ['Голы', totals.goals ?? 0],
        ['Ассисты', totals.assists ?? 0],
        ['Минуты', totals.minutes ?? 0],
      ] as [label, value] (label)}
        <div class="centre-total">
          <strong>{value}</strong>
          <span>{label}</span>
        </div>
      {/each}
    </div>
  </section>

  <section class="centre-block">
    <div class="centre-block-head">По турнирам</div>
    {#if competitions.length}
      {#each competitions as competition (competition.id)}
        <div class="competition-card">
          <div class="competition-head">
            <strong>{competition.name}</strong>
            <span>{competition.apps} И · {competition.minutes} мин</span>
          </div>
          <div class="competition-metrics">
            <span><strong>{competition.goals}</strong> голы</span>
            <span><strong>{competition.assists}</strong> ассисты</span>
            <span><strong>{competition.yellow}</strong> ЖК</span>
            <span><strong>{competition.red}</strong> КК</span>
            {#if player.role === 'GK'}
              <span class="is-clean">
                <strong>{competition.clean_sheets}</strong> сухие
              </span>
            {/if}
          </div>
        </div>
      {/each}
    {:else}
      <p class="centre-note">Статистика появится после первых матчей.</p>
    {/if}
  </section>
</aside>
