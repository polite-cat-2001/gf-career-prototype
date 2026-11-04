<script>
  import AppShell from '../../ui/AppShell.svelte'
  import Row from '../../ui/Row.svelte'
  import { hideBrokenImage, plural } from '../../format.js'
  import { nextSeasonLabel } from '../utils/dates.js'

  let { review, season, reviewStep, ownRow, career, onAdvance, onStartNewSeason } = $props()

  let hints = $derived(
    reviewStep === 0
      ? [
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Далее' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Закрыть' },
        ]
      : [
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Начать новый сезон' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'К таблице' },
        ],
  )

  let note = $derived(reviewStep === 0 ? 'Итоги сезона' : 'Новый сезон')
</script>

<div class="match-overlay season-review">
  <AppShell fill {hints} {note}>
    <section class="review-card" aria-label="Итоги сезона">
      <header class="review-head">
        <span class="review-eyebrow">
          {reviewStep === 0 ? `Итоги сезона · ${season.season_start.slice(0, 4)}` : 'Новый сезон'}
        </span>
        <div class="review-title-row">
          <h2>{reviewStep === 0 ? review.league.name : review.next.league.name}</h2>
          {#if reviewStep === 0 && ownRow}
            <span class="review-place">
              {ownRow.position}-е место · {ownRow.points}
              {plural(ownRow.points, 'очко', 'очка', 'очков')}
            </span>
          {:else if reviewStep === 1}
            <span class="review-place">{nextSeasonLabel(season.season_start)}</span>
          {/if}
        </div>
      </header>

      {#if reviewStep === 0}
        <div class="review-table-wrap">
          <div class="review-table">
            <div class="review-row review-row-head">
              <span>#</span>
              <span>Клуб</span>
              <span>И</span>
              <span>+/-</span>
              <span>О</span>
            </div>
            {#each review.standings as row (row.club_id)}
              <div
                class="review-row"
                class:is-club={row.club_id === career.club.id}
                class:is-up={review.promoted.some((club) => club.id === row.club_id)}
                class:is-down={review.relegated.some((club) => club.id === row.club_id)}
              >
                <span class="review-pos">{row.position}</span>
                <span class="review-club">
                  <img src={row.club_logo} alt="" onerror={hideBrokenImage} />
                  <span>{row.club_name}</span>
                </span>
                <span>{row.played}</span>
                <span>{row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}</span>
                <span class="review-points">{row.points}</span>
              </div>
            {/each}
          </div>
        </div>

        <div class="review-zones">
          {#if review.promoted.length}
            <div class="review-zone is-up">
              <span class="review-zone-label">Поднялись в {review.promoted_to.name}</span>
              <div class="review-chips">
                {#each review.promoted as club (club.id)}
                  <span class="review-chip">
                    <img src={club.logo} alt="" onerror={hideBrokenImage} />
                    {club.name}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
          {#if review.relegated.length}
            <div class="review-zone is-down">
              <span class="review-zone-label">Вылетели в {review.relegated_to.name}</span>
              <div class="review-chips">
                {#each review.relegated as club (club.id)}
                  <span class="review-chip">
                    <img src={club.logo} alt="" onerror={hideBrokenImage} />
                    {club.name}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
        </div>

        <Row title="Далее" meta="A" autofocus onclick={onAdvance} />
      {:else}
        <div
          class="review-transition"
          class:is-up={review.movement === 'up'}
          class:is-down={review.movement === 'down'}
          class:is-stay={review.movement === null}
        >
          <span class="review-move-arrow">
            {review.movement === 'up' ? '↑' : review.movement === 'down' ? '↓' : '→'}
          </span>
          <img class="review-move-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
          <div class="review-move-copy">
            <strong>{career.club.name}</strong>
            <span>
              {review.movement === 'up'
                ? 'Повышение в'
                : review.movement === 'down'
                  ? 'Вылет в'
                  : 'Остались в'}
              {review.next.league.name}
            </span>
          </div>
        </div>

        <div class="review-next-grid">
          {#if review.next.from_above.length}
            <div class="review-next-col">
              <span class="review-next-label">Пришли из {review.next.above.name}</span>
              {#each review.next.from_above as item (item.club.id)}
                <div class="review-next-row">
                  <img src={item.club.logo} alt="" onerror={hideBrokenImage} />
                  <span>{item.club.name}</span>
                  <small>{item.league.name}</small>
                </div>
              {/each}
            </div>
          {/if}
          {#if review.next.from_below.length}
            <div class="review-next-col">
              <span class="review-next-label">Пришли из {review.next.below.name}</span>
              {#each review.next.from_below as item (item.club.id)}
                <div class="review-next-row">
                  <img src={item.club.logo} alt="" onerror={hideBrokenImage} />
                  <span>{item.club.name}</span>
                  <small>{item.league.name}</small>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <Row
          title="Начать новый сезон"
          meta="A"
          autofocus
          onclick={onStartNewSeason}
        />
      {/if}
    </section>
  </AppShell>
</div>
