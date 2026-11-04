<script>
  import Glyph from '../../ui/Glyph.svelte'
  import {
    competitionLabel,
    hideBrokenImage,
    plural,
    seasonLabel,
    shortDate,
    shortMonthLabel,
  } from '../../format.js'

  let {
    career,
    season,
    nextMatch,
    displayDate,
    trackDays,
    trackWidth,
    trackShift,
    isMatchDay,
    simulating,
    advancing,
    ownRow,
    onPlay,
    onOpenSimulation,
    onNext,
  } = $props()
</script>

{#snippet dayStrip()}
  <div
    class="home-days__track is-sliding"
    style={`width:${trackWidth}%; --cells:${trackDays.length}; --shift:${trackShift}%`}
  >
    {#each trackDays as day (day.key)}
      <div
        class="home-day"
        class:is-today={day.key === displayDate}
        class:is-match={nextMatch && day.key === nextMatch.date}
      >
        <span class="home-day__week">{day.weekday}</span>
        <span class="home-day__num">{day.day}</span>
        {#if nextMatch && day.key === nextMatch.date}
          <img
            class="home-day__crest"
            src={nextMatch.opponent.logo}
            alt=""
            onerror={hideBrokenImage}
          />
        {/if}
      </div>
    {/each}
  </div>
{/snippet}

{#if isMatchDay && nextMatch && !simulating && !advancing}
  <div class="home-actions">
    <button
      type="button"
      class="gf-tile home-tile home-action"
      data-nav
      data-autofocus
      onclick={onPlay}
    >
      <div class="home-action__head">
        <div class="home-action__text">
          <span class="home-eyebrow">Матч</span>
          <span class="gf-tile__title">Играть</span>
        </div>
        <img
          class="home-action__crest"
          src={nextMatch.opponent.logo}
          alt=""
          onerror={hideBrokenImage}
        />
      </div>
      <span class="home-action__meta">
        Тур {nextMatch.round} · {shortDate(nextMatch.date)} · {nextMatch.home ? 'Дома' : 'В гостях'}
      </span>
      <div class="home-action__foot">
        <span>vs {nextMatch.opponent.name}</span>
        <span>{career.club.league_name}</span>
      </div>
    </button>

    <button
      type="button"
      class="gf-tile home-tile home-action"
      data-nav
      onclick={onOpenSimulation}
    >
      <div class="home-action__head">
        <div class="home-action__text">
          <span class="home-eyebrow">Матч</span>
          <span class="gf-tile__title">Симуляция</span>
        </div>
        <span class="gf-tile__glyph home-action__glyph"><Glyph name="monitor" size={56} /></span>
      </div>
      <span class="home-action__meta">
        Тур {nextMatch.round} · {shortDate(nextMatch.date)} · {nextMatch.home ? 'Дома' : 'В гостях'}
      </span>
      <div class="home-action__foot">
        <span>vs {nextMatch.opponent.name}</span>
        <span>{career.club.league_name}</span>
      </div>
    </button>
  </div>
{:else}
  <button
    type="button"
    class="gf-tile gf-tile--hero home-tile home-next"
    data-nav
    data-autofocus
    onclick={onNext}
  >
    <div class="home-head">
      <div class="home-head__main">
        <span class="home-eyebrow">
          {simulating ? 'Симуляция' : season.complete ? 'Сезон' : 'Календарь'}
        </span>
        <span class="gf-tile__title">
          {simulating ? 'Остановить' : season.complete ? 'Перейти в следующий сезон' : 'Далее'}
        </span>
      </div>
      <span class="home-head__month">{shortMonthLabel(displayDate)}</span>
    </div>

    {#if nextMatch}
      {#if simulating}
        <div class="home-days">{@render dayStrip()}</div>
      {:else}
        {#key displayDate}
          <div class="home-days is-advancing">{@render dayStrip()}</div>
        {/key}
      {/if}
    {/if}

    {#if nextMatch}
      {@const homeTeam = nextMatch.home ? career.club : nextMatch.opponent}
      {@const awayTeam = nextMatch.home ? nextMatch.opponent : career.club}
      <div class="home-fixture">
        <div class="home-fixture__side">
          <img class="home-fixture__crest" src={homeTeam.logo} alt="" onerror={hideBrokenImage} />
          <span class="home-fixture__name">{homeTeam.name}</span>
        </div>
        <span class="home-fixture__vs">VS</span>
        <div class="home-fixture__side is-away">
          <span class="home-fixture__name">{awayTeam.name}</span>
          <img class="home-fixture__crest" src={awayTeam.logo} alt="" onerror={hideBrokenImage} />
        </div>
      </div>
      <div class="home-foot">
        <span class="home-foot__meta">
          {seasonLabel(displayDate)} · {competitionLabel(career.club.league_name)} · Тур
          {nextMatch.round} · {nextMatch.home ? 'Дома' : 'В гостях'}
        </span>
        {#if season.form.length}
          <div class="home-form">
            {#each season.form as item (item.fixture_id)}
              <span
                class="home-form__pill"
                class:is-win={item.outcome === 'W'}
                class:is-draw={item.outcome === 'D'}
                class:is-loss={item.outcome === 'L'}
                title={`${item.opponent.name} ${item.goals_for}:${item.goals_against}`}
              >
                {item.outcome === 'W' ? 'В' : item.outcome === 'D' ? 'Н' : 'П'}
              </span>
            {/each}
          </div>
        {/if}
      </div>
    {:else}
      <div class="home-season">
        <span class="home-season__title">Сезон завершён</span>
        {#if ownRow}
          <span class="home-season__meta">
            {ownRow.position}-е место · {ownRow.points}
            {plural(ownRow.points, 'очко', 'очка', 'очков')} · {ownRow.played}
            {plural(ownRow.played, 'матч', 'матча', 'матчей')}
          </span>
        {/if}
      </div>
      <div class="home-cta">
        <span>Перейти в следующий сезон</span>
        <span>A</span>
      </div>
    {/if}
  </button>
{/if}
