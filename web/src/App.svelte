<script>
  import { onMount } from 'svelte'
  import { api } from './lib/api.js'

  const ROLE_ORDER = ['GK', 'CB', 'LB', 'RB', 'DM', 'CM', 'LM', 'RM', 'AM', 'CF']
  const ROLE_LABELS = {
    GK: 'Вратари',
    CB: 'Центральные защитники',
    LB: 'Левые защитники',
    RB: 'Правые защитники',
    DM: 'Опорные полузащитники',
    CM: 'Центральные полузащитники',
    LM: 'Левые полузащитники',
    RM: 'Правые полузащитники',
    AM: 'Атакующие полузащитники',
    CF: 'Нападающие',
  }

  let meta = $state(null)
  let countries = $state([])
  let leagues = $state([])
  let clubs = $state([])
  let selectedClub = $state(null)
  let squad = $state([])

  let selectedCountryId = $state(null)
  let selectedLeagueId = $state(null)
  let selectedClubId = $state(null)

  let countryQuery = $state('')
  let loadingCountries = $state(true)
  let loadingLeagues = $state(false)
  let loadingClubs = $state(false)
  let loadingSquad = $state(false)
  let error = $state('')

  let leagueToken = 0
  let clubToken = 0
  let squadToken = 0

  let selectedCountry = $derived(countries.find((item) => item.id === selectedCountryId) ?? null)
  let selectedLeague = $derived(leagues.find((item) => item.id === selectedLeagueId) ?? null)

  let filteredCountries = $derived.by(() => {
    const query = countryQuery.trim().toLowerCase()
    if (!query) return countries
    return countries.filter((country) => country.name.toLowerCase().includes(query))
  })

  let groups = $derived.by(() => {
    const byRole = new Map()
    for (const player of squad) {
      const role = player.role || '—'
      if (!byRole.has(role)) byRole.set(role, [])
      byRole.get(role).push(player)
    }
    return ROLE_ORDER.filter((role) => byRole.has(role)).map((role) => ({
      role,
      label: ROLE_LABELS[role] || role,
      players: byRole.get(role),
    }))
  })

  let avgOverall = $derived.by(() => {
    if (!squad.length) return 0
    return Math.round((squad.reduce((sum, player) => sum + player.overall, 0) / squad.length) * 10) / 10
  })

  let totalValue = $derived.by(() => squad.reduce((sum, player) => sum + player.market_value, 0))

  let heroStyle = $derived(
    selectedClub && selectedClub.colors.length
      ? `--hero-a: ${hexToRgba(selectedClub.colors[0], 0.3)}; --hero-b: ${hexToRgba(
          selectedClub.colors[1] || selectedClub.colors[0],
          0.13,
        )};`
      : '',
  )

  onMount(async () => {
    try {
      const [metaData, countryData] = await Promise.all([api.meta(), api.countries()])
      meta = metaData
      countries = countryData
    } catch (caught) {
      error = `Не удалось загрузить канон: ${caught.message}`
    } finally {
      loadingCountries = false
    }
  })

  function hexToRgba(hex, alpha) {
    if (!hex || !hex.startsWith('#') || hex.length < 7) return `rgba(91, 154, 139, ${alpha})`
    const value = hex.slice(1)
    const r = parseInt(value.slice(0, 2), 16)
    const g = parseInt(value.slice(2, 4), 16)
    const b = parseInt(value.slice(4, 6), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  function formatValue(value) {
    const number = Number(value) || 0
    if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)} млрд €`
    if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1)} млн €`
    if (number >= 1_000) return `${Math.round(number / 1_000)} тыс. €`
    return `${number} €`
  }

  function formatDate(value) {
    if (!value) return '—'
    return new Intl.NumberFormat('ru-RU').format(value)
  }

  function tierLabel(league) {
    if (!league) return ''
    const map = {
      'First Tier': 'D1',
      'Second Tier': 'D2',
      'Third Tier': 'D3',
      'Fourth Tier': 'D4',
      'Fifth Tier': 'D5',
      'Sixth Tier': 'D6',
      'Reserve league': 'Резерв',
      'Youth league': 'Молодёжь',
    }
    return map[league.tier] || league.tier
  }

  function initials(name) {
    return name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('')
      .toUpperCase()
  }

  function ovrClass(overall) {
    const value = Math.round(overall)
    if (value >= 90) return 'rating-dark'
    if (value >= 80) return 'rating-green'
    if (value >= 70) return 'rating-yellow'
    if (value >= 60) return 'rating-orange'
    return 'rating-red'
  }

  function hideBrokenImage(event) {
    event.currentTarget.style.visibility = 'hidden'
  }

  async function chooseCountry(country) {
    if (selectedCountryId === country.id) return
    selectedCountryId = country.id
    selectedLeagueId = null
    selectedClubId = null
    leagues = []
    clubs = []
    selectedClub = null
    squad = []
    error = ''

    const token = ++leagueToken
    loadingLeagues = true
    try {
      const data = await api.leagues(country.id)
      if (token !== leagueToken) return
      leagues = data
      if (data.length > 0) {
        await chooseLeague(data[0])
      }
    } catch (caught) {
      if (token === leagueToken) error = `Не удалось загрузить лиги: ${caught.message}`
    } finally {
      if (token === leagueToken) loadingLeagues = false
    }
  }

  async function chooseLeague(league) {
    if (selectedLeagueId === league.id) return
    selectedLeagueId = league.id
    selectedClubId = null
    clubs = []
    selectedClub = null
    squad = []
    error = ''

    const token = ++clubToken
    loadingClubs = true
    try {
      const data = await api.clubs(league.id)
      if (token !== clubToken) return
      clubs = data
    } catch (caught) {
      if (token === clubToken) error = `Не удалось загрузить клубы: ${caught.message}`
    } finally {
      if (token === clubToken) loadingClubs = false
    }
  }

  async function chooseClub(club) {
    if (selectedClubId === club.id) return
    selectedClubId = club.id
    selectedClub = club
    squad = []
    error = ''

    const token = ++squadToken
    loadingSquad = true
    try {
      const [clubData, squadData] = await Promise.all([api.club(club.id), api.squad(club.id)])
      if (token !== squadToken) return
      selectedClub = clubData
      squad = squadData
    } catch (caught) {
      if (token === squadToken) error = `Не удалось загрузить состав: ${caught.message}`
    } finally {
      if (token === squadToken) loadingSquad = false
    }
  }
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Career Mode</div>
        <div class="brand-sub">Новая карьера · выбор клуба из реального канона</div>
      </div>
    </div>

    {#if meta}
      <div class="meta-strip">
        <span class="meta-pill"><strong>{formatDate(meta.counts.players)}</strong> игроков</span>
        <span class="meta-pill"><strong>{formatDate(meta.counts.clubs)}</strong> клубов</span>
        <span class="meta-pill"><strong>{formatDate(meta.counts.leagues)}</strong> лиг</span>
        <span class="meta-pill"><strong>{formatDate(meta.counts.countries)}</strong> стран</span>
      </div>
    {/if}
  </header>

  <div class="stepbar">
    <div class:active={!selectedCountryId} class:done={selectedCountryId} class:current={!selectedCountryId} class="step">
      <span class="step-num">{selectedCountryId ? '✓' : '1'}</span>
      <span>
        <span class="step-label">Страна</span>
        <span class="step-value">{selectedCountry?.name || 'Выберите страну'}</span>
      </span>
    </div>
    <span class="step-line"></span>
    <div
      class:active={selectedCountryId && !selectedLeagueId}
      class:done={selectedLeagueId}
      class:current={selectedCountryId && !selectedLeagueId}
      class="step"
    >
      <span class="step-num">{selectedLeagueId ? '✓' : '2'}</span>
      <span>
        <span class="step-label">Лига</span>
        <span class="step-value">{selectedLeague?.name || 'Выберите лигу'}</span>
      </span>
    </div>
    <span class="step-line"></span>
    <div
      class:active={selectedLeagueId && !selectedClubId}
      class:done={selectedClubId}
      class:current={selectedLeagueId && !selectedClubId}
      class="step"
    >
      <span class="step-num">{selectedClubId ? '✓' : '3'}</span>
      <span>
        <span class="step-label">Клуб</span>
        <span class="step-value">{selectedClub?.name || 'Выберите клуб'}</span>
      </span>
    </div>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  <main class="workspace">
    <section class="panel">
      <div class="panel-head">
        <h2 class="panel-title">Страна</h2>
        <span class="panel-count">{filteredCountries.length} / {countries.length}</span>
      </div>
      <div class="search-wrap">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="7"></circle>
          <path d="m20 20-3.5-3.5"></path>
        </svg>
        <input class="search" bind:value={countryQuery} placeholder="Поиск страны" aria-label="Поиск страны" />
      </div>
      <div class="list">
        {#if loadingCountries}
          <div class="skeleton">
            {#each Array(8) as _}
              <div class="skeleton-line"></div>
            {/each}
          </div>
        {:else if filteredCountries.length === 0}
          <div class="empty">Страна не найдена</div>
        {:else}
          {#each filteredCountries as country (country.id)}
            <button
              class="row"
              class:selected={country.id === selectedCountryId}
              onclick={() => chooseCountry(country)}
            >
              <img class="flag" src={country.flag} alt="" loading="lazy" onerror={hideBrokenImage} />
              <span class="row-main">
                <span class="row-title">{country.name}</span>
                <span class="row-meta">{country.leagues_count} лиг · {country.clubs_count} клубов</span>
              </span>
              <svg class="row-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m9 18 6-6-6-6"></path>
              </svg>
            </button>
          {/each}
        {/if}
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2 class="panel-title">Лига</h2>
        <span class="panel-count">{leagues.length}</span>
      </div>
      <div class="list">
        {#if loadingLeagues}
          <div class="skeleton">
            {#each Array(6) as _}
              <div class="skeleton-line"></div>
            {/each}
          </div>
        {:else if !selectedCountryId}
          <div class="empty">Сначала выберите страну</div>
        {:else if leagues.length === 0}
          <div class="empty">В этой стране нет лиг</div>
        {:else}
          {#each leagues as league (league.id)}
            <button
              class="row"
              class:selected={league.id === selectedLeagueId}
              onclick={() => chooseLeague(league)}
            >
              <img class="crest" src={league.logo} alt="" loading="lazy" onerror={hideBrokenImage} />
              <span class="row-main">
                <span class="row-title">{league.name}</span>
                <span class="row-meta">{league.clubs_count} клубов · {league.tier}</span>
              </span>
              <span class="badge tier">{tierLabel(league)}</span>
            </button>
          {/each}
        {/if}
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2 class="panel-title">Клуб</h2>
        <span class="panel-count">{clubs.length}</span>
      </div>
      <div class="list">
        {#if loadingClubs}
          <div class="skeleton">
            {#each Array(8) as _}
              <div class="skeleton-line"></div>
            {/each}
          </div>
        {:else if !selectedLeagueId}
          <div class="empty">Сначала выберите лигу</div>
        {:else if clubs.length === 0}
          <div class="empty">В этой лиге нет клубов</div>
        {:else}
          {#each clubs as club (club.id)}
            <button class="row" class:selected={club.id === selectedClubId} onclick={() => chooseClub(club)}>
              <img class="crest sq" src={club.logo} alt="" loading="lazy" onerror={hideBrokenImage} />
              <span class="row-main">
                <span class="row-title">{club.name}</span>
                <span class="row-meta club-meta">
                  <span class="stadium-name" title={club.stadium.name || ''}>
                    {club.stadium.name || 'Стадион не указан'}
                  </span>
                  {#if club.stadium.seats}
                    <span class="seats">{formatDate(club.stadium.seats)} мест</span>
                  {/if}
                </span>
              </span>
              <svg class="row-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m9 18 6-6-6-6"></path>
              </svg>
            </button>
          {/each}
        {/if}
      </div>
    </section>

    <section class="panel detail-panel">
      {#if !selectedClubId}
        <div class="placeholder">
          <div class="placeholder-ring">
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
              <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z"></path>
              <path d="m12 8 2.4 1.8-.9 2.8h-3l-.9-2.8L12 8Z"></path>
              <path d="M12 3v5M3.8 8.7l5.2 3M20.2 8.7l-5.2 3M7 21l1.5-4.4M17 21l-1.5-4.4"></path>
            </svg>
          </div>
          <h3>Выберите клуб</h3>
          <p>Страна → лига → клуб. Состав, рейтинги и стоимость подтянутся из canon.db.</p>
        </div>
      {:else if loadingSquad && !selectedClub}
        <div class="skeleton">
          {#each Array(10) as _}
            <div class="skeleton-line"></div>
          {/each}
        </div>
      {:else if selectedClub}
        <div class="detail">
          <div class="club-hero" style={heroStyle}>
            <div class="club-hero-top">
              <img class="crest lg" src={selectedClub.logo} alt="" onerror={hideBrokenImage} />
              <div class="row-main">
                <div class="club-name">{selectedClub.name}</div>
                <div class="club-sub">
                  <img class="flag" src={selectedClub.country_flag} alt="" onerror={hideBrokenImage} />
                  <span>{selectedClub.country_name}</span>
                  <span class="dot"></span>
                  <span>{selectedClub.league_name}</span>
                  <span class="badge tier">{tierLabel(selectedClub)}</span>
                </div>
              </div>
            </div>
            <div class="hero-stats">
              <div class="hero-stat">
                <span>Стадион</span>
                <strong title={selectedClub.stadium.name || ''}>{selectedClub.stadium.name || '—'}</strong>
              </div>
              <div class="hero-stat">
                <span>Вместимость</span>
                <strong>{selectedClub.stadium.seats ? formatDate(selectedClub.stadium.seats) : '—'}</strong>
              </div>
              <div class="hero-stat">
                <span>Средний OVR</span>
                <strong>{avgOverall || '—'}</strong>
              </div>
              <div class="hero-stat">
                <span>Стоимость состава</span>
                <strong>{totalValue ? formatValue(totalValue) : '—'}</strong>
              </div>
            </div>
          </div>

          <div class="squad-head">
            <h3>Состав</h3>
            <span>{squad.length} игроков</span>
          </div>

          <div class="squad">
            {#if loadingSquad}
              <div class="skeleton">
                {#each Array(8) as _}
                  <div class="skeleton-line"></div>
                {/each}
              </div>
            {:else if squad.length === 0}
              <div class="empty">У клуба нет игроков в каноне</div>
            {:else}
              {#each groups as group (group.role)}
                <div class="group-title">{group.label}</div>
                {#each group.players as player (player.id)}
                  <div class="player">
                    <span class="shirt">{player.shirt_number ?? '—'}</span>
                    <span class="avatar">
                      {initials(player.name)}
                      <img src={player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                    </span>
                    <span class="row-main">
                      <span class="player-name">{player.name}</span>
                      <span class="player-meta">
                        {player.position}
                        {#if player.citizenship.length}· {player.citizenship[0]}{/if}
                      </span>
                    </span>
                    <span class="pos">{player.role || '—'}</span>
                    <span class="num">{player.age ?? '—'}</span>
                    <span class="ovr {ovrClass(player.overall)}">{Math.round(player.overall)}</span>
                    <span class="value">{formatValue(player.market_value)}</span>
                  </div>
                {/each}
              {/each}
            {/if}
          </div>
        </div>
      {/if}
    </section>
  </main>

  <footer class="footnote">
    <span>
      {#if selectedClub}
        Выбран клуб: <strong>{selectedClub.name}</strong> · {selectedClub.league_name}
      {:else}
        Канон: реальные составы и рейтинги из transfermarkt
      {/if}
    </span>
    <span><code>canon.db</code> · schema v{meta?.schema_version ?? 1}</span>
  </footer>
</div>
