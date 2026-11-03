import { tick } from 'svelte'

import { api } from '../../api.js'
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
import { ROLE_GROUP, TASK_ROLES } from '../constants/scouting.js'

export function createScoutingState(ctx) {
  const {
    getCareer,
    getMode,
    getBackToHub,
    getInitialEntryId,
    onclose,
    onaction,
    focusFirst,
  } = ctx

    let scouting = $derived(getCareer().scouting ?? null)
    let scouts = $derived(scouting?.scouts ?? [])
    let candidates = $derived(scouting?.candidates ?? [])
    let regions = $derived(scouting?.regions ?? [])
    let networks = $derived(scouting?.networks ?? [])
    let counts = $derived(scouting?.counts ?? { new: 0, updates: 0, total: 0 })
    let maxScouts = $derived(scouting?.max_scouts ?? 6)
    let balance = $derived(getCareer().squad?.finance?.balance ?? 0)

    let view = $state(getMode() === 'reports' ? 'reports' : getMode() === 'tasks' ? 'tasks' : 'scouts')
    let networkTab = $state(getMode() === 'tasks' ? 'tasks' : 'scouts')
    let reportTab = $state('requests')
    let reportsReturn = $state(getBackToHub() ? 'close' : 'scouts')
    let selectedScoutId = $state(null)
    let selectedTaskScoutId = $state(null)
    let selectedEntryId = $state(getInitialEntryId())
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
      if (initialResolved || !getInitialEntryId()) return
      const requests = (scouting?.reports ?? []).some(
        (entry) => entry.player.id === getInitialEntryId(),
      )
      const recommendations = (scouting?.recommendations ?? []).some(
        (entry) => entry.player.id === getInitialEntryId(),
      )
      if (!requests && recommendations) reportTab = 'recommendations'
      selectedEntryId = getInitialEntryId()
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


  return {
    get view() {
      return view
    },
    set view(value) {
      view = value
    },
    get networkTab() {
      return networkTab
    },
    set networkTab(value) {
      networkTab = value
    },
    get reportTab() {
      return reportTab
    },
    set reportTab(value) {
      reportTab = value
    },
    get reportsReturn() {
      return reportsReturn
    },
    set reportsReturn(value) {
      reportsReturn = value
    },
    get selectedScoutId() {
      return selectedScoutId
    },
    set selectedScoutId(value) {
      selectedScoutId = value
    },
    get selectedTaskScoutId() {
      return selectedTaskScoutId
    },
    set selectedTaskScoutId(value) {
      selectedTaskScoutId = value
    },
    get selectedEntryId() {
      return selectedEntryId
    },
    set selectedEntryId(value) {
      selectedEntryId = value
    },
    get scoutFilter() {
      return scoutFilter
    },
    set scoutFilter(value) {
      scoutFilter = value
    },
    get roleFilter() {
      return roleFilter
    },
    set roleFilter(value) {
      roleFilter = value
    },
    get hireId() {
      return hireId
    },
    set hireId(value) {
      hireId = value
    },
    get confirm() {
      return confirm
    },
    set confirm(value) {
      confirm = value
    },
    get error() {
      return error
    },
    set error(value) {
      error = value
    },
    get busy() {
      return busy
    },
    set busy(value) {
      busy = value
    },
    get acked() {
      return acked
    },
    set acked(value) {
      acked = value
    },
    get initialResolved() {
      return initialResolved
    },
    set initialResolved(value) {
      initialResolved = value
    },
    get failedPhotos() {
      return failedPhotos
    },
    set failedPhotos(value) {
      failedPhotos = value
    },
    get entryActionsOpen() {
      return entryActionsOpen
    },
    set entryActionsOpen(value) {
      entryActionsOpen = value
    },
    get entryActionsId() {
      return entryActionsId
    },
    set entryActionsId(value) {
      entryActionsId = value
    },
    get assignScoutId() {
      return assignScoutId
    },
    set assignScoutId(value) {
      assignScoutId = value
    },
    get regionId() {
      return regionId
    },
    set regionId(value) {
      regionId = value
    },
    get countryId() {
      return countryId
    },
    set countryId(value) {
      countryId = value
    },
    get countryLeagues() {
      return countryLeagues
    },
    set countryLeagues(value) {
      countryLeagues = value
    },
    get taskScoutId() {
      return taskScoutId
    },
    set taskScoutId(value) {
      taskScoutId = value
    },
    get taskField() {
      return taskField
    },
    set taskField(value) {
      taskField = value
    },
    get taskRangeRow() {
      return taskRangeRow
    },
    set taskRangeRow(value) {
      taskRangeRow = value
    },
    get taskDraft() {
      return taskDraft
    },
    set taskDraft(value) {
      taskDraft = value
    },
    get taskSaved() {
      return taskSaved
    },
    set taskSaved(value) {
      taskSaved = value
    },
    get scouting() {
      return scouting
    },
    get scouts() {
      return scouts
    },
    get candidates() {
      return candidates
    },
    get regions() {
      return regions
    },
    get networks() {
      return networks
    },
    get counts() {
      return counts
    },
    get maxScouts() {
      return maxScouts
    },
    get balance() {
      return balance
    },
    get selectedScout() {
      return selectedScout
    },
    get selectedTaskScout() {
      return selectedTaskScout
    },
    get region() {
      return region
    },
    get country() {
      return country
    },
    get hireCandidate() {
      return hireCandidate
    },
    get entrySource() {
      return entrySource
    },
    get entries() {
      return entries
    },
    get selectedEntry() {
      return selectedEntry
    },
    get entryActionsEntry() {
      return entryActionsEntry
    },
    get taskScout() {
      return taskScout
    },
    get emptySlots() {
      return emptySlots
    },
    get activeTask() {
      return activeTask
    },
    get hintList() {
      return hintList
    },
    get hints() {
      return hintList
    },
    go,
    openReports,
    openScout,
    startAssign,
    openHire,
    openTask,
    defaultCriteria,
    footLabel,
    roleLabel,
    rangeLabel,
    criteriaLine,
    taskTitle,
    taskSubtitle,
    scoutStatus,
    playerStatRows,
    pitchZone,
    countryPosition,
    openEntryActions,
    closeEntryActions,
    removeActiveEntry,
    toggleShortlist,
    cycleReport,
    cycleScout,
    handleTabs,
    handleCycle,
    handleBack,
    handlePrimary,
    handleReset,
    handleStep,
    stepRole,
    stepTaskRange,
    selectTaskField,
    runAction,
    saveTask,
    confirmHire,
    confirmNetwork,
    askHire,
    askNetwork,
    nextAssignStep,
    scoutName,
  }
}
