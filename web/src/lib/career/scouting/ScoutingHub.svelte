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
  import { focusFirst } from '../../input.js'
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

  function monthsUntil(value) {
    if (!value || !career?.date) return null
    const target = new Date(`${value}T00:00:00`)
    const current = new Date(`${career.date}T00:00:00`)
    if (Number.isNaN(target.getTime()) || Number.isNaN(current.getTime())) return null
    const days = (target.getTime() - current.getTime()) / 86_400_000
    if (days <= 0) return 0
    return Math.ceil(days / 30.44)
  }

  const ROLE_FILTERS = [
    { id: '', label: 'Все' },
    { id: 'GK', label: 'Врт' },
    { id: 'DEF', label: 'Защ' },
    { id: 'MID', label: 'ПЗЩ' },
    { id: 'FWD', label: 'Нап' },
  ]
  const TASK_ROLES = [
    { id: '', label: 'Любая позиция' },
    { id: 'GK', label: 'Вратарь' },
    { id: 'DEF', label: 'Защитник' },
    { id: 'MID', label: 'Полузащитник' },
    { id: 'FWD', label: 'Нападающий' },
  ]
  const ROLE_GROUP = {
    GK: 'GK',
    CB: 'DEF',
    LB: 'DEF',
    RB: 'DEF',
    LWB: 'DEF',
    RWB: 'DEF',
    SW: 'DEF',
    DM: 'MID',
    CM: 'MID',
    LM: 'MID',
    RM: 'MID',
    AM: 'MID',
    CF: 'FWD',
    ST: 'FWD',
    LW: 'FWD',
    RW: 'FWD',
  }

  let scouting = $derived(career.scouting ?? null)
  let scouts = $derived(scouting?.scouts ?? [])
  let candidates = $derived(scouting?.candidates ?? [])
  let regions = $derived(scouting?.regions ?? [])
  let networks = $derived(scouting?.networks ?? [])
  let counts = $derived(scouting?.counts ?? { new: 0, updates: 0, total: 0 })
  let maxScouts = $derived(scouting?.max_scouts ?? 6)
  let balance = $derived(career.squad?.finance?.balance ?? 0)

  let view = $state(mode === 'reports' ? 'reports' : mode === 'tasks' ? 'tasks' : 'scouts')
  let networkTab = $state(mode === 'tasks' ? 'tasks' : 'scouts')
  let reportTab = $state('requests')
  let reportsReturn = $state(backToHub ? 'close' : 'scouts')
  let selectedScoutId = $state(null)
  let selectedTaskScoutId = $state(null)
  let selectedEntryId = $state(initialEntryId)
  let scoutFilter = $state(null)
  let roleFilter = $state('')
  let hireId = $state(null)
  let confirm = $state(null)
  let error = $state('')
  let busy = $state(false)
  let acked = $state(false)
  let initialResolved = $state(false)
  let failedPhotos = $state({})
  let entryActionsOpen = $state(false)
  let entryActionsId = $state(null)
  let assignScoutId = $state(null)
  let regionId = $state(null)
  let countryId = $state(null)
  let countryLeagues = $state([])
  let taskScoutId = $state(null)
  let taskField = $state(null)
  let taskRangeRow = $state('min')
  let taskDraft = $state(null)
  let taskSaved = $state(true)

  let selectedScout = $derived(
    scouts.find((scout) => scout.id === selectedScoutId) ?? scouts[0] ?? null,
  )
  let selectedTaskScout = $derived(
    scouts.find((scout) => scout.id === selectedTaskScoutId) ?? scouts[0] ?? null,
  )
  let region = $derived(regions.find((item) => item.id === regionId) ?? regions[0] ?? null)
  let country = $derived(
    region?.countries.find((item) => item.id === countryId) ?? region?.countries[0] ?? null,
  )
  let hireCandidate = $derived(
    candidates.find((item) => item.id === hireId) ?? candidates[0] ?? null,
  )
  let entrySource = $derived(
    reportTab === 'requests' ? (scouting?.reports ?? []) : (scouting?.recommendations ?? []),
  )
  let entries = $derived.by(() => {
    let list = entrySource
    if (scoutFilter) list = list.filter((entry) => entry.scout_id === scoutFilter)
    if (roleFilter) {
      list = list.filter(
        (entry) => ROLE_GROUP[entry.player.role] === roleFilter,
      )
    }
    return list
  })
  let selectedEntry = $derived(
    entries.find((entry) => entry.player.id === selectedEntryId) ?? entries[0] ?? null,
  )
  let entryActionsEntry = $derived(
    entrySource.find((entry) => entry.player.id === entryActionsId) ?? null,
  )
  let taskScout = $derived(
    scouts.find((scout) => scout.id === taskScoutId) ?? scouts[0] ?? null,
  )
  let emptySlots = $derived(Math.max(0, maxScouts - scouts.length))
  let activeTask = $derived(
    view === 'task' ? taskScout?.task ?? null : selectedTaskScout?.task ?? null,
  )

  let hintList = $derived.by(() => {
    const nav = { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Навигация' }
    const back = { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' }
    const open = { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' }
    if (entryActionsOpen) {
      return [
        nav,
        open,
        { gamepad: ['X'], keyboard: ['X'], label: 'Удалить из отчёта' },
        back,
      ]
    }
    if (view === 'reports') {
      return [
        nav,
        { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Вкладки' },
        open,
        back,
      ]
    }
    if (view === 'hire') {
      return [nav, open, back]
    }
    if (view === 'region' || view === 'country') {
      return [nav, open, back]
    }
    if (view === 'task') {
      return taskField
        ? [
            { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
            { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Порог' },
            open,
            back,
          ]
        : [nav, open, { gamepad: ['X'], keyboard: ['X'], label: 'По умолчанию' }, back]
    }
    return [
      nav,
      { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Вкладки' },
      open,
      back,
    ]
  })

  $effect(() => {
    hints = hintList
  })

  $effect(() => {
    if (initialResolved || !initialEntryId) return
    const requests = (scouting?.reports ?? []).some(
      (entry) => entry.player.id === initialEntryId,
    )
    const recommendations = (scouting?.recommendations ?? []).some(
      (entry) => entry.player.id === initialEntryId,
    )
    if (!requests && recommendations) reportTab = 'recommendations'
    selectedEntryId = initialEntryId
    initialResolved = true
  })

  $effect(() => {
    if (view !== 'reports' || acked) return
    if (!counts.new) {
      acked = true
      return
    }
    acked = true
    onaction({ type: 'scout_ack' })
  })

  $effect(() => {
    if (!regions.length) return
    if (!regionId) regionId = regions[0].id
    if (region && !region.countries.some((item) => item.id === countryId)) {
      countryId = region.countries[0]?.id ?? null
    }
  })

  $effect(() => {
    const id = country?.id
    if (!id) {
      countryLeagues = []
      return
    }
    let alive = true
    api
      .leagues(id)
      .then((items) => {
        if (alive) countryLeagues = items
      })
      .catch(() => {
        if (alive) countryLeagues = []
      })
    return () => {
      alive = false
    }
  })

  onMount(() => {
    const stopBack = registerBack(handleBack)
    const stopTabs = registerTabs(handleTabs)
    const stopPrimary = registerPrimary(handlePrimary)
    const stopStep = registerStep(handleStep)
    const stopReset = registerReset(handleReset)
    const stopCycle = registerCycle(handleCycle)
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

  function go(next) {
    view = next
    error = ''
    tick().then(focusFirst)
  }

  function openReports(tab, entryId = null, scoutId = null, returnTo = 'scouts') {
    reportTab = tab
    selectedEntryId = entryId
    scoutFilter = scoutId
    roleFilter = ''
    reportsReturn = returnTo
    acked = false
    go('reports')
  }

  function openScout(scout) {
    if (!scout) return
    if (scout.report) {
      openReports('requests', scout.report.player_id, scout.id)
      return
    }
    if (scout.task) {
      openReports('recommendations', null, scout.id)
      return
    }
    startAssign(scout.id)
  }

  function startAssign(scoutId) {
    assignScoutId = scoutId
    regionId = region?.id ?? regions[0]?.id ?? null
    countryId = null
    go('region')
  }

  function openHire() {
    hireId = candidates[0]?.id ?? null
    go('hire')
  }

  function openTask(scout) {
    if (!scout) return
    taskScoutId = scout.id
    taskDraft = { ...(scout.task?.criteria ?? defaultCriteria()) }
    taskField = null
    taskSaved = true
    go('task')
  }

  function defaultCriteria() {
    return {
      role: '',
      age_min: null,
      age_max: null,
      contract_min: null,
      contract_max: null,
    }
  }

  function footLabel(foot) {
    if (foot === 'left') return 'Левая'
    if (foot === 'right') return 'Правая'
    return foot || '—'
  }

  function roleLabel(role) {
    return TASK_ROLES.find((item) => item.id === role)?.label ?? 'Любая позиция'
  }

  function rangeLabel(min, max, suffix = '') {
    if (min === null && max === null) return 'Любой'
    return `${min ?? '—'} – ${max ?? '—'}${suffix}`
  }

  function criteriaLine(criteria) {
    if (!criteria) return ''
    const parts = [roleLabel(criteria.role)]
    if (criteria.age_min !== null || criteria.age_max !== null) {
      parts.push(`Возраст ${rangeLabel(criteria.age_min, criteria.age_max)}`)
    }
    if (criteria.contract_min !== null || criteria.contract_max !== null) {
      parts.push(`Контракт ${rangeLabel(criteria.contract_min, criteria.contract_max)}`)
    }
    return parts.join(' · ')
  }

  function taskTitle(task) {
    return task ? `Сеть в ${task.country_name}` : 'Добавить новую задачу'
  }

  function taskSubtitle(task) {
    if (!task) return 'Скаут свободен — выберите регион поиска'
    return criteriaLine(task.criteria)
  }

  function scoutStatus(scout) {
    if (scout.report) {
      return {
        tone: 'active',
        title: `Следит за ${scout.report.player_name}`,
        detail: `Осталось ${scout.report.days_left} ${plural(scout.report.days_left, 'день', 'дня', 'дней')}`,
      }
    }
    if (scout.task) {
      return {
        tone: 'active',
        title: 'Просмотр региона',
        detail: `${scout.task.found_count} ${plural(scout.task.found_count, 'игрок', 'игрока', 'игроков')}`,
      }
    }
    return { tone: 'free', title: 'Скаут доступен', detail: '' }
  }

  function playerStatRows(player) {
    if (!player?.stats) return []
    return attributeGroups(player.stats)
      .flatMap((group) => group.rows)
      .slice(0, 6)
  }

  function pitchZone(role) {
    const group = ROLE_GROUP[role] ?? ''
    if (group === 'GK') return 'gk'
    if (group === 'DEF') return 'def'
    if (group === 'MID') return 'mid'
    return 'fwd'
  }

  function countryPosition(index) {
    const rings = [
      { size: 8, radius: 19 },
      { size: 12, radius: 32 },
      { size: 12, radius: 43 },
    ]
    let rest = index
    let ring = rings[0]
    for (const candidate of rings) {
      if (rest < candidate.size) {
        ring = candidate
        break
      }
      rest -= candidate.size
    }
    const angle = (Math.PI * 2 * rest) / Math.max(1, ring.size) - Math.PI / 2
    return {
      left: `${50 + Math.cos(angle) * ring.radius}%`,
      top: `${50 + Math.sin(angle) * ring.radius}%`,
    }
  }

  function openEntryActions(entry) {
    if (!entry) return
    entryActionsId = entry.player.id
    entryActionsOpen = true
    tick().then(focusFirst)
  }

  function closeEntryActions() {
    const id = entryActionsId
    entryActionsOpen = false
    entryActionsId = null
    tick().then(() => {
      const element = id
        ? document.querySelector(`[data-entry="${id}"]`)
        : null
      if (element) element.focus({ preventScroll: true })
      else focusFirst()
    })
  }

  async function removeActiveEntry() {
    const entry = entryActionsEntry
    if (!entry) return
    const updated = await runAction({
      type: 'scout_remove',
      player_id: entry.player.id,
    })
    if (!updated) return
    selectedEntryId = null
    entryActionsOpen = false
    entryActionsId = null
    tick().then(focusFirst)
  }

  async function toggleShortlist(player) {
    if (!player) return
    await runAction({ type: 'shortlist_toggle', player_id: player.id })
  }

  function cycleReport(direction) {
    if (!entries.length) return
    const index = Math.max(
      0,
      entries.findIndex((entry) => entry.player.id === selectedEntry?.player.id),
    )
    const offset = direction === 'right' ? 1 : -1
    const next = entries[(index + offset + entries.length) % entries.length]
    selectedEntryId = next.player.id
    tick().then(() => {
      document
        .querySelector(`[data-entry="${next.player.id}"]`)
        ?.focus({ preventScroll: true })
    })
  }

  function cycleScout(direction) {
    if (!scouts.length) return
    const index = Math.max(
      0,
      scouts.findIndex((scout) => scout.id === selectedTaskScout?.id),
    )
    const offset = direction === 'right' ? 1 : -1
    selectedTaskScoutId = scouts[(index + offset + scouts.length) % scouts.length].id
    tick().then(focusFirst)
  }

  function handleTabs(direction) {
    if (
      entryActionsOpen ||
      confirm ||
      view === 'hire' ||
      view === 'region' ||
      view === 'country' ||
      view === 'task'
    ) {
      return
    }
    if (view === 'reports') {
      reportTab = reportTab === 'requests' ? 'recommendations' : 'requests'
      selectedEntryId = null
      tick().then(focusFirst)
      return
    }
    networkTab = networkTab === 'scouts' ? 'tasks' : 'scouts'
    view = networkTab
    selectedEntryId = null
    tick().then(focusFirst)
  }

  function handleCycle(direction) {
    if (entryActionsOpen) return false
    if (view === 'reports') {
      cycleReport(direction)
      return true
    }
    if (view === 'scouts' || view === 'tasks') {
      cycleScout(direction)
      return true
    }
    if (view === 'task' && taskField) {
      stepTaskRange(direction === 'right' ? 1 : -1)
      return true
    }
    return false
  }

  async function handleBack() {
    if (busy) return
    if (entryActionsOpen) {
      closeEntryActions()
      return
    }
    if (confirm) {
      confirm = null
      tick().then(focusFirst)
      return
    }
    if (view === 'hire') {
      go('scouts')
      return
    }
    if (view === 'region') {
      go('scouts')
      return
    }
    if (view === 'country') {
      go('region')
      return
    }
    if (view === 'task') {
      if (taskField) {
        taskField = null
        tick().then(focusFirst)
        return
      }
      await saveTask()
      view = 'tasks'
      taskScoutId = null
      tick().then(focusFirst)
      return
    }
    if (view === 'reports') {
      if (reportsReturn === 'close') {
        onclose()
      } else {
        selectedEntryId = null
        scoutFilter = null
        go(networkTab)
      }
      return
    }
    onclose()
  }

  function handlePrimary() {
    if (view === 'task' && taskField) {
      taskField = null
      tick().then(focusFirst)
      return true
    }
    return false
  }

  function handleReset() {
    if (entryActionsOpen && entryActionsEntry) {
      removeActiveEntry()
      return true
    }
    if (view === 'reports' && selectedEntry) {
      return false
    }
    if (view === 'task') {
      taskDraft = defaultCriteria()
      taskSaved = false
      taskField = null
      return true
    }
    return false
  }

  function handleStep(direction) {
    if (view !== 'task' || !taskField) return false
    if (taskField === 'role') {
      if (direction === 'left' || direction === 'right') stepRole(direction === 'right' ? 1 : -1)
      return true
    }
    if (direction === 'up' || direction === 'down') {
      taskRangeRow = taskRangeRow === 'min' ? 'max' : 'min'
      return true
    }
    stepTaskRange(direction === 'right' ? 1 : -1)
    return true
  }

  function stepRole(delta) {
    if (!taskDraft) return
    const index = TASK_ROLES.findIndex((item) => item.id === taskDraft.role)
    const next = TASK_ROLES[(index + delta + TASK_ROLES.length) % TASK_ROLES.length]
    taskDraft.role = next.id
    taskSaved = false
  }

  function stepTaskRange(delta) {
    if (!taskDraft || (taskField !== 'age' && taskField !== 'contract')) return
    const config =
      taskField === 'age'
        ? { min: 16, max: 35 }
        : { min: 0, max: 5 }
    const minKey = `${taskField}_min`
    const maxKey = `${taskField}_max`
    const key = taskRangeRow === 'min' ? minKey : maxKey
    const current = taskDraft[key]
    let next
    if (current === null) {
      next = delta > 0 ? config.min : config.max
    } else {
      next = current + delta
      if (next < config.min || next > config.max) next = null
    }
    taskDraft[key] = next
    if (
      taskDraft[minKey] !== null &&
      taskDraft[maxKey] !== null &&
      taskDraft[minKey] > taskDraft[maxKey]
    ) {
      if (taskRangeRow === 'min') taskDraft[maxKey] = taskDraft[minKey]
      else taskDraft[minKey] = taskDraft[maxKey]
    }
    taskSaved = false
  }

  function selectTaskField(field) {
    if (field === 'traits') return
    if (taskField === field) {
      taskField = null
      tick().then(focusFirst)
      return
    }
    taskField = field
    taskRangeRow = 'min'
  }

  async function runAction(payload) {
    if (busy) return null
    busy = true
    error = ''
    const updated = await onaction(payload)
    busy = false
    if (!updated) {
      error = 'Не удалось выполнить действие'
      return null
    }
    return updated
  }

  async function saveTask() {
    if (!taskScoutId || !taskDraft || taskSaved) return
    const updated = await runAction({
      type: 'scout_task',
      scout_id: taskScoutId,
      criteria: taskDraft,
    })
    if (updated) taskSaved = true
  }

  async function confirmHire() {
    if (!hireCandidate) return
    const updated = await runAction({
      type: 'scout_hire',
      scout_id: hireCandidate.id,
    })
    confirm = null
    if (!updated) return
    selectedScoutId = hireCandidate.id
    go('scouts')
  }

  async function confirmNetwork() {
    if (!assignScoutId || !region || !country) return
    const updated = await runAction({
      type: 'scout_network',
      scout_id: assignScoutId,
      region_id: region.id,
      country_id: country.id,
    })
    confirm = null
    if (!updated) return
    selectedTaskScoutId = assignScoutId
    networkTab = 'tasks'
    go('tasks')
  }

  function askHire() {
    if (!hireCandidate) return
    if (!hireCandidate.affordable) {
      error = 'Недостаточно средств'
      return
    }
    confirm = {
      title: `${hireCandidate.name} станет вашим новым скаутом. Вы уверены в своем решении?`,
      yes: 'Да',
      no: 'Нет',
      action: confirmHire,
    }
    tick().then(focusFirst)
  }

  function askNetwork() {
    if (!country) return
    confirm = {
      title: 'Вы уверены, что хотите организовать здесь сеть поиска игроков?',
      yes: 'OK',
      no: 'Отмена',
      action: confirmNetwork,
    }
    tick().then(focusFirst)
  }

  function nextAssignStep() {
    if (view === 'region') {
      go('country')
      return
    }
    askNetwork()
  }

  function scoutName(scoutId) {
    return scouts.find((scout) => scout.id === scoutId)?.name ?? ''
  }
</script>

<div class="sc-screen">
  <header class="sc-head">
    <div class="sc-crumbs">Трансферы <i>›</i> Всемирная трансферная сеть</div>
    {#if view === 'scouts' || view === 'tasks'}
      <div class="sc-tabs" role="tablist">
        <button
          class="sc-tab"
          class:is-active={networkTab === 'scouts'}
          data-nav
          onclick={() => {
            networkTab = 'scouts'
            go('scouts')
          }}
        >
          Скауты
        </button>
        <button
          class="sc-tab"
          class:is-active={networkTab === 'tasks'}
          data-nav
          onclick={() => {
            networkTab = 'tasks'
            go('tasks')
          }}
        >
          Задачи
        </button>
      </div>
    {:else if view === 'reports'}
      <div class="sc-title-line">
        <strong class="sc-title">Отчёт скаута</strong>
        <span class="sc-sub">
          {busy ? 'Сохранение…' : `${career.club.name} · ${formatDate(career.date)}`}
        </span>
      </div>
    {:else}
      <div class="sc-title-line">
        <span class="sc-sub">
          {busy ? 'Сохранение…' : `${career.club.name} · ${formatDate(career.date)}`}
        </span>
      </div>
    {/if}
  </header>

  {#if error}
    <div class="sc-error">{error}</div>
  {/if}

  {#if view === 'scouts'}
    <div class="sc-body sc-scouts">
      <ScoutGrid
        {scouts}
        {emptySlots}
        selectedId={selectedScout?.id}
        statusFor={scoutStatus}
        onFocus={(id) => (selectedScoutId = id)}
        onOpen={openScout}
        onHire={openHire}
      />

      <aside class="sc-panel scroll-area" aria-label="Сведения о скауте">
        {#if selectedScout}
          {@const status = scoutStatus(selectedScout)}
          <div class="sc-panel-head">
            <span class="sc-panel-flag">
              {#if selectedScout.flag}
                <img src={selectedScout.flag} alt="" onerror={hideBrokenImage} />
              {/if}
            </span>
            <div>
              <strong class="sc-panel-name">{selectedScout.name}</strong>
              <span class="sc-panel-country">{selectedScout.nationality}</span>
            </div>
            <div class="sc-stars" aria-label={`Решение ${selectedScout.judgement} из 5`}>
              {#each [0, 1, 2, 3, 4] as star (star)}
                <i class:on={star < selectedScout.judgement}>★</i>
              {/each}
            </div>
          </div>

          <div class="sc-panel-status" class:is-free={status.tone === 'free'}>
            <span>{status.title}</span>
            {#if status.detail}<small>{status.detail}</small>{/if}
          </div>

          {#if selectedScout.task}
            <div class="sc-panel-section">
              <div class="sc-panel-label">Сеть поиска</div>
              <div class="sc-panel-big">{selectedScout.task.country_name}</div>
              <div class="sc-panel-muted">{selectedScout.task.region_name}</div>
              <div class="sc-panel-stats">
                <span>Дней работы <b>{selectedScout.task.days_worked}</b></span>
                <span>Найдено <b>{selectedScout.task.found_count}</b></span>
              </div>
              <div class="sc-panel-muted">{criteriaLine(selectedScout.task.criteria)}</div>
            </div>
          {/if}

          {#if selectedScout.report}
            <div class="sc-panel-section">
              <div class="sc-panel-label">Отчёт по запросу</div>
              <div class="sc-panel-big">{selectedScout.report.player_name}</div>
              <div class="sc-progress">
                <span><i style={`width:${Math.round(selectedScout.report.progress * 100)}%`}></i></span>
                <small>
                  {selectedScout.report.days_worked} / {selectedScout.report.days_total}
                </small>
              </div>
              <div class="sc-panel-muted">
                Осталось {selectedScout.report.days_left}
                {plural(selectedScout.report.days_left, 'день', 'дня', 'дней')}
              </div>
            </div>
          {/if}

          <div class="sc-panel-section">
            <div class="sc-panel-label">Характеристики</div>
            <div class="sc-panel-row"><span>Опыт</span><b>{selectedScout.experience} / 5</b></div>
            <div class="sc-panel-row"><span>Решение</span><b>{selectedScout.judgement} / 5</b></div>
            <div class="sc-panel-row"><span>Стоимость</span><b>{formatValue(selectedScout.price)}</b></div>
          </div>
        {:else}
          <p class="sc-panel-muted">Скаутов пока нет — наймите первого.</p>
        {/if}
      </aside>
    </div>

  {:else if view === 'tasks'}
    <div class="sc-body sc-tasks">
      <section class="sc-grid" aria-label="Задачи скаутов">
        {#each scouts as scout, index (scout.id)}
          {@const task = scout.task}
          {@const report = scout.report}
          <ScoutTaskCard
            {scout}
            {task}
            {report}
            title={task ? taskTitle(task) : report ? 'Отчёт по запросу' : 'Добавить новую задачу'}
            subtitle={task
              ? taskSubtitle(task)
              : report
                ? `Следит за ${report.player_name}`
                : 'Выберите регион поиска'}
            selected={selectedTaskScout?.id === scout.id}
            autofocus={index === 0}
            onFocus={() => (selectedTaskScoutId = scout.id)}
            onOpen={() => {
              if (task) openTask(scout)
              else if (report) openReports('requests', report.player_id, scout.id, 'tasks')
              else openScout(scout)
            }}
          />
        {/each}
        {#each Array(emptySlots) as _, index (index)}
          <button class="sc-tile is-empty" data-nav onclick={openHire}>
            <span class="sc-tile-empty">Нанять скаута</span>
          </button>
        {/each}
      </section>

      <aside class="sc-panel scroll-area" aria-label="Подробности задачи">
        {#if selectedTaskScout}
          {@const task = selectedTaskScout.task}
          {@const report = selectedTaskScout.report}
          <div class="sc-panel-title">Подробности</div>
          <div class="sc-panel-stats">
            <span>Найдены игроки <b>{task ? task.found_count : 0}</b></span>
            <span>Дней работы скаута <b>{task ? task.days_worked : report ? report.days_worked : 0}</b></span>
          </div>
          <div class="sc-pitch" class:is-task={Boolean(task)}>
            <span class="sc-pitch-zone {task ? pitchZone(task.criteria.role) : 'all'}"></span>
            <span class="sc-pitch-line halfway"></span>
            <span class="sc-pitch-circle"></span>
            <span class="sc-pitch-box top"></span>
            <span class="sc-pitch-box bottom"></span>
          </div>
          <div class="sc-panel-section">
            <div class="sc-panel-row">
              <span>Скаут</span><b>{selectedTaskScout.name}</b>
            </div>
            {#if task}
              <div class="sc-panel-row"><span>Регион</span><b>{task.region_name}</b></div>
              <div class="sc-panel-row"><span>Страна</span><b>{task.country_name}</b></div>
              <div class="sc-panel-muted">{criteriaLine(task.criteria)}</div>
            {:else if report}
              <div class="sc-panel-row"><span>Игрок</span><b>{report.player_name}</b></div>
              <div class="sc-panel-muted">
                Осталось {report.days_left}
                {plural(report.days_left, 'день', 'дня', 'дней')}
              </div>
            {:else}
              <div class="sc-panel-muted">
                Задача не назначена. Выберите регион и страну поиска.
              </div>
            {/if}
          </div>
          {#if task}
            <button
              class="sc-wide-action"
              data-nav
              onclick={() =>
                openReports('recommendations', null, selectedTaskScout.id, 'tasks')}
            >
              <span>Список найденных игроков</span>
              <span class="sc-key">A</span>
            </button>
          {/if}
        {/if}
      </aside>
    </div>

  {:else if view === 'hire'}
  {:else if view === 'region' || view === 'country'}
    <ScoutMapPanel
      {view}
      {regions}
      {region}
      {country}
      {countryLeagues}
      {networks}
      {scouts}
      {assignScoutId}
      onFocusRegion={(id) => {
        regionId = id
        countryId = null
      }}
      onSelectRegion={(id) => {
        regionId = id
        countryId = null
        go('country')
      }}
      onFocusCountry={(id) => (countryId = id)}
      onSelectCountry={(id) => (countryId = id)}
      onNext={nextAssignStep}
      {scoutName}
      {countryPosition}
    />
  {:else if view === 'task'}
    <ScoutTaskEditor
      {taskDraft}
      {taskField}
      {taskScout}
      {activeTask}
      onSelectField={selectTaskField}
      {roleLabel}
      {rangeLabel}
      {criteriaLine}
      {pitchZone}
      onOpenReports={async () => {
        await saveTask()
        openReports('recommendations', null, taskScout?.id, 'tasks')
      }}
    />
  {:else if view === 'reports'}
    <ScoutReportsFeed
      {reportTab}
      roleFilters={ROLE_FILTERS}
      {roleFilter}
      {scoutFilter}
      {entries}
      {selectedEntry}
      {failedPhotos}
      {entryActionsOpen}
      onTab={(tab) => {
        reportTab = tab
        selectedEntryId = null
        tick().then(focusFirst)
      }}
      onRoleFilter={(id) => {
        roleFilter = id
        selectedEntryId = null
        tick().then(focusFirst)
      }}
      onFocusEntry={(id) => (selectedEntryId = id)}
      onOpenEntry={(entry) => {
        selectedEntryId = entry.player.id
        openEntryActions(entry)
      }}
      onEntryFail={(id) => (failedPhotos[id] = true)}
      {scoutName}
      {footLabel}
      {positionLabel}
      {playerStatRows}
    />

  {/if}

  {#if entryActionsOpen && entryActionsEntry}
    <PlayerActionsModal
      player={entryActionsEntry.player}
      revealed
      shortlisted={Boolean(entryActionsEntry.player.shortlisted)}
      contractMonths={monthsUntil(entryActionsEntry.player.contract_expires)}
      removeLabel="Удалить из отчёта"
      onremove={removeActiveEntry}
      onshortlist={() => toggleShortlist(entryActionsEntry.player)}
      ontransfer={onoffer
        ? () => onoffer(entryActionsEntry.player, 'transfer')
        : null}
      onloan={onoffer
        ? () => onoffer(entryActionsEntry.player, 'loan')
        : null}
      ondiscuss={onnegotiate
        ? () => onnegotiate(entryActionsEntry.player)
        : null}
    />
  {/if}

  <ScoutingModal
    view={view}
    {candidates}
    {balance}
    hireCandidateId={hireCandidate?.id}
    onFocusHire={(id) => (hireId = id)}
    onHire={(id) => {
      hireId = id
      askHire()
    }}
    {confirm}
    onConfirm={() => confirm?.action()}
    onCancelConfirm={() => (confirm = null)}
  />
</div>
