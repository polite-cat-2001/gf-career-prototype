<script>
  import EventGlyph from './EventGlyph.svelte'
  import { formatDate, hideBrokenImage } from './format.js'

  let {
    phase = 'setup',
    minute = 0,
    setup,
    simulation = null,
    loading = false,
    error = '',
  } = $props()

  let data = $derived(simulation ?? setup)
  let events = $derived(simulation?.events ?? [])
  let visibleEvents = $derived(
    events
      .filter((event) => event.minute <= minute)
      .sort((a, b) => b.minute - a.minute || b.id.localeCompare(a.id)),
  )
  let score = $derived.by(() => {
    const result = { home: 0, away: 0 }
    for (const event of visibleEvents) {
      if (event.type === 'goal' || event.type === 'penalty') result[event.team] += 1
    }
    return result
  })
  let scoreLabel = $derived(phase === 'setup' ? 'VS' : `${score.home} : ${score.away}`)
  let minuteLabel = $derived(
    phase === 'setup' ? 'Матч не начат' : phase === 'done' ? '90 мин.' : `${minute} мин.`,
  )
  let clockLabel = $derived(phase === 'setup' ? 'Матч не начат' : `${minute} мин.`)

  function displayName(player) {
    return player?.last_name || player?.name || '—'
  }

  function marksFor(playerId, side) {
    const marks = []
    for (const event of visibleEvents) {
      if (event.team !== side) continue
      if (event.type === 'sub') {
        if (event.player_out?.id === playerId) marks.push('sub-out')
        else if (event.player?.id === playerId) marks.push('sub-in')
        continue
      }
      if (event.player?.id === playerId) marks.push(event.type)
    }
    return [...new Set(marks)].slice(0, 4)
  }

  function glyphFor(event) {
    return event.type === 'sub' ? 'sub-in' : event.type
  }

  function eventText(event) {
    const player = displayName(event.player)
    if (event.type === 'sub') return `${player} → ${displayName(event.player_out)}`
    if (event.type === 'penalty') return `Пенальти · ${player}`
    if (event.type === 'injury') return `Травма · ${player}`
    return player
  }

  function teamFor(side) {
    return side === 'home' ? data?.home_team : data?.away_team
  }
</script>

{#if data}
  <div class="sim-page">
    <div class="sim-stage">
      <section class="sim-main" aria-label="Матч">
        <div class="sim-board">
          <div class="sim-board__top">
            <span class="sim-competition">{data.competition} · Тур {data.round}</span>
            <span class="sim-date">{formatDate(data.date)}</span>
          </div>

          <div class="sim-scoreline">
            <div class="sim-club is-home">
              <img src={data.home_team.logo} alt="" onerror={hideBrokenImage} />
              <div class="sim-club__text">
                <strong>{data.home_team.name}</strong>
                {#if data.home}<span class="sim-club__tag">Ваша команда</span>{/if}
              </div>
            </div>

            <div class="sim-centre">
              {#key scoreLabel}
                <strong class="sim-score">{scoreLabel}</strong>
              {/key}
              <span class="sim-minute">{minuteLabel}</span>
            </div>

            <div class="sim-club is-away">
              <div class="sim-club__text">
                <strong>{data.away_team.name}</strong>
                {#if !data.home}<span class="sim-club__tag">Ваша команда</span>{/if}
              </div>
              <img src={data.away_team.logo} alt="" onerror={hideBrokenImage} />
            </div>
          </div>
        </div>

        <div class="sim-lineups">
          {#each [['home', data.home_team, data.home_lineup], ['away', data.away_team, data.away_lineup]] as [side, team, lineup] (side)}
            <div class="sim-team" class:is-away={side === 'away'}>
              <div class="sim-list-head">
                <span class="sim-list-team">{team.name}</span>
                <strong class="sim-list-formation">{lineup.formation}</strong>
              </div>
              <div class="sim-players">
                {#each lineup.slots as slot (slot.player.id)}
                  <div class="sim-player">
                    {#if side === 'away'}
                      <span class="sim-marks">
                        {#each marksFor(slot.player.id, side) as mark (mark)}
                          <EventGlyph type={mark} size={14} />
                        {/each}
                      </span>
                    {/if}
                    <span class="sim-name">{displayName(slot.player)}</span>
                    {#if side === 'home'}
                      <span class="sim-marks">
                        {#each marksFor(slot.player.id, side) as mark (mark)}
                          <EventGlyph type={mark} size={14} />
                        {/each}
                      </span>
                    {/if}
                  </div>
                {/each}
                {#if lineup.bench.length}
                  <div class="sim-bench-label">Запасные</div>
                  {#each lineup.bench as player (player.id)}
                    <div class="sim-player is-bench">
                      {#if side === 'away'}
                        <span class="sim-marks">
                          {#each marksFor(player.id, side) as mark (mark)}
                            <EventGlyph type={mark} size={14} />
                          {/each}
                        </span>
                      {/if}
                      <span class="sim-name">{displayName(player)}</span>
                      {#if side === 'home'}
                        <span class="sim-marks">
                          {#each marksFor(player.id, side) as mark (mark)}
                            <EventGlyph type={mark} size={14} />
                          {/each}
                        </span>
                      {/if}
                    </div>
                  {/each}
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </section>

      <aside class="sim-side" aria-label="Ход матча">
        <div
          class="sim-clock"
          class:is-setup={phase === 'setup'}
          class:is-live={phase === 'live'}
          class:is-done={phase === 'done'}
        >
          {#if phase !== 'setup'}
            <span class="sim-clock__label">{phase === 'live' ? 'Идёт матч' : 'Финал'}</span>
          {/if}
          {#key clockLabel}
            <strong class="sim-clock__value">{clockLabel}</strong>
          {/key}
        </div>

        <div class="sim-feed-head">
          <span>Лента матча</span>
          <span>{visibleEvents.length}</span>
        </div>

        <div class="sim-feed">
          {#if phase === 'setup'}
            <div class="sim-setup">
              <span class="sim-setup__eyebrow">Перед матчем</span>
              <div class="sim-setup__rows">
                <div class="sim-setup__row">
                  <span>Турнир</span>
                  <strong>{data.competition}</strong>
                </div>
                <div class="sim-setup__row">
                  <span>Тур</span>
                  <strong>{data.round}</strong>
                </div>
                <div class="sim-setup__row">
                  <span>Схемы</span>
                  <strong>{data.home_lineup.formation} · {data.away_lineup.formation}</strong>
                </div>
                <div class="sim-setup__row">
                  <span>Матч</span>
                  <strong>{data.home ? 'Дома' : 'В гостях'}</strong>
                </div>
              </div>
              <span class="sim-setup__hint">События появятся после старта</span>
            </div>
          {:else if visibleEvents.length}
            {#each visibleEvents as event (event.id)}
              <div class="sim-feed-row is-{event.type}">
                <span class="sim-feed-minute">{event.minute}′</span>
                <EventGlyph type={glyphFor(event)} size={16} />
                <span class="sim-feed-player">{eventText(event)}</span>
                <span class="sim-feed-club">{teamFor(event.team)?.abbr}</span>
              </div>
            {/each}
          {:else}
            <div class="sim-feed-empty">
              <span class="sim-feed-pulse"></span>
              <span>События появятся по ходу матча</span>
            </div>
          {/if}
        </div>

        {#if error}
          <div class="sim-message is-error">{error}</div>
        {/if}
        {#if loading}
          <div class="sim-message is-loading">Симуляция…</div>
        {/if}
      </aside>
    </div>
  </div>
{/if}
