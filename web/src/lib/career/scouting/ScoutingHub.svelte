<script>
  import { onMount, tick } from 'svelte'
  import {
    registerBack,
    registerCycle,
    registerPrimary,
    registerReset,
    registerStep,
    registerTabs,
  } from '../../actions.js'
  import { api } from '../../api.js'
  import Icon from '../../Icon.svelte'
  import PlayerActionsModal from '../../PlayerActionsModal.svelte'
  import TabBar from '../../ui/TabBar.svelte'
  import { focusFirst } from '../../input.js'
  import { createScoutingState } from '../state/scouting.svelte.js'
  import { REPORT_TABS } from '../constants/scouting.js'
  import ScoutPanel from './ScoutPanel.svelte'
  import ScoutTaskPanel from './ScoutTaskPanel.svelte'
  import ScoutGrid from './ScoutGrid.svelte'
  import ScoutTaskCard from './ScoutTaskCard.svelte'
  import ScoutMapPanel from './ScoutMapPanel.svelte'
  import ScoutTaskEditor from './ScoutTaskEditor.svelte'
  import ScoutReportsFeed from './ScoutReportsFeed.svelte'
  import ScoutingModal from './ScoutingModal.svelte'
  import {
    attributeGroups,
    formatDate,
    formatValue,
    hideBrokenImage,
    plural,
    posTone,
    positionLabel,
    shortRole,
    statTone,
  } from '../../format.js'

  let {
    career,
    mode = 'scouts',
    initialEntryId = null,
    backToHub = false,
    onclose = () => {},
    onaction = async () => null,
    onoffer = null,
    onnegotiate = null,
    hints = $bindable([]),
  } = $props()

  const networkTabs = [
    { id: 'scouts', label: 'Скауты' },
    { id: 'tasks', label: 'Задачи' },
  ]

  const hub = createScoutingState({
    getCareer: () => career,
    getMode: () => mode,
    getBackToHub: () => backToHub,
    getInitialEntryId: () => initialEntryId,
    onclose,
    onaction,
    focusFirst,
  })

  $effect(() => {
    hints = hub.hints
  })

  function monthsUntil(value) {
    if (!value || !career?.date) return null
    const target = new Date(`${value}T00:00:00`)
    const current = new Date(`${career.date}T00:00:00`)
    if (Number.isNaN(target.getTime()) || Number.isNaN(current.getTime())) return null
    const days = (target.getTime() - current.getTime()) / 86_400_000
    if (days <= 0) return 0
    return Math.ceil(days / 30.44)
  }

  $effect(() => {
    hints = hub.hintList
  })

  onMount(() => {
    const stopBack = registerBack(hub.handleBack)
    const stopTabs = registerTabs(hub.handleTabs)
    const stopPrimary = registerPrimary(hub.handlePrimary)
    const stopStep = registerStep(hub.handleStep)
    const stopReset = registerReset(hub.handleReset)
    const stopCycle = registerCycle(hub.handleCycle)
    tick().then(focusFirst)
    return () => {
      stopBack()
      stopTabs()
      stopPrimary()
      stopStep()
      stopReset()
      stopCycle()
    }
  })

</script>

