<script>
  import BenchDrawer from '../../BenchDrawer.svelte'
  import { compareTone, hideBrokenImage, statTone } from '../../format.js'
  import PlayerBlock from '../shared/PlayerBlock.svelte'
  import RadarChart from '../shared/RadarChart.svelte'
  import PitchBoard from './PitchBoard.svelte'
  import RolesPanel from './RolesPanel.svelte'
  import SchemesPanel from './SchemesPanel.svelte'

  let {
    view,
    planTab,
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
    currentFormation,
    schemeLineup,
    visibleFormations,
    formationPage,
    formationPageCount,
    onSelectPlanTab,
    onPreviewFormation,
    onSelectFormation,
    onFormationScroll,
    roleTiles,
    roleFocusId,
    rolePickingId,
    roleAnchorId,
    onRoleFocus,
    onRoleSelect,
    onRolePlayerActivate,
    onCardFocus,
    onCardEnter,
    onCardActivate,
    onBenchFocus,
    onBenchActivate,
    onBenchLeave,
  } = $props()
</script>

<div class="plan">
  <div
    class="plan-stage"
    class:has-drawer={view === 'plan' && planTab === 'squad'}
    class:is-schemes={planTab === 'schemes'}
    class:is-roles={planTab === 'roles'}
  >
    <nav class="plan-tabs" aria-label="План игры">
      {#each planTabs as item (item.id)}
        <button
          class="plan-tab"
          class:active={item.id === planTab}
          disabled={item.disabled}
          onclick={() => !item.disabled && onSelectPlanTab(item.id)}
        >
          {item.label}
        </button>
      {/each}
    </nav>

    {#if view === 'details' && planTab === 'squad'}
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
          <div class="details-list details-stats" class:is-single={detailGroups.length === 1}>
            {#each detailGroups as group (group.id)}
              <div class="details-group">
                <span class="details-group-label">{group.label}</span>
                <div class="details-rows">
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
    {:else if planTab === 'schemes'}
      <PitchBoard
        lineup={schemeLineup}
        cornerLabel={schemeLineup.formation_label ?? currentFormation}
        interactive={false}
        showStrength={false}
      />

      <SchemesPanel
        clubName={career.club.name}
        {currentFormation}
        formations={visibleFormations}
        page={formationPage}
        pageCount={formationPageCount}
        onPreview={onPreviewFormation}
        onSelect={onSelectFormation}
        onScroll={onFormationScroll}
      />
    {:else if planTab === 'roles'}
      <PitchBoard
        {lineup}
        anchorId={roleAnchorId}
        showStrength={false}
        interactive={Boolean(rolePickingId)}
        trapFocus={Boolean(rolePickingId)}
        onCardFocus={onCardFocus}
        onCardEnter={onCardEnter}
        onCardActivate={onRolePlayerActivate}
      />

      <RolesPanel
        roles={roleTiles}
        focusedId={roleFocusId}
        pickingId={rolePickingId}
        onFocus={onRoleFocus}
        onSelect={onRoleSelect}
      />
    {:else}
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

    {#if view === 'plan' && planTab === 'squad'}
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
