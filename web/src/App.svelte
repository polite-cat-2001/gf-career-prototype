<script>
  import { onMount } from 'svelte'
  import { api } from './lib/api.js'
  import { initInput } from './lib/input.js'
  import StartScreen from './lib/StartScreen.svelte'
  import LoadScreen from './lib/LoadScreen.svelte'
  import NewCareer from './lib/NewCareer.svelte'
  import Hub from './lib/Hub.svelte'

  let screen = $state('start')
  let saves = $state([])
  let savesLoading = $state(true)
  let savesError = $state('')
  let career = $state(null)
  let saving = $state(false)
  let playing = $state(false)
  let saveError = $state('')

  let latest = $derived(saves.find((save) => save.compatible) ?? null)

  onMount(() => {
    const stopInput = initInput()
    refreshSaves()
    return stopInput
  })

  async function refreshSaves() {
    savesLoading = true
    savesError = ''
    try {
      saves = await api.careers()
    } catch (caught) {
      savesError = `Не удалось загрузить сохранения: ${caught.message}`
    } finally {
      savesLoading = false
    }
  }

  async function continueLatest() {
    savesError = ''
    try {
      career = await api.latestCareer()
      openHub()
    } catch (caught) {
      savesError = `Не удалось продолжить карьеру: ${caught.message}`
      refreshSaves()
    }
  }

  async function loadCareer(careerId) {
    savesError = ''
    try {
      career = await api.career(careerId)
      openHub()
    } catch (caught) {
      savesError = `Не удалось загрузить карьеру: ${caught.message}`
    }
  }

  function openHub() {
    saveError = ''
    screen = 'hub'
    refreshSaves()
  }

  function showStart() {
    screen = 'start'
    savesError = ''
  }

  function showLoad() {
    savesError = ''
    screen = 'load'
  }

  function startNew() {
    savesError = ''
    screen = 'new'
  }

  function careerCreated(snapshot) {
    career = snapshot
    openHub()
  }

  async function saveCareer() {
    if (!career || saving) return
    saving = true
    saveError = ''
    try {
      career = await api.saveCareer(career.id)
      refreshSaves()
    } catch (caught) {
      saveError = `Не удалось сохранить: ${caught.message}`
    } finally {
      saving = false
    }
  }

  async function swapPlayers(playerA, playerB) {
    if (!career) return null
    saveError = ''
    try {
      career = await api.swapPlayers(career.id, playerA, playerB)
      refreshSaves()
      return career
    } catch (caught) {
      saveError = `Не удалось изменить состав: ${caught.message}`
      return null
    }
  }

  async function playMatch() {
    if (!career || playing) return null
    playing = true
    saveError = ''
    try {
      career = await api.playMatch(career.id)
      refreshSaves()
      return career
    } catch (caught) {
      saveError = `Не удалось сыграть матч: ${caught.message}`
      return null
    } finally {
      playing = false
    }
  }

  async function advanceCareer(date) {
    if (!career) return null
    saveError = ''
    try {
      career = await api.advanceCareer(career.id, date)
      return career
    } catch (caught) {
      saveError = `Не удалось перемотать календарь: ${caught.message}`
      return null
    }
  }

  async function previewSimulation() {
    if (!career) return null
    saveError = ''
    try {
      return await api.matchPreview(career.id)
    } catch (caught) {
      saveError = `Не удалось открыть симуляцию: ${caught.message}`
      return null
    }
  }

  async function simulateMatch() {
    if (!career) return null
    saveError = ''
    try {
      const payload = await api.simulateMatch(career.id)
      career = payload.career
      refreshSaves()
      return payload.match
    } catch (caught) {
      saveError = `Не удалось симулировать матч: ${caught.message}`
      return null
    }
  }

  async function startNextSeason() {
    if (!career) return null
    saveError = ''
    try {
      career = await api.nextSeason(career.id)
      refreshSaves()
      return career
    } catch (caught) {
      saveError = `Не удалось начать новый сезон: ${caught.message}`
      return null
    }
  }

  async function runSquadAction(payload) {
    if (!career) return null
    saveError = ''
    try {
      career = await api.careerAction(career.id, payload)
      refreshSaves()
      return career
    } catch (caught) {
      saveError = `Не удалось выполнить действие: ${caught.message}`
      return null
    }
  }

  async function exitToMenu() {
    screen = 'start'
    career = null
    await refreshSaves()
  }
</script>

{#if screen === 'start'}
  <StartScreen
    {latest}
    savesCount={saves.length}
    loading={savesLoading}
    error={savesError}
    oncontinue={continueLatest}
    onnew={startNew}
    onload={showLoad}
  />
{:else if screen === 'load'}
  <LoadScreen
    {saves}
    error={savesError}
    onload={loadCareer}
    onback={showStart}
  />
{:else if screen === 'new'}
  <NewCareer oncreated={careerCreated} onback={showStart} />
{:else if screen === 'hub' && career}
  <Hub
    {career}
    {saving}
    {playing}
    {saveError}
    onsave={saveCareer}
    onswap={swapPlayers}
    onplay={playMatch}
    onpreview={previewSimulation}
    onsimulate={simulateMatch}
    onadvance={advanceCareer}
    onnextseason={startNextSeason}
    onaction={runSquadAction}
    onexit={exitToMenu}
  />
{/if}