<div class="sc-screen">
  {#if hub.view === 'scouts' || hub.view === 'tasks'}
    <header class="sc-head">
      <TabBar
        tabs={networkTabs}
        active={hub.networkTab}
        onselect={(id) => {
          hub.networkTab = id
          hub.go(id)
        }}
      />
    </header>
  {:else if hub.view !== 'reports'}
    <header class="sc-head">
      <div class="sc-headline">
        <strong class="sc-title">
          {hub.view === 'task'
            ? 'Задача скаута'
            : hub.view === 'hire'
              ? 'Нанять скаута'
              : hub.view === 'region'
                ? 'Выбор региона'
                : hub.view === 'country'
                  ? 'Выбор страны'
                  : 'Сеть поиска'}
        </strong>
        <span class="sc-sub">
          {hub.busy ? 'Сохранение…' : `${career.club.name} · ${formatDate(career.date)}`}
        </span>
      </div>
    </header>
  {/if}

  {#if hub.error}
    <div class="sc-error">error={hub.error}</div>
  {/if}

  {#if hub.view === 'scouts'}
    <div class="sc-body sc-scouts">
      <ScoutGrid
        scouts={hub.scouts}
        emptySlots={hub.emptySlots}
        selectedId={hub.selectedScout?.id}
        statusFor={hub.scoutStatus}
        onFocus={(id) => (hub.selectedScoutId = id)}
        onOpen={hub.openScout}
        onHire={hub.openHire}
      />

      <ScoutPanel
        scout={hub.selectedScout}
        status={hub.selectedScout
          ? hub.scoutStatus(hub.selectedScout)
          : { tone: '', title: '', detail: '' }}
        criteriaLine={hub.criteriaLine}
      />
    </div>

  {:else if hub.view === 'tasks'}
    <div class="sc-body sc-tasks">
      <section class="sc-grid" aria-label="Задачи скаутов">
        {#each hub.scouts as scout, index (scout.id)}
          {@const task = scout.task}
          {@const report = scout.report}
          <ScoutTaskCard
            {scout}
            {task}
            {report}
            title={task ? hub.taskTitle(task) : report ? 'Отчёт по запросу' : 'Добавить новую задачу'}
            subtitle={task
              ? hub.taskSubtitle(task)
              : report
                ? `Следит за ${report.player_name}`
                : 'Выберите регион поиска'}
            selected={hub.selectedTaskScout?.id === scout.id}
            autofocus={index === 0}
            onFocus={() => (hub.selectedTaskScoutId = scout.id)}
            onOpen={() => {
              if (task) hub.openTask(scout)
              else if (report) hub.openReports('requests', report.player_id, scout.id, 'tasks')
              else hub.openScout(scout)
            }}
          />
        {/each}
        {#each Array(hub.emptySlots) as _, index (index)}
          <button class="sc-tile is-empty" data-nav onclick={hub.openHire}>
            <span class="sc-tile-empty">Нанять скаута</span>
          </button>
        {/each}
      </section>

      <ScoutTaskPanel
        scout={hub.selectedTaskScout}
        task={hub.selectedTaskScout?.task ?? null}
        report={hub.selectedTaskScout?.report ?? null}
        criteriaLine={hub.criteriaLine}
        pitchZone={hub.pitchZone}
        onOpenReports={() =>
          hub.openReports('recommendations', null, hub.selectedTaskScout.id, 'tasks')}
      />
    </div>

  {:else if hub.view === 'hire'}
  {:else if hub.view === 'region' || hub.view === 'country'}
    <ScoutMapPanel
      view={hub.view}
      regions={hub.regions}
      region={hub.region}
      country={hub.country}
      countryLeagues={hub.countryLeagues}
      networks={hub.networks}
      scouts={hub.scouts}
      assignScoutId={hub.assignScoutId}
      onFocusRegion={(id) => {
        hub.regionId = id
        hub.countryId = null
      }}
      onSelectRegion={(id) => {
        hub.regionId = id
        hub.countryId = null
        hub.go('country')
      }}
      onFocusCountry={(id) => (hub.countryId = id)}
      onSelectCountry={(id) => (hub.countryId = id)}
      onNext={hub.nextAssignStep}
      scoutName={hub.scoutName}
      countryPosition={hub.countryPosition}
    />
  {:else if hub.view === 'task'}
    <ScoutTaskEditor
      taskDraft={hub.taskDraft}
      taskField={hub.taskField}
      taskScout={hub.taskScout}
      activeTask={hub.activeTask}
      onSelectField={hub.selectTaskField}
      roleLabel={hub.roleLabel}
      rangeLabel={hub.rangeLabel}
      criteriaLine={hub.criteriaLine}
      pitchZone={hub.pitchZone}
      onOpenReports={async () => {
        await hub.saveTask()
        hub.openReports('recommendations', null, hub.taskScout?.id, 'tasks')
      }}
    />
  {:else if hub.view === 'reports'}
    <ScoutReportsFeed
      filter={hub.reportFilter}
      filters={REPORT_TABS}
      scoutFilter={hub.scoutFilter}
      entries={hub.entries}
      selectedEntry={hub.selectedEntry}
      failedPhotos={hub.failedPhotos}
      entryActionsOpen={hub.entryActionsOpen}
      onFilter={(id) => {
        hub.reportFilter = id
        hub.selectedEntryId = null
        tick().then(focusFirst)
      }}
      onFocusEntry={(id) => (hub.selectedEntryId = id)}
      onOpenEntry={(entry) => {
        hub.selectedEntryId = entry.player.id
        hub.openEntryActions(entry)
      }}
      onEntryFail={(id) => (hub.failedPhotos[id] = true)}
      scoutName={hub.scoutName}
      footLabel={hub.footLabel}
      {positionLabel}
      playerStatRows={hub.playerStatRows}
    />

  {/if}

  {#if hub.entryActionsOpen && hub.entryActionsEntry}
    <PlayerActionsModal
      player={hub.entryActionsEntry.player}
      revealed
      shortlisted={Boolean(hub.entryActionsEntry.player.shortlisted)}
      contractMonths={monthsUntil(hub.entryActionsEntry.player.contract_expires)}
      removeLabel="Удалить из отчёта"
      onremove={hub.removeActiveEntry}
      onshortlist={() => hub.toggleShortlist(hub.entryActionsEntry.player)}
      ontransfer={onoffer
        ? () => onoffer(hub.entryActionsEntry.player, 'transfer')
        : null}
      onloan={onoffer
        ? () => onoffer(hub.entryActionsEntry.player, 'loan')
        : null}
      ondiscuss={onnegotiate
        ? () => onnegotiate(hub.entryActionsEntry.player)
        : null}
    />
  {/if}

  <ScoutingModal
    view={hub.view}
    candidates={hub.candidates}
    balance={hub.balance}
    hireCandidateId={hub.hireCandidate?.id}
    onFocusHire={(id) => (hub.hireId = id)}
    onHire={(id) => {
      hub.hireId = id
      hub.askHire()
    }}
    confirm={hub.confirm}
    onConfirm={() => hub.confirm?.action()}
    onCancelConfirm={() => (hub.confirm = null)}
    hints={hub.hints}
  />
</div>
