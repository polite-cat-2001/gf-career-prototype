<script>
  import BenchDrawer from '../../BenchDrawer.svelte'
  import { compareTone, hideBrokenImage, statTone } from '../../format.js'
  import PlayerBlock from '../shared/PlayerBlock.svelte'
  import RadarChart from '../shared/RadarChart.svelte'
  import PitchBoard from './PitchBoard.svelte'

  let {
    view,
    planTabs,
    comparing,
    anchorPlayer,
    focusedPlayer,
    lineup,
    radar,
    anchorRadar,
    detailsPage,
    detailPages,
    infoRows,
    seasonRows,
    detailGroups,
    anchorId,
    teamDisplay,
    teamDelta,
    career,
    benchFocused,
    onCardFocus,
    onCardEnter,
    onCardActivate,
    onBenchFocus,
    onBenchActivate,
    onBenchLeave,
  } = $props()
</script>

<div class="plan">
  <div class="plan-stage" class:has-drawer={view === 'plan'}>
    <nav class="plan-tabs" aria-label="План игры">
      {#each planTabs as item (item.label)}
        <span class="plan-tab" class:active={item.active}>{item.label}</span>
      {/each}
    </nav>

    {#if comparing}
      <div class="player-head compare-head">
        <PlayerBlock
          player={anchorPlayer}
          mirrored={false}
          {comparing}
          {anchorPlayer}
          {focusedPlayer}
          {lineup}
        />
        {#if radar.length && focusedPlayer.role !== 'GK'}
          <RadarChart
            values={anchorRadar.length ? anchorRadar : radar}
            secondary={anchorRadar.length ? radar : null}
          />
        {:else}
          <span class="radar-empty">Вратарский профиль не входит в канон</span>
        {/if}
        <PlayerBlock
          player={focusedPlayer}
          mirrored={true}
          {comparing}
          {anchorPlayer}
          {focusedPlayer}
          {lineup}
        />
      </div>
    {:else}
      <div class="player-head">
        <PlayerBlock
          player={focusedPlayer}
          mirrored={false}
          {comparing}
          {anchorPlayer}
          {focusedPlayer}
          {lineup}
        />
        {#if radar.length && focusedPlayer.role !== 'GK'}
          <RadarChart values={radar} />
        {:else}
          <span class="radar-empty">Вратарский профиль не входит в канон</span>
        {/if}
      </div>
    {/if}

    {#if view === 'details'}
      <section class="details-panel" data-nav tabindex="-1" aria-label="Подробности игрока">
        <strong class="details-title">{detailPages[detailsPage].label}</strong>

        {#if detailsPage === 0}
          <div class="details-list details-info">
            {#each infoRows as row (row.label)}
              <div class="details-row info-row" class:is-compare={comparing}>
                <span class="info-value">{row.left}</span>
                <span class="details-label">{row.label}</span>
                {#if comparing}
                  <span class="info-value right">{row.right}</span>
                {:else}
                  <span class="details-spacer"></span>
                {/if}
              </div>
            {/each}
          </div>
        {:else if detailsPage === 3}
          <div class="details-list details-info">
            {#each seasonRows as row (row.key)}
              <div class="details-row info-row" class:is-compare={comparing}>
                <span class="info-value">{row.left}</span>
                <span class="details-label">{row.label}</span>
                {#if comparing}
                  <span class="info-value right">{row.right}</span>
                {:else}
                  <span class="details-spacer"></span>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <div class="details-list">
            {#each detailGroups as group (group.id)}
              <div class="details-group">
                <span class="details-group-label">{group.label}</span>
                {#each group.rows as row (row.key)}
                  {@const right = comparing ? Math.round(focusedPlayer.stats[row.key] ?? 0) : null}
                  {@const left = comparing ? Math.round(anchorPlayer.stats[row.key] ?? 0) : row.value}
                  <div class="details-row" class:is-compare={comparing}>
                    <span class="details-value {comparing ? compareTone(left, right) : statTone(left)}">
                      {left}
                    </span>
                    <span class="details-label">{row.label}</span>
                    {#if comparing}
                      <span class="details-value {compareTone(right, left)}">{right}</span>
                    {:else}
                      <span class="details-spacer"></span>
                    {/if}
                  </div>
                {/each}
              </div>
            {/each}
          </div>
        {/if}

        <div class="details-dots" aria-hidden="true">
          {#each detailPages as page, index (page.id)}
            <i class:active={index === detailsPage}></i>
          {/each}
        </div>
      </section>
    {:else}
      <PitchBoard
        {lineup}
        {anchorId}
        {teamDisplay}
        {comparing}
        {teamDelta}
        onCardFocus={onCardFocus}
        onCardEnter={onCardEnter}
        onCardActivate={onCardActivate}
      />
    {/if}

    {#if view === 'plan'}
      <BenchDrawer
        bench={lineup.bench}
        reserve={lineup.reserve ?? []}
        open={benchFocused}
        selectedId={anchorId}
        onfocus={onBenchFocus}
        onactivate={onBenchActivate}
        onleave={onBenchLeave}
      />
    {/if}
  </div>

  <div class="plan-crest" aria-hidden="true">
    <img src={career.club.logo} alt="" onerror={hideBrokenImage} />
  </div>
</div>
