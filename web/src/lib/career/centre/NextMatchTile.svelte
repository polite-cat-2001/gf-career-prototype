<script>
  import Icon from '../../Icon.svelte'
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

{#if isMatchDay && nextMatch && !simulating && !advancing}
  <div class="match-actions" style="grid-area: next">
    <button class="match-action" data-nav data-autofocus onclick={onPlay}>
      <div class="match-action-head">
        <div>
          <span class="eyebrow">Матч</span>
          <strong class="match-action-title">Играть</strong>
        </div>
        <img
          class="match-action-crest"
          src={nextMatch.opponent.logo}
          alt=""
          onerror={hideBrokenImage}
        />
      </div>
      <span class="match-action-meta">
        Тур {nextMatch.round} · {shortDate(nextMatch.date)} · {nextMatch.home ? 'Дома' : 'В гостях'}
      </span>
      <div class="match-action-foot">
        <span>vs {nextMatch.opponent.name}</span>
        <span>{career.club.league_name}</span>
      </div>
    </button>

    <button class="match-action" data-nav onclick={onOpenSimulation}>
      <div class="match-action-head">
        <div>
          <span class="eyebrow">Матч</span>
          <strong class="match-action-title">Симуляция</strong>
        </div>
        <Icon name="clock" size={34} />
      </div>
      <span class="match-action-meta">
        Тур {nextMatch.round} · {shortDate(nextMatch.date)} · {nextMatch.home ? 'Дома' : 'В гостях'}
      </span>
      <div class="match-action-foot">
        <span>vs {nextMatch.opponent.name}</span>
        <span>{career.club.league_name}</span>
      </div>
    </button>
  </div>
{:else}
  <button
    class="widget widget-next"
    class:is-simulating={simulating}
    style="grid-area: next"
    data-nav
    data-autofocus
    onclick={onNext}
  >
    <div class="widget-head calendar-head">
      <strong class="widget-title calendar-title" class:is-season={season.complete}>
        {simulating ? 'Остановить' : season.complete ? 'Перейти в следующий сезон' : 'Далее'}
      </strong>
      <span class="calendar-month">{shortMonthLabel(displayDate)}</span>
    </div>

    <div class="day-window">
      <div
        class="day-track"
        class:is-sliding={simulating}
        style={`width:${trackWidth}%; --cells:${trackDays.length}; --shift:${trackShift}%`}
      >
        {#each trackDays as day (day.key)}
          <div
            class="day"
            class:today={day.key === displayDate}
            class:is-match={nextMatch && day.key === nextMatch.date}
          >
            <span class="day-week">{day.weekday}</span>
            <span class="day-num">{day.day}</span>
            {#if nextMatch && day.key === nextMatch.date}
              <img
                class="day-crest"
                src={nextMatch.opponent.logo}
                alt=""
                onerror={hideBrokenImage}
              />
            {/if}
          </div>
        {/each}
      </div>
    </div>

    {#if nextMatch}
      {@const homeTeam = nextMatch.home ? career.club : nextMatch.opponent}
      {@const awayTeam = nextMatch.home ? nextMatch.opponent : career.club}
      <div class="next-fixture">
        <div class="fixture-side">
          <img class="fixture-crest" src={homeTeam.logo} alt="" onerror={hideBrokenImage} />
          <span class="fixture-name">{homeTeam.name}</span>
        </div>
        <span class="fixture-vs">VS</span>
        <div class="fixture-side is-away">
          <span class="fixture-name">{awayTeam.name}</span>
          <img class="fixture-crest" src={awayTeam.logo} alt="" onerror={hideBrokenImage} />
        </div>
      </div>
      <div class="calendar-foot">
        <span class="next-meta">
          {seasonLabel(displayDate)} · {competitionLabel(career.club.league_name)} · Тур
          {nextMatch.round} · {nextMatch.home ? 'Дома' : 'В гостях'}
        </span>
        {#if season.form.length}
          <div class="form-pills">
            {#each season.form as item (item.fixture_id)}
              <span
                class="form-pill"
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
      <div class="season-final">
        <span class="season-final-title">Сезон завершён</span>
        {#if ownRow}
          <span>
            {ownRow.position}-е место · {ownRow.points}
            {plural(ownRow.points, 'очко', 'очка', 'очков')} · {ownRow.played}
            {plural(ownRow.played, 'матч', 'матча', 'матчей')}
          </span>
        {/if}
      </div>
      <div class="widget-action-bar season-cta">
        <span>Перейти в следующий сезон</span>
        <span>A</span>
      </div>
    {/if}
  </button>
{/if}
