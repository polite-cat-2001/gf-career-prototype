<script>
  import { onMount, tick } from 'svelte'
  import {
    registerBack,
    registerCycle,
    registerPrimary,
    registerReset,
    registerStep,
    registerTabs,
  } from './actions.js'
  import { api } from './api.js'
  import Icon from './Icon.svelte'
  import PlayerActionsModal from './PlayerActionsModal.svelte'
  import { focusFirst } from './input.js'
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
  } from './format.js'

  let {
    career,
    mode = 'scouts',
    initialEntryId = null,
    backToHub = false,
    onclose = () => {},
    onaction = async () => null,
    hints = $bindable([]),
  } = $props()

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
      <section class="sc-grid" aria-label="Скауты">
        {#each scouts as scout, index (scout.id)}
          {@const status = scoutStatus(scout)}
          <button
            class="sc-tile"
            class:is-selected={selectedScout?.id === scout.id}
            data-nav
            data-autofocus={index === 0 ? '' : undefined}
            onfocus={() => (selectedScoutId = scout.id)}
            onclick={() => openScout(scout)}
          >
            <span class="sc-tile-flag">
              {#if scout.flag}<img src={scout.flag} alt="" onerror={hideBrokenImage} />{/if}
            </span>
            <strong class="sc-tile-name">{scout.name}</strong>
            <span class="sc-tile-status" class:is-free={status.tone === 'free'}>
              {status.title}
            </span>
            {#if status.detail}
              <span class="sc-tile-detail">{status.detail}</span>
            {:else}
              <span class="sc-tile-arrow">→</span>
            {/if}
            <span class="sc-tile-stars">
              {#each [0, 1, 2, 3, 4] as star (star)}
                <i class:on={star < scout.judgement}>★</i>
              {/each}
              <small>Решение</small>
            </span>
          </button>
        {/each}
        {#each Array(emptySlots) as _, index (index)}
          <button
            class="sc-tile is-empty"
            data-nav
            onclick={openHire}
          >
            <span class="sc-tile-empty">Нанять скаута</span>
          </button>
        {/each}
      </section>

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
          <button
            class="sc-tile sc-task-tile"
            class:is-selected={selectedTaskScout?.id === scout.id}
            data-nav
            data-autofocus={index === 0 ? '' : undefined}
            onfocus={() => (selectedTaskScoutId = scout.id)}
            onclick={() => {
              if (task) openTask(scout)
              else if (report) openReports('requests', report.player_id, scout.id, 'tasks')
              else openScout(scout)
            }}
          >
            <span class="sc-task-owner">{scout.name}</span>
            <strong class="sc-task-title">
              {task ? taskTitle(task) : report ? 'Отчёт по запросу' : 'Добавить новую задачу'}
            </strong>
            <span class="sc-task-sub">
              {task
                ? taskSubtitle(task)
                : report
                  ? `Следит за ${report.player_name}`
                  : 'Выберите регион поиска'}
            </span>
            {#if task}
              <span class="sc-task-found">
                <Icon name="users" size={18} />
                {task.found_count}
              </span>
            {/if}
            {#if report}
              <span class="sc-task-found">
                <Icon name="clock" size={18} />
                {report.days_left}
              </span>
            {/if}
          </button>
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
    <div class="sc-modal-layer">
      <div class="sc-modal sc-hire" role="dialog" aria-modal="true" aria-label="Нанять скаута">
        <header class="sc-modal-head">
          <strong>Нанять скаута</strong>
        </header>
        <div class="sc-hire-top">
          <span>Нанять скаута</span>
          <span>Бюджет {formatValue(balance)}</span>
        </div>
        <div class="sc-hire-head">
          <span>Скаут</span>
          <span>Опыт</span>
          <span>Решение</span>
          <span>Цена</span>
        </div>
        <div class="sc-hire-list scroll-area">
          {#each candidates as candidate, index (candidate.id)}
            <button
              class="sc-hire-row"
              class:is-selected={hireCandidate?.id === candidate.id}
              class:is-disabled={!candidate.affordable}
              data-nav
              data-autofocus={index === 0 ? '' : undefined}
              onfocus={() => (hireId = candidate.id)}
              onclick={() => {
                hireId = candidate.id
                askHire()
              }}
            >
              <span class="sc-hire-scout">
                <span class="sc-hire-flag">
                  {#if candidate.flag}
                    <img src={candidate.flag} alt="" onerror={hideBrokenImage} />
                  {/if}
                </span>
                <span class="sc-hire-name">
                  <b>{candidate.name}</b>
                  <small>{candidate.nationality}</small>
                </span>
              </span>
              <span class="sc-stars">
                {#each [0, 1, 2, 3, 4] as star (star)}
                  <i class:on={star < candidate.experience}>★</i>
                {/each}
              </span>
              <span class="sc-stars">
                {#each [0, 1, 2, 3, 4] as star (star)}
                  <i class:on={star < candidate.judgement}>★</i>
                {/each}
              </span>
              <span class="sc-hire-price">{formatValue(candidate.price)}</span>
            </button>
          {/each}
          {#if !candidates.length}
            <p class="sc-panel-muted">Свободных скаутов нет.</p>
          {/if}
        </div>
      </div>
    </div>

  {:else if view === 'region' || view === 'country'}
    <div class="sc-body sc-map-screen">
      <section class="sc-map-panel">
        <div class="sc-map-head">
          <strong>{view === 'region' ? 'Выбор региона' : region?.name}</strong>
          <span>{view === 'region' ? 'Страны региона появятся на следующем шаге' : 'Выберите страну для сети'}</span>
        </div>
        <div class="sc-map">
          <div class="sc-map-grid" aria-hidden="true"></div>
          {#if view === 'region'}
            {#each regions as item, index (item.id)}
              <button
                class="sc-map-node"
                class:is-selected={region?.id === item.id}
                class:is-locked={Boolean(networks.find((net) => net.region_id === item.id))}
                style={`left:${item.x}%;top:${item.y}%`}
                data-nav
                data-autofocus={region?.id === item.id ? '' : undefined}
                onfocus={() => {
                  regionId = item.id
                  countryId = null
                }}
                onclick={() => {
                  regionId = item.id
                  countryId = null
                  go('country')
                }}
                title={item.name}
              >
                <span class="sc-map-dot"></span>
                <span class="sc-map-label">{item.name}</span>
              </button>
            {/each}
          {:else if region}
            <span class="sc-map-region" style={`left:${region.x}%;top:${region.y}%`}>
              {region.name}
            </span>
            {#each region.countries as item, index (item.id)}
              {@const pos = countryPosition(index)}
              <button
                class="sc-map-node is-country"
                class:is-selected={country?.id === item.id}
                style={`left:${pos.left};top:${pos.top}`}
                data-nav
                data-autofocus={country?.id === item.id ? '' : undefined}
                onfocus={() => (countryId = item.id)}
                onclick={() => (countryId = item.id)}
                title={item.name}
              >
                <span class="sc-map-flag">
                  {#if item.flag}<img src={item.flag} alt="" onerror={hideBrokenImage} />{/if}
                </span>
                <span class="sc-map-label">{item.name}</span>
              </button>
            {/each}
          {/if}
        </div>
      </section>

      <aside class="sc-map-side">
        <div class="sc-map-list scroll-area">
          {#if view === 'region'}
            <div class="sc-map-list-title">{region?.name}</div>
            {#each region?.countries ?? [] as item (item.id)}
              <button
                class="sc-map-row"
                class:is-selected={country?.id === item.id}
                data-nav
                onfocus={() => (countryId = item.id)}
                onclick={() => (countryId = item.id)}
              >
                <span class="sc-hire-flag">
                  {#if item.flag}<img src={item.flag} alt="" onerror={hideBrokenImage} />{/if}
                </span>
                <span>{item.name}</span>
              </button>
            {/each}
          {:else}
            <div class="sc-map-list-title">{country?.name}</div>
            {#each countryLeagues as league (league.id)}
              <div class="sc-map-league">
                {#if league.logo}
                  <img src={league.logo} alt="" onerror={hideBrokenImage} />
                {/if}
                <span>{league.name}</span>
                <small>{league.clubs_count} клубов</small>
              </div>
            {/each}
            {#if !countryLeagues.length}
              <p class="sc-panel-muted">Лиги загружаются…</p>
            {/if}
          {/if}
        </div>

        <div class="sc-scout-mini">
          <div class="sc-panel-label">Скаут</div>
          <div class="sc-panel-head">
            <span class="sc-panel-flag">
              {#if scouts.find((scout) => scout.id === assignScoutId)?.flag}
                <img
                  src={scouts.find((scout) => scout.id === assignScoutId)?.flag}
                  alt=""
                  onerror={hideBrokenImage}
                />
              {/if}
            </span>
            <div>
              <strong class="sc-panel-name">{scoutName(assignScoutId)}</strong>
              <span class="sc-panel-country">Сеть поиска</span>
            </div>
          </div>
          <div class="sc-panel-row">
            <span>Опыт</span>
            <b>{scouts.find((scout) => scout.id === assignScoutId)?.experience ?? 0} / 5</b>
          </div>
          <div class="sc-panel-row">
            <span>Решение</span>
            <b>{scouts.find((scout) => scout.id === assignScoutId)?.judgement ?? 0} / 5</b>
          </div>
        </div>

        <button class="sc-wide-action" data-nav onclick={nextAssignStep}>
          <span>{view === 'region' ? 'Далее' : 'Организовать сеть'}</span>
          <span class="sc-key">A</span>
        </button>
      </aside>
    </div>

  {:else if view === 'task'}
    <div class="sc-body sc-task-edit">
      <section class="sc-task-grid">
        <button
          class="sc-task-cell"
          class:is-editing={taskField === 'role'}
          data-nav
          data-autofocus
          data-edit={taskField === 'role' ? 'true' : undefined}
          onclick={() => selectTaskField('role')}
        >
          <span class="sc-task-cell-label">Позиция</span>
          <strong>{roleLabel(taskDraft?.role)}</strong>
          <span class="sc-task-cell-hint">A — выбор позиции</span>
        </button>
        <button class="sc-task-cell is-disabled" aria-disabled="true" disabled>
          <span class="sc-task-cell-label">Особенности</span>
          <strong>Любой</strong>
          <span class="sc-task-cell-hint">Пока не настраивается</span>
        </button>
        <button
          class="sc-task-cell"
          class:is-editing={taskField === 'contract'}
          data-nav
          data-edit={taskField === 'contract' ? 'true' : undefined}
          onclick={() => selectTaskField('contract')}
        >
          <span class="sc-task-cell-label">Контракт</span>
          <strong>{rangeLabel(taskDraft?.contract_min ?? null, taskDraft?.contract_max ?? null)}</strong>
          <span class="sc-task-cell-hint">Срок, лет</span>
        </button>
        <button
          class="sc-task-cell"
          class:is-editing={taskField === 'age'}
          data-nav
          data-edit={taskField === 'age' ? 'true' : undefined}
          onclick={() => selectTaskField('age')}
        >
          <span class="sc-task-cell-label">Лет</span>
          <strong>{rangeLabel(taskDraft?.age_min ?? null, taskDraft?.age_max ?? null)}</strong>
          <span class="sc-task-cell-hint">Возраст</span>
        </button>
      </section>

      <aside class="sc-panel scroll-area" aria-label="Подробности задачи">
        <div class="sc-panel-title">Подробности</div>
        <div class="sc-panel-stats">
          <span>Найдены игроки <b>{activeTask?.found_count ?? 0}</b></span>
          <span>Дней работы скаута <b>{activeTask?.days_worked ?? 0}</b></span>
        </div>
        <div class="sc-pitch">
          <span class="sc-pitch-zone {pitchZone(taskDraft?.role)}"></span>
          <span class="sc-pitch-line halfway"></span>
          <span class="sc-pitch-circle"></span>
          <span class="sc-pitch-box top"></span>
          <span class="sc-pitch-box bottom"></span>
        </div>
        <div class="sc-panel-section">
          <div class="sc-panel-row"><span>Скаут</span><b>{taskScout?.name}</b></div>
          <div class="sc-panel-row"><span>Регион</span><b>{activeTask?.region_name}</b></div>
          <div class="sc-panel-row"><span>Страна</span><b>{activeTask?.country_name}</b></div>
          <div class="sc-panel-muted">{criteriaLine(taskDraft)}</div>
        </div>
        <button
          class="sc-wide-action"
          data-nav
          onclick={async () => {
            await saveTask()
            openReports('recommendations', null, taskScout?.id, 'tasks')
          }}
        >
          <span>Список найденных игроков</span>
          <span class="sc-key">A</span>
        </button>
      </aside>
    </div>

  {:else if view === 'reports'}
    <div class="sc-body sc-reports">
      <section class="sc-report-main" inert={entryActionsOpen ? true : undefined}>
        <div class="sc-report-tabs">
          <button
            class="sc-tab"
            class:is-active={reportTab === 'recommendations'}
            data-nav
            onclick={() => {
              reportTab = 'recommendations'
              selectedEntryId = null
              tick().then(focusFirst)
            }}
          >
            Рекомендации
          </button>
          <button
            class="sc-tab"
            class:is-active={reportTab === 'requests'}
            data-nav
            onclick={() => {
              reportTab = 'requests'
              selectedEntryId = null
              tick().then(focusFirst)
            }}
          >
            Отчёты по запросу
          </button>
        </div>
        <div class="sc-role-tabs">
          {#each ROLE_FILTERS as filter (filter.id)}
            <button
              class="sc-role-tab"
              class:is-active={roleFilter === filter.id}
              data-nav
              onclick={() => {
                roleFilter = filter.id
                selectedEntryId = null
                tick().then(focusFirst)
              }}
            >
              {filter.label}
            </button>
          {/each}
          {#if scoutFilter}
            <span class="sc-filter-note">{scoutName(scoutFilter)}</span>
          {/if}
        </div>

        <div class="sc-entry-list scroll-area" data-nav-grid>
          {#each entries as entry, index (entry.player.id)}
            <button
              class="sc-entry"
              class:is-selected={selectedEntry?.player.id === entry.player.id}
              data-nav
              data-entry={entry.player.id}
              data-autofocus={index === 0 ? '' : undefined}
              onfocus={() => (selectedEntryId = entry.player.id)}
              onclick={() => {
                selectedEntryId = entry.player.id
                openEntryActions(entry)
              }}
            >
              <span
                class="sc-entry-photo"
                class:is-empty={!entry.player.photo || failedPhotos[entry.player.id]}
              >
                {#if !entry.player.photo || failedPhotos[entry.player.id]}
                  <span class="sc-entry-photo-fallback">
                    <Icon name="users" size={24} />
                  </span>
                {:else}
                  <img
                    src={entry.player.photo}
                    alt=""
                    onerror={() => (failedPhotos[entry.player.id] = true)}
                  />
                {/if}
              </span>
              <span class="sc-entry-main">
                <strong>{entry.player.name}</strong>
                <span class="sc-entry-meta">
                  {entry.player.age ?? '—'}
                  {plural(entry.player.age ?? 0, 'год', 'года', 'лет')}
                  <i class="pos-badge {posTone(entry.player.role)}">
                    {shortRole(entry.player.role)}
                  </i>
                </span>
              </span>
              <span class="sc-entry-side">
                {#if !entry.acknowledged}<i class="sc-new" title="Новый"></i>{/if}
                <b class="sc-entry-ovr">{Math.round(entry.player.overall ?? 0)}</b>
                {#if entry.player.club_logo}
                  <img
                    class="sc-entry-crest"
                    src={entry.player.club_logo}
                    alt=""
                    onerror={hideBrokenImage}
                  />
                {/if}
              </span>
            </button>
          {/each}
          {#if !entries.length}
            <div class="sc-empty">
              {#if reportTab === 'recommendations'}
                <p>Скауты пока ничего не рекомендуют.</p>
                <span>
                  Создайте сеть поиска в стране, и скаут начнёт присылать игроков.
                </span>
              {:else}
                <p>Отчётов по запросу пока нет.</p>
                <span>
                  Откройте карточку игрока в поиске и выберите «Поручить скауту».
                </span>
              {/if}
            </div>
          {/if}
        </div>
      </section>

      <aside class="sc-report-detail" inert={entryActionsOpen ? true : undefined}>
        {#if selectedEntry}
          {@const player = selectedEntry.player}
          <div class="sc-report-top">
            <span
              class="sc-report-photo"
              class:is-empty={!player.photo || failedPhotos[player.id]}
            >
              {#if !player.photo || failedPhotos[player.id]}
                <span class="sc-entry-photo-fallback">
                  <Icon name="users" size={36} />
                </span>
              {:else}
                <img
                  src={player.photo}
                  alt=""
                  onerror={() => (failedPhotos[player.id] = true)}
                />
              {/if}
            </span>
            <div class="sc-report-info">
              {#if !selectedEntry.acknowledged}
                <span class="sc-report-badge">Новый</span>
              {:else if selectedEntry.kind === 'recommendation'}
                <span class="sc-report-badge is-soft">Рекомендация</span>
              {:else}
                <span class="sc-report-badge is-soft">Отчёт</span>
              {/if}
              <strong class="sc-report-name">{player.name}</strong>
              <div class="sc-report-facts">
                <span>Лет <b>{player.age ?? '—'}</b></span>
                <span>Амплуа <b>{shortRole(player.role)}</b></span>
                <span>Рост <b>{player.height ? `${player.height} см` : '—'}</b></span>
                <span>Нога <b>{footLabel(player.foot)}</b></span>
              </div>
              <div class="sc-report-traits">
                {positionLabel(player.position)}
              </div>
            </div>
            <span class="sc-report-club">
              {#if player.club_logo}
                <img src={player.club_logo} alt="" onerror={hideBrokenImage} />
              {/if}
              <span>{player.club_name ?? 'Свободный агент'}</span>
            </span>
          </div>

          <div class="sc-report-ovr">
            <span>ОБЩ.</span>
            <strong class={statTone(player.overall ?? 0)}>
              {Math.round(player.overall ?? 0)}
            </strong>
            <span>ПОТ. <b class={statTone(player.pot ?? 0)}>{player.pot ?? '—'}</b></span>
          </div>

          <div class="sc-report-traits-center">
            <div class="sc-trait-item">
              <span>Слабая нога</span>
              <b class="sc-trait-stars">
                {#each [0, 1, 2, 3, 4] as star (star)}
                  <i class:on={star < (player.weak_foot ?? 0)}>★</i>
                {/each}
              </b>
            </div>
            <div class="sc-trait-item">
              <span>Финты</span>
              <b class="sc-trait-stars">
                {#each [0, 1, 2, 3, 4] as star (star)}
                  <i class:on={star < (player.skill_moves ?? 0)}>★</i>
                {/each}
              </b>
            </div>
          </div>

          <div class="sc-report-grid">
            <div class="sc-report-column">
              <div class="sc-report-head">Финансы</div>
              <div class="sc-money-list">
                <div>
                  <span>Зарплата</span>
                  <b>{formatValue(player.weekly_wage ?? 0)} <small>/ нед.</small></b>
                </div>
                <div>
                  <span>Стоимость</span>
                  <b>{formatValue(player.market_value ?? 0)}</b>
                </div>
                <div>
                  <span>Отступные</span>
                  <b class="is-accent">{formatValue(player.release_clause ?? 0)}</b>
                </div>
              </div>
            </div>
            <div class="sc-report-column">
              <div class="sc-report-head">Сводка</div>
              <ul class="sc-stat-list">
                {#each playerStatRows(player) as row (row.key)}
                  <li>
                    <span>{row.label}</span>
                    <b class={statTone(row.value)}>{row.value}</b>
                  </li>
                {/each}
              </ul>
            </div>
          </div>

          <div class="sc-report-foot">
            <span>
              <Icon name="check" size={14} />
              {selectedEntry.kind === 'report' ? 'Отчёт готов' : 'Игрок изучен'}
              · {selectedEntry.scout_name} · {formatDate(selectedEntry.date)}
            </span>
          </div>
        {:else}
          <p class="sc-panel-muted">Выберите игрока в списке.</p>
        {/if}
      </aside>
    </div>
  {/if}

  {#if entryActionsOpen && entryActionsEntry}
    <PlayerActionsModal
      player={entryActionsEntry.player}
      revealed
      shortlisted={Boolean(entryActionsEntry.player.shortlisted)}
      removeLabel="Удалить из отчёта"
      onremove={removeActiveEntry}
      onshortlist={() => toggleShortlist(entryActionsEntry.player)}
    />
  {/if}

  {#if confirm}
    <div class="sc-modal-layer">
      <div class="sc-modal sc-confirm" role="dialog" aria-modal="true">
        <p class="sc-confirm-text">{confirm.title}</p>
        <button
          class="sc-confirm-row is-selected"
          data-nav
          data-autofocus
          onclick={() => confirm.action()}
        >
          <span class="sc-key">A</span>
          <span>{confirm.yes}</span>
        </button>
        <button class="sc-confirm-row" data-nav onclick={() => (confirm = null)}>
          <span>{confirm.no}</span>
        </button>
      </div>
    </div>
  {/if}
</div>
