<script>
  import { onMount, tick } from 'svelte'
  import { api } from './api.js'
  import { registerBack, registerCycle } from './actions.js'
  import Controls from './Controls.svelte'
  import { focusFirst, inputDevice } from './input.js'
  import { formatValue, hideBrokenImage, tierLabel } from './format.js'

  let { oncreated, onback } = $props()

  let meta = $state(null)
  let countries = $state([])
  let leagues = $state([])
  let clubs = $state([])
  let selectedClub = $state(null)
  let squad = $state([])
  let step = $state('country')

  let selectedCountryId = $state(null)
  let selectedLeagueId = $state(null)
  let selectedClubId = $state(null)

  let managerName = $state('')
  let nationalityId = $state('')
  let nationalityTouched = $state(false)

  let loadingCountries = $state(true)
  let loadingLeagues = $state(false)
  let loadingClub = $state(false)
  let creating = $state(false)
  let error = $state('')

  let leagueToken = 0
  let clubsToken = 0
  let detailToken = 0

  let selectedCountry = $derived(countries.find((item) => item.id === selectedCountryId) ?? null)
  let selectedLeague = $derived(leagues.find((item) => item.id === selectedLeagueId) ?? null)
  let nationality = $derived(countries.find((item) => item.id === nationalityId) ?? null)
  let clubIndex = $derived(clubs.findIndex((club) => club.id === selectedClubId))
  let summary = $derived.by(() => {
    if (!squad.length) return null
    const totalValue = squad.reduce((sum, player) => sum + player.market_value, 0)
    const average = squad.reduce((sum, player) => sum + player.overall, 0) / squad.length
    return { totalValue, average: Math.round(average * 10) / 10 }
  })
  let canCreate = $derived(Boolean(managerName.trim() && nationalityId && !creating))
  let confirmKey = $derived($inputDevice === 'gamepad' ? 'A' : 'Enter')

  onMount(() => {
    const stopBack = registerBack(handleBack)
    const stopCycle = registerCycle(handleCycle)
    loadCanon()
    return () => {
      stopBack()
      stopCycle()
    }
  })

  async function loadCanon() {
    try {
      const [metaData, countryData] = await Promise.all([api.meta(), api.countries()])
      meta = metaData
      countries = countryData
    } catch (caught) {
      error = `Не удалось загрузить канон: ${caught.message}`
    } finally {
      loadingCountries = false
      await tick()
      focusFirst()
    }
  }

  async function go(next) {
    step = next
    error = ''
    await tick()
    focusFirst()
  }

  function handleBack() {
    if (step === 'nationality') go('manager')
    else if (step === 'manager') go('club')
    else if (step === 'club') go('league')
    else if (step === 'league') go('country')
    else onback()
  }

  function handleCycle(direction) {
    if (step !== 'club' || clubs.length < 2) return
    const current = clubIndex < 0 ? 0 : clubIndex
    const next = (current + (direction === 'right' ? 1 : -1) + clubs.length) % clubs.length
    chooseClub(clubs[next], false)
  }

  async function chooseCountry(country) {
    selectedCountryId = country.id
    selectedLeagueId = null
    selectedClubId = null
    selectedClub = null
    leagues = []
    clubs = []
    squad = []
    error = ''

    const token = ++leagueToken
    loadingLeagues = true
    try {
      const data = await api.leagues(country.id)
      if (token !== leagueToken) return
      leagues = data
      await go('league')
    } catch (caught) {
      if (token === leagueToken) error = `Не удалось загрузить лиги: ${caught.message}`
    } finally {
      if (token === leagueToken) loadingLeagues = false
    }
  }

  async function chooseLeague(league) {
    selectedLeagueId = league.id
    selectedClubId = null
    selectedClub = null
    clubs = []
    squad = []
    error = ''

    const token = ++clubsToken
    try {
      const data = await api.clubs(league.id)
      if (token !== clubsToken) return
      clubs = data
      if (data.length) {
        await chooseClub(data[0], false)
      }
      await go('club')
    } catch (caught) {
      if (token === clubsToken) error = `Не удалось загрузить клубы: ${caught.message}`
    } finally {
    }
  }

  async function chooseClub(club, focusAfter = false) {
    selectedClubId = club.id
    selectedClub = club
    squad = []
    error = ''
    if (!nationalityTouched) nationalityId = club.country_id

    const token = ++detailToken
    loadingClub = true
    try {
      const [clubData, squadData] = await Promise.all([api.club(club.id), api.squad(club.id)])
      if (token !== detailToken) return
      selectedClub = clubData
      squad = squadData
      if (focusAfter) {
        await tick()
        focusFirst()
      }
    } catch (caught) {
      if (token === detailToken) error = `Не удалось загрузить клуб: ${caught.message}`
    } finally {
      if (token === detailToken) loadingClub = false
    }
  }

  function chooseNationality(country) {
    nationalityId = country.id
    nationalityTouched = true
    go('manager')
  }

  async function createCareer() {
    if (!canCreate) return
    creating = true
    error = ''
    try {
      const snapshot = await api.createCareer({
        club_id: selectedClubId,
        manager_name: managerName.trim(),
        manager_nationality_id: nationalityId,
      })
      oncreated(snapshot)
    } catch (caught) {
      error = `Не удалось создать карьеру: ${caught.message}`
    } finally {
      creating = false
    }
  }
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Новая карьера</div>
        <div class="brand-sub">
          {#if step === 'country'}Страна
          {:else if step === 'league'}Лига
          {:else if step === 'club'}Клуб
          {:else if step === 'manager'}Менеджер
          {:else}Гражданство{/if}
        </div>
      </div>
    </div>
    <div class="topbar-meta">
      {#if meta}
        <span class="pill"><strong>{meta.counts.clubs}</strong> клубов</span>
        <span class="pill"><strong>{meta.counts.leagues}</strong> лиг</span>
      {/if}
      {#if selectedCountry}<span class="pill">{selectedCountry.name}</span>{/if}
      {#if selectedLeague}<span class="pill">{selectedLeague.name}</span>{/if}
      {#if selectedClub}<span class="pill">{selectedClub.name}</span>{/if}
    </div>
  </header>

  <main class="screen creation-screen">
    {#if error}
      <div class="notice error">{error}</div>
    {/if}

    {#if step === 'country'}
      <div class="picker-head">
        <span class="eyebrow">Шаг 1 из 4</span>
        <h1>Выберите страну</h1>
        <p>От страны зависит набор лиг и клубов.</p>
      </div>

      {#if loadingCountries}
        <div class="skeleton">
          {#each Array(8) as _}<div class="skeleton-line"></div>{/each}
        </div>
      {:else}
        <div class="country-grid">
          {#each countries as country, index (country.id)}
            <button
              class="country-tile"
              data-nav
              data-autofocus={index === 0 ? '' : undefined}
              onclick={() => chooseCountry(country)}
            >
              <img src={country.flag} alt="" loading="lazy" onerror={hideBrokenImage} />
              <span class="country-name">{country.name}</span>
              <span class="country-meta">{country.leagues_count} лиг · {country.clubs_count} клубов</span>
            </button>
          {/each}
        </div>
      {/if}
    {:else if step === 'league'}
      <div class="picker-head">
        <span class="eyebrow">Шаг 2 из 4 · {selectedCountry?.name}</span>
        <h1>Выберите лигу</h1>
        <p>Все клубы лиги доступны сразу.</p>
      </div>

      {#if loadingLeagues}
        <div class="skeleton">
          {#each Array(5) as _}<div class="skeleton-line"></div>{/each}
        </div>
      {:else}
        <div class="big-list">
          {#each leagues as league, index (league.id)}
            <button
              class="big-row"
              data-nav
              data-autofocus={index === 0 ? '' : undefined}
              onclick={() => chooseLeague(league)}
            >
              <img class="row-crest" src={league.logo} alt="" loading="lazy" onerror={hideBrokenImage} />
              <span class="big-row-main">
                <span class="big-row-title">{league.name}</span>
                <span class="big-row-sub">{league.clubs_count} клубов</span>
              </span>
              <span class="pill tier">{tierLabel(league)}</span>
            </button>
          {/each}
        </div>
      {/if}
    {:else if step === 'club'}
      <div class="picker-head">
        <span class="eyebrow">Шаг 3 из 4 · {selectedLeague?.name}</span>
        <h1>Выберите клуб</h1>
        <p>Крупный выбранный клуб и его сводка. <kbd>←</kbd> <kbd>→</kbd> меняют клуб.</p>
      </div>

      {#if !clubs.length || !selectedClub}
        <div class="skeleton">
          {#each Array(5) as _}<div class="skeleton-line"></div>{/each}
        </div>
      {:else}
        <div class="club-picker">
          <button
            class="club-focus-card"
            data-nav
            data-cycle="club"
            data-autofocus
            onclick={() => go('manager')}
          >
            <span class="club-focus-head">
              <span class="cycle-arrow">←</span>
              <span class="club-focus-index">{clubIndex + 1} / {clubs.length}</span>
              <span class="cycle-arrow">→</span>
            </span>
            <img class="club-focus-crest" src={selectedClub.logo} alt="" onerror={hideBrokenImage} />
            <span class="club-focus-name">{selectedClub.name}</span>
            <span class="club-focus-meta">{tierLabel(selectedClub)} · {selectedClub.league_name}</span>
            <span class="club-focus-action">{confirmKey} · выбрать клуб</span>
          </button>

          <div class="club-details">
            <div class="detail-card">
              <span class="detail-label">Стадион</span>
              <strong>{selectedClub.stadium.name || '—'}</strong>
              <span>{selectedClub.stadium.seats ? `${selectedClub.stadium.seats} мест` : 'Вместимость неизвестна'}</span>
            </div>
            <div class="detail-card">
              <span class="detail-label">Состав</span>
              <strong>{loadingClub ? '…' : `${squad.length} игроков`}</strong>
              <span>{summary ? `Средний OVR ${summary.average}` : 'Загрузка'}</span>
            </div>
            <div class="detail-card">
              <span class="detail-label">Стоимость состава</span>
              <strong>{summary ? formatValue(summary.totalValue) : '—'}</strong>
              <span>по данным канона</span>
            </div>
            <div class="detail-card">
              <span class="detail-label">Страна</span>
              <strong>{selectedClub.country_name}</strong>
              <span>{selectedClub.league_name}</span>
            </div>
            <div class="detail-card wide">
              <span class="detail-label">Основан</span>
              <strong>{selectedClub.founded_on ? selectedClub.founded_on.slice(0, 4) : '—'}</strong>
              <span>Домашний стадион: {selectedClub.stadium.name || '—'}</span>
            </div>
          </div>
        </div>
      {/if}
    {:else if step === 'manager'}
      <div class="picker-head">
        <span class="eyebrow">Шаг 4 из 4 · {selectedClub?.name}</span>
        <h1>Менеджер</h1>
        <p>Имя и гражданство создают вашего менеджера. Seed выбирается случайно.</p>
      </div>

      <div class="manager-layout">
        <form class="manager-card" onsubmit={(event) => { event.preventDefault(); createCareer() }}>
          <label class="field">
            <span>Имя менеджера</span>
            <input
              class="text-input"
              data-nav
              data-autofocus
              bind:value={managerName}
              maxlength="80"
              placeholder="Например, Алексей Смирнов"
              autocomplete="off"
            />
          </label>

          <button class="choice-card" data-nav type="button" onclick={() => go('nationality')}>
            <span class="choice-label">Гражданство</span>
            <span class="choice-value">{nationality?.name || 'Выберите страну'}</span>
            {#if nationality}
              <img class="choice-flag" src={nationality.flag} alt="" onerror={hideBrokenImage} />
            {/if}
          </button>

          <button class="primary-action" data-nav type="submit" disabled={!canCreate}>
            {creating ? 'Создаём карьеру…' : 'Начать карьеру'}
          </button>
          {#if !managerName.trim() || !nationalityId}
            <p class="field-hint">Введите имя и выберите гражданство.</p>
          {/if}
        </form>

        <aside class="manager-recap">
          <img class="club-focus-crest small" src={selectedClub?.logo} alt="" onerror={hideBrokenImage} />
          <div>
            <span class="detail-label">Ваш клуб</span>
            <strong>{selectedClub?.name}</strong>
            <span>{selectedClub?.league_name} · {selectedClub?.country_name}</span>
          </div>
          <div class="recap-row">
            <span>Состав</span>
            <strong>{squad.length}</strong>
          </div>
          <div class="recap-row">
            <span>Средний OVR</span>
            <strong>{summary?.average ?? '—'}</strong>
          </div>
          <div class="recap-row">
            <span>Стоимость</span>
            <strong>{summary ? formatValue(summary.totalValue) : '—'}</strong>
          </div>
          <div class="recap-row">
            <span>Seed</span>
            <strong>случайный</strong>
          </div>
        </aside>
      </div>
    {:else if step === 'nationality'}
      <div class="picker-head">
        <span class="eyebrow">Менеджер · гражданство</span>
        <h1>Выберите гражданство</h1>
        <p>Список стран канона. <kbd>B</kbd>/<kbd>Esc</kbd> — назад.</p>
      </div>

      <div class="country-grid">
        {#each countries as country, index (country.id)}
          <button
            class="country-tile"
            data-nav
            data-autofocus={index === 0 ? '' : undefined}
            onclick={() => chooseNationality(country)}
          >
            <img src={country.flag} alt="" loading="lazy" onerror={hideBrokenImage} />
            <span class="country-name">{country.name}</span>
            <span class="country-meta">{country.leagues_count} лиг · {country.clubs_count} клубов</span>
          </button>
        {/each}
      </div>
    {/if}
  </main>

  <Controls
    hints={step === 'club' ? [{ gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Сменить клуб' }] : []}
    note={selectedClub ? `${selectedClub.name} · ${selectedClub.league_name}` : 'Выбор из canon.db'}
  />
</div>
