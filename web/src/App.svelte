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
  let saveNotice = $state('')
  let saveError = $state('')
  let noticeTimer = null

  let latest = $derived(saves.find((save) => save.compatible) ?? null)

  onMount(() => {
    const stopInput = initInput()
    refreshSaves()
    return stopInput
  })

  function announce(text) {
    saveNotice = text
    clearTimeout(noticeTimer)
    noticeTimer = setTimeout(() => {
      saveNotice = ''
    }, 2800)
  }

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
    saveNotice = ''
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
    announce('Карьера создана и сохранена')
  }

  async function saveCareer() {
    if (!career || saving) return
    saving = true
    saveError = ''
    saveNotice = ''
    try {
      career = await api.saveCareer(career.id)
      announce('Сохранено вручную')
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
      announce('Состав обновлён и сохранён')
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

  async function startNextSeason() {
    if (!career) return null
    saveError = ''
    try {
      career = await api.nextSeason(career.id)
      announce('Начат новый сезон')
      refreshSaves()
      return career
    } catch (caught) {
      saveError = `Не удалось начать новый сезон: ${caught.message}`
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
    {saveNotice}
    {saveError}
    onsave={saveCareer}
    onswap={swapPlayers}
    onplay={playMatch}
    onadvance={advanceCareer}
    onnextseason={startNextSeason}
    onexit={exitToMenu}
  />
{/if}
