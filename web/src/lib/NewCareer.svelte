<script>
  import { onMount, tick } from 'svelte'
  import { fade, fly } from 'svelte/transition'
  import { api } from './api.js'
  import { registerBack, registerCycle } from './actions.js'
  import AppShell from './ui/AppShell.svelte'
  import Glyph from './ui/Glyph.svelte'
  import Row from './ui/Row.svelte'
  import Tile from './ui/Tile.svelte'
  import { focusFirst, inputDevice } from './input.js'
  import { formatValue, hideBrokenImage, tierLabel } from './format.js'

  let { oncreated, onback } = $props()

  let meta = $state(null)
  let countries = $state([])
  let leagues = $state([])
  let clubs = $state([])
  let selectedClub = $state(null)
  let squad = $state([])
  let step = $state('club')

  let selectedCountryId = $state(null)
  let selectedLeagueId = $state(null)
  let selectedClubId = $state(null)

  let managerName = $state('')
  let nationalityId = $state('')
  let nationalityTouched = $state(false)

  let loadingCountries = $state(true)
  let loadingLeagues = $state(false)
  let loadingClubs = $state(false)
  let loadingClub = $state(false)
  let creating = $state(false)
  let error = $state('')

  let reducedMotion = $state(false)
  let swapDuration = $derived(reducedMotion ? 0 : 160)
  let stepDuration = $derived(reducedMotion ? 0 : 180)
  let stepShift = $derived(reducedMotion ? 0 : 12)

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
    const ages = squad.map((player) => player.age).filter((age) => typeof age === 'number')
    const averageAge = ages.length
      ? Math.round((ages.reduce((sum, age) => sum + age, 0) / ages.length) * 10) / 10
      : null
    return { totalValue, average: Math.round(average * 10) / 10, averageAge }
  })
  let canCreate = $derived(Boolean(managerName.trim() && nationalityId && !creating))
  let confirmKey = $derived($inputDevice === 'gamepad' ? 'A' : 'Enter')
  let status = $derived(
    error
      ? 'ошибка API'
      : meta
        ? `${meta.counts.clubs} клубов · ${meta.counts.leagues} лиг`
        : 'canon.db · загрузка…',
  )
  let hints = $derived(
    step === 'club'
      ? [
          { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Навигация' },
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Сменить значение' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать клуб' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      : [
          { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Навигация' },
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Гражданство' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Начать карьеру' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ],
  )

  onMount(() => {
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const syncMotion = () => {
      reducedMotion = motion.matches
    }
    syncMotion()
    motion.addEventListener?.('change', syncMotion)

    const stopBack = registerBack(handleBack)
    const stopCycle = registerCycle(handleCycle)
    loadCanon()

    return () => {
      motion.removeEventListener?.('change', syncMotion)
      stopBack()
      stopCycle()
    }
  })

  function revealSelected(node, selected) {
    if (selected) node.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    return {
      update(next) {
        if (next) node.scrollIntoView({ block: 'nearest', inline: 'nearest' })
      },
    }
  }

  async function loadCanon() {
    try {
      const [metaData, countryData] = await Promise.all([api.meta(), api.countries()])
      meta = metaData
      countries = countryData
      if (countryData.length) {
        await chooseCountry(countryData[0])
      }
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
    if (step === 'manager') go('club')
    else onback()
  }

  function handleCycle(direction) {
    const control = document.activeElement?.dataset?.cycle ?? ''
    if (control === 'country') cycleCountry(direction)
    else if (control === 'league') cycleLeague(direction)
    else if (control === 'club') cycleClub(direction)
    else if (control === 'nationality') cycleNationality(direction)
  }

  function cycleCountry(direction) {
    if (countries.length < 2) return
    const index = countries.findIndex((item) => item.id === selectedCountryId)
    const current = index < 0 ? 0 : index
    const next = (current + (direction === 'right' ? 1 : -1) + countries.length) % countries.length
    chooseCountry(countries[next])
  }

  function cycleLeague(direction) {
    if (leagues.length < 2) return
    const index = leagues.findIndex((item) => item.id === selectedLeagueId)
    const current = index < 0 ? 0 : index
    const next = (current + (direction === 'right' ? 1 : -1) + leagues.length) % leagues.length
    chooseLeague(leagues[next])
  }

  function cycleClub(direction) {
    if (clubs.length < 2) return
    const current = clubIndex < 0 ? 0 : clubIndex
    const next = (current + (direction === 'right' ? 1 : -1) + clubs.length) % clubs.length
    chooseClub(clubs[next])
  }

  function cycleNationality(direction) {
    if (countries.length < 2) return
    const index = countries.findIndex((item) => item.id === nationalityId)
    const current = index < 0 ? 0 : index
    const next = (current + (direction === 'right' ? 1 : -1) + countries.length) % countries.length
    nationalityId = countries[next].id
    nationalityTouched = true
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
    loadingClubs = false
    loadingClub = false
    ++clubsToken
    ++detailToken

    const token = ++leagueToken
    loadingLeagues = true
    try {
      const data = await api.leagues(country.id)
      if (token !== leagueToken) return
      leagues = data
      if (data.length) {
        await chooseLeague(data[0])
      }
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
    loadingClub = false
    ++detailToken

    const token = ++clubsToken
    loadingClubs = true
    try {
      const data = await api.clubs(league.id)
      if (token !== clubsToken) return
      clubs = data
      if (data.length) {
        await chooseClub(data[0])
      }
    } catch (caught) {
      if (token === clubsToken) error = `Не удалось загрузить клубы: ${caught.message}`
    } finally {
      if (token === clubsToken) loadingClubs = false
    }
  }

  async function chooseClub(club) {
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
    } catch (caught) {
      if (token === detailToken) error = `Не удалось загрузить клуб: ${caught.message}`
    } finally {
      if (token === detailToken) loadingClub = false
    }
  }

  function chooseClubFromList(club) {
    chooseClub(club)
    focusFirst()
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

<AppShell
  fill
  {status}
  statusError={Boolean(error)}
  {hints}
  note={selectedClub ? `${selectedClub.name} · ${selectedClub.league_name}` : 'Выбор из canon.db'}
>
  {#snippet header()}
    <div class="creation-steps" role="group" aria-label="Этапы новой карьеры">
      <span class="creation-step-tab" class:is-active={step === 'club'}>Клуб</span>
      <span class="creation-step-tab" class:is-active={step === 'manager'}>Менеджер</span>
    </div>
  {/snippet}

  <div class="creation">
    {#if error}
      <p class="gf-notice is-error">{error}</p>
    {/if}

    {#key step}
      {#if step === 'club'}
        <section
          class="creation-step creation-step--club"
          aria-label="Выбор клуба"
          in:fly={{ y: stepShift, duration: stepDuration }}
        >
          <div class="creation-left">
            <Row
              title={selectedCountry?.name ?? (loadingCountries ? 'Загрузка…' : 'Нет стран')}
              sub={selectedCountry
                ? `Страна · ${selectedCountry.leagues_count} лиг · ${selectedCountry.clubs_count} клубов`
                : 'Страна'}
              data-cycle="country"
              aria-label={`Страна: ${selectedCountry?.name ?? 'не выбрана'}. Изменяется стрелками влево и вправо.`}
            >
              {#snippet lead()}
                {#if selectedCountry?.flag}
                  <img
                    src={selectedCountry.flag}
                    alt=""
                    width="44"
                    height="30"
                    loading="lazy"
                    onerror={hideBrokenImage}
                  />
                {/if}
              {/snippet}
            </Row>

            <Row
              title={selectedLeague?.name ?? (loadingLeagues ? 'Загрузка лиг…' : 'Нет лиг')}
              sub={selectedLeague
                ? `Лига · ${selectedLeague.clubs_count} клубов · ${tierLabel(selectedLeague)}`
                : 'Лига'}
              data-cycle="league"
              aria-label={`Лига: ${selectedLeague?.name ?? 'не выбрана'}. Изменяется стрелками влево и вправо.`}
            >
              {#snippet lead()}
                {#if selectedLeague?.logo}
                  <img
                    src={selectedLeague.logo}
                    alt=""
                    width="44"
                    height="30"
                    loading="lazy"
                    onerror={hideBrokenImage}
                  />
                {/if}
              {/snippet}
            </Row>

            <div class="creation-clublist">
              <div class="creation-clublist__head">
                <span>Клубы лиги</span>
                <span class="creation-clublist__count">{clubs.length}</span>
              </div>
              <div class="creation-clublist__grid">
                {#each clubs as club (club.id)}
                  <button
                    type="button"
                    class="creation-club-chip"
                    class:is-selected={club.id === selectedClubId}
                    tabindex="-1"
                    use:revealSelected={club.id === selectedClubId}
                    title={club.name}
                    onclick={() => chooseClubFromList(club)}
                  >
                    {club.name}
                  </button>
                {:else}
                  <span class="creation-clublist__empty">
                    {loadingCountries || loadingLeagues || loadingClubs ? 'Загрузка…' : 'Нет клубов'}
                  </span>
                {/each}
              </div>
            </div>
          </div>

          {#if selectedClub}
            <div class="creation-club__spotlight">
              <Tile
                bare
                data-cycle="club"
                data-autofocus
                aria-label={`${selectedClub.name}, ${selectedClub.league_name}. ${clubIndex + 1} из ${clubs.length}. ${confirmKey} — выбрать клуб.`}
                onclick={() => go('manager')}
              >
                <span class="creation-club__body">
                  {#key selectedClub.id}
                    <span
                      class="creation-club__panel"
                      transition:fade={{ duration: swapDuration }}
                    >
                      <span class="creation-club__top">
                        <span class="creation-club__arrow" aria-hidden="true">←</span>
                        <span class="creation-club__index">{clubIndex + 1} / {clubs.length}</span>
                        <span class="creation-club__arrow" aria-hidden="true">→</span>
                      </span>
                      <span class="creation-club__crest">
                        <img
                          src={selectedClub.logo}
                          alt=""
                          width="210"
                          height="210"
                          onerror={hideBrokenImage}
                        />
                      </span>
                      <span class="creation-club__name">{selectedClub.name}</span>
                      <span class="creation-club__sub">
                        {tierLabel(selectedClub)} · {selectedClub.league_name} · {selectedClub.country_name}
                      </span>
                      <span class="creation-club__hint">{confirmKey} · выбрать клуб</span>
                    </span>
                  {/key}
                </span>
              </Tile>
            </div>

            <aside class="creation-facts" aria-label="Сводка по клубу">
              {#key selectedClub.id}
                <div class="creation-facts__panel" transition:fade={{ duration: swapDuration }}>
                  <div class="creation-facts__head">
                    <span class="creation-facts__title">Сводка по клубу</span>
                    <span class="creation-facts__league">{selectedClub.country_name}</span>
                  </div>
                  <div class="creation-facts__grid">
                    <div class="creation-fact">
                      <span class="creation-fact__label">Состав</span>
                      <strong class="creation-fact__value">
                        {loadingClub ? '…' : `${squad.length} игроков`}
                      </strong>
                      <span class="creation-fact__sub">
                        {summary
                          ? `OVR ${summary.average}`
                          : loadingClub
                            ? 'Загрузка…'
                            : 'Нет данных'}
                      </span>
                    </div>
                    <div class="creation-fact">
                      <span class="creation-fact__label">Возраст</span>
                      <strong class="creation-fact__value">{summary?.averageAge ?? '—'}</strong>
                      <span class="creation-fact__sub">лет</span>
                    </div>
                    <div class="creation-fact">
                      <span class="creation-fact__label">Стоимость</span>
                      <strong class="creation-fact__value">
                        {summary ? formatValue(summary.totalValue) : '—'}
                      </strong>
                      <span class="creation-fact__sub">состава</span>
                    </div>
                    <div class="creation-fact">
                      <span class="creation-fact__label">Основан</span>
                      <strong class="creation-fact__value">
                        {selectedClub.founded_on ? selectedClub.founded_on.slice(0, 4) : '—'}
                      </strong>
                      <span class="creation-fact__sub">{tierLabel(selectedClub)}</span>
                    </div>
                    <div class="creation-fact creation-fact--stadium">
                      <span class="creation-fact__label">Стадион</span>
                      <strong class="creation-fact__value">{selectedClub.stadium.name || '—'}</strong>
                    </div>
                    <div class="creation-fact">
                      <span class="creation-fact__label">Вместимость</span>
                      <strong class="creation-fact__value">
                        {selectedClub.stadium.seats
                          ? selectedClub.stadium.seats.toLocaleString('ru-RU')
                          : '—'}
                      </strong>
                      <span class="creation-fact__sub">мест</span>
                    </div>
                  </div>
                </div>
              {/key}
            </aside>
          {:else}
            <div class="creation-placeholder" aria-live="polite">
              {#if loadingCountries || loadingLeagues || loadingClubs}
                <span class="creation-placeholder__label">Загрузка клубов…</span>
                <span class="creation-skeleton-line"></span>
                <span class="creation-skeleton-line"></span>
                <span class="creation-skeleton-line"></span>
              {:else}
                <span class="creation-placeholder__label">Нет клубов</span>
                <span class="creation-placeholder__sub">
                  Смените лигу или страну стрелками ← →
                </span>
              {/if}
            </div>
          {/if}
        </section>
      {:else}
        <section
          class="creation-step creation-step--manager"
          aria-label="Менеджер"
          in:fly={{ y: stepShift, duration: stepDuration }}
        >
          <form
            class="creation-manager"
            onsubmit={(event) => {
              event.preventDefault()
              createCareer()
            }}
          >
            <label class="creation-field">
              <span class="creation-field__label">Имя менеджера</span>
              <input
                id="manager-name"
                name="manager_name"
                class="creation-input"
                data-nav
                data-autofocus
                bind:value={managerName}
                maxlength="80"
                placeholder="Например, Алексей Смирнов"
                autocomplete="off"
              />
            </label>

            <Row
              title={nationality?.name ?? 'Выберите гражданство'}
              sub="Гражданство менеджера"
              data-cycle="nationality"
              aria-label={`Гражданство: ${nationality?.name ?? 'не выбрано'}. Изменяется стрелками влево и вправо.`}
            >
              {#snippet trail()}
                {#if nationality}
                  <img
                    class="creation-flag"
                    src={nationality.flag}
                    alt=""
                    width="46"
                    height="32"
                    onerror={hideBrokenImage}
                  />
                {/if}
              {/snippet}
            </Row>

            <div class="creation-cta">
              <Tile
                title={creating ? 'Создаём карьеру…' : 'Начать карьеру'}
                sub={creating
                  ? 'Сохраняем карьеру…'
                  : canCreate
                    ? 'Имя и гражданство заданы'
                    : 'Введите имя и выберите гражданство'}
                meta={creating ? 'Подождите…' : `${confirmKey} · создать`}
                glyph="play"
                glyphSize={56}
                disabled={!canCreate}
                onclick={createCareer}
              />
            </div>
          </form>

          <aside class="creation-recap" aria-label="Выбранный клуб">
            <span class="creation-recap__eyebrow">Ваш клуб</span>
            {#if selectedClub}
              <div class="creation-recap__head">
                <img
                  class="creation-recap__crest"
                  src={selectedClub.logo}
                  alt=""
                  width="72"
                  height="72"
                  onerror={hideBrokenImage}
                />
                <div class="creation-recap__identity">
                  <strong class="creation-recap__name">{selectedClub.name}</strong>
                  <span class="creation-recap__meta">
                    {selectedClub.league_name} · {selectedClub.country_name}
                  </span>
                </div>
              </div>
            {/if}
            <div class="creation-recap__grid">
              <div class="creation-recap__stat">
                <span>Состав</span>
                <strong>{squad.length}</strong>
              </div>
              <div class="creation-recap__stat">
                <span>Средний OVR</span>
                <strong>{summary?.average ?? '—'}</strong>
              </div>
              <div class="creation-recap__stat">
                <span>Стоимость</span>
                <strong>{summary ? formatValue(summary.totalValue) : '—'}</strong>
              </div>
              <div class="creation-recap__stat">
                <span>Seed</span>
                <strong>случайный</strong>
              </div>
            </div>
          </aside>
        </section>
      {/if}
    {/key}
  </div>
</AppShell>
