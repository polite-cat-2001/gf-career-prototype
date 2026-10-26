<script>
  import { onMount, tick } from 'svelte'
  import { registerBack, registerDetails, registerSave, registerTabs } from './actions.js'
  import Controls from './Controls.svelte'
  import Icon from './Icon.svelte'
  import Tabs from './Tabs.svelte'
  import { focusElement, focusFirst } from './input.js'
  import {
    attributeGroups,
    compareTone,
    formatDate,
    formatTimestamp,
    formatValue,
    hideBrokenImage,
    monthLabel,
    ovrClass,
    playerInitialName,
    posTone,
    positionLabel,
    radarValues,
    seasonLabel,
    shortRole,
    statTone,
    tierLabel,
    weekStrip,
  } from './format.js'

  let {
    career,
    saving = false,
    saveNotice = '',
    saveError = '',
    onsave,
    onswap,
    onexit,
  } = $props()

  const tabs = [
    { id: 'centre', label: 'Центр' },
    { id: 'squad', label: 'Состав' },
    { id: 'transfers', label: 'Трансферы', disabled: true },
    { id: 'office', label: 'Офис', disabled: true },
    { id: 'season', label: 'Сезон', disabled: true },
  ]
  const enabledTabs = tabs.filter((tab) => !tab.disabled).map((tab) => tab.id)

  const planTabs = [
    { label: 'Состав', active: true },
    { label: 'Схемы' },
    { label: 'Амплуа' },
    { label: 'Задачи' },
    { label: 'Тактика' },
  ]

  const detailPages = [
    { id: 'general', label: 'Общая информация' },
    { id: 'stats-one', label: 'Статы 1' },
    { id: 'stats-two', label: 'Статы 2' },
  ]

  const INFO_LABELS = [
    { key: 'position', label: 'Амплуа' },
    { key: 'age', label: 'Возраст' },
    { key: 'height', label: 'Рост' },
    { key: 'weight', label: 'Вес' },
    { key: 'foot', label: 'Рабочая нога' },
    { key: 'weakFoot', label: 'Слабая нога' },
    { key: 'skillMoves', label: 'Финты' },
    { key: 'shirtNumber', label: 'Номер' },
    { key: 'potential', label: 'Потенциал' },
    { key: 'marketValue', label: 'Стоимость' },
    { key: 'citizenship', label: 'Гражданство' },
  ]

  const squadTiles = [
    { id: 'club', label: 'Состав клуба', note: 'Текущий состав на матч', selected: true },
    { id: 'national', label: 'Сборная', note: 'Сейчас вы не являетесь тренером сборной', icon: 'globe', disabled: true },
    { id: 'centre', label: 'Центр составов', note: 'Статус, статистика и финансы — #4', icon: 'users', disabled: true },
    { id: 'national-squad', label: 'Выбор состава сборной', note: 'Доступно только для сборных', icon: 'globe', disabled: true },
    { id: 'main-squads', label: 'Основные составы', note: 'Несколько составов — #4', icon: 'layers', disabled: true },
    { id: 'change', label: 'Изменить игрока', note: 'Заблокировано', icon: 'lock', disabled: true },
  ]

  let tab = $state('centre')
  let view = $state('overview')
  let detailsPage = $state(0)
  let focusPlayerId = $state(null)
  let anchorId = $state(null)
  let swapping = $state(false)
  let soonNotice = $state('')
  let soonTimer = null

  let summary = $derived(career.squad.summary)
  let lineup = $derived(career.squad.lineup)
  let squadPlayers = $derived([...lineup.slots.map((slot) => slot.player), ...lineup.bench])
  let focusedPlayer = $derived(
    squadPlayers.find((player) => player.id === focusPlayerId) ?? lineup.slots[0]?.player ?? null,
  )
  let anchorPlayer = $derived(
    anchorId ? squadPlayers.find((player) => player.id === anchorId) ?? null : null,
  )
  let comparing = $derived(
    Boolean(anchorPlayer && focusedPlayer && anchorPlayer.id !== focusedPlayer.id),
  )
  let canSwap = $derived(comparing)
  let anchorRadar = $derived(anchorPlayer ? radarValues(anchorPlayer.stats) : [])
  let teamAverage = $derived(average(lineup.slots.map((slot) => slot.player.overall)))
  let teamStrength = $derived(Math.round(teamAverage))
  let projectedTeamAverage = $derived(teamAfterSwap())
  let teamDelta = $derived(comparing ? projectedTeamAverage - teamAverage : 0)
  let teamDisplay = $derived(Math.round(comparing ? projectedTeamAverage : teamAverage))
  let profileGroups = $derived(focusedPlayer ? attributeGroups(focusedPlayer.stats) : [])
  let detailGroups = $derived(
    detailsPage === 1
      ? profileGroups.filter((group) => group.id !== 'technical')
      : detailsPage === 2
        ? profileGroups.filter((group) => group.id === 'technical')
        : [],
  )
  let infoRows = $derived.by(() => {
    if (!focusedPlayer) return []
    const right = infoValues(focusedPlayer)
    const left = anchorPlayer ? infoValues(anchorPlayer) : null
    return INFO_LABELS.map((item) => ({
      label: item.label,
      left: left ? left[item.key] : right[item.key],
      right: comparing ? right[item.key] : null,
    }))
  })
  let radar = $derived(focusedPlayer ? radarValues(focusedPlayer.stats) : [])
  let days = $derived(weekStrip(career.date))

  let hints = $derived.by(() => {
    const start = { gamepad: ['Start'], keyboard: ['S'], label: 'Сохранить' }
    const sections = { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Разделы' }
    if (tab === 'squad' && view === 'details') {
      return [
        { gamepad: ['B'], keyboard: ['Esc'], label: 'К полю' },
        { gamepad: ['Y'], keyboard: ['R'], label: 'План игры' },
        { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Страницы' },
        start,
      ]
    }
    if (tab === 'squad' && view === 'plan') {
      return [
        { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
        comparing
          ? { gamepad: ['A'], keyboard: ['Enter'], label: canSwap ? 'Обменять' : 'Просмотр' }
          : { gamepad: ['A'], keyboard: ['Enter'], label: 'Сравнить' },
        { gamepad: ['Y'], keyboard: ['R'], label: 'Подробности' },
        { gamepad: ['B'], keyboard: ['Esc'], label: comparing ? 'Отменить' : 'Назад' },
        start,
      ]
    }
    const list = [sections]
    if (tab === 'centre') {
      list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Открыть' })
      list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'В меню' })
    } else {
      list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'План игры' })
      list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
    }
    list.push(start)
    return list
  })

  onMount(() => {
    const stopBack = registerBack(handleBack)
    const stopTabs = registerTabs(switchTab)
    const stopSave = registerSave(handleSave)
    const stopDetails = registerDetails(toggleDetails)
    tick().then(focusFirst)
    return () => {
      stopBack()
      stopTabs()
      stopSave()
      stopDetails()
    }
  })

  function handleSave() {
    if (!saving) onsave()
  }

  function showSoon(message) {
    soonNotice = message
    clearTimeout(soonTimer)
    soonTimer = setTimeout(() => {
      soonNotice = ''
    }, 2400)
  }

  function average(values) {
    if (!values.length) return 0
    return values.reduce((total, value) => total + value, 0) / values.length
  }

  function slotFor(playerId) {
    return lineup.slots.find((slot) => slot.player.id === playerId) ?? null
  }

  function currentRole(player) {
    return slotFor(player.id)?.role ?? player.role
  }

  function teamAfterSwap() {
    if (!comparing) return teamAverage
    const starterIds = lineup.slots.map((slot) => slot.player.id)
    const anchorSlot = starterIds.indexOf(anchorPlayer.id)
    const focusedSlot = starterIds.indexOf(focusedPlayer.id)
    if (anchorSlot !== -1 && focusedSlot !== -1) return teamAverage
    if (anchorSlot === -1 && focusedSlot === -1) return teamAverage
    const overalls = lineup.slots.map((slot) => slot.player.overall)
    if (anchorSlot !== -1) overalls[anchorSlot] = focusedPlayer.overall
    if (focusedSlot !== -1) overalls[focusedSlot] = anchorPlayer.overall
    return average(overalls)
  }

  function ratingAt(player, slotRole) {
    if (player.role === slotRole) return Math.round(player.overall)
    const families = {
      GK: 'goalkeeper',
      CB: 'defence',
      LB: 'defence',
      RB: 'defence',
      DM: 'middle',
      CM: 'middle',
      AM: 'middle',
      LM: 'wing',
      RM: 'wing',
      CF: 'attack',
    }
    const order = ['goalkeeper', 'defence', 'middle', 'wing', 'attack']
    const from = order.indexOf(families[player.role])
    const to = order.indexOf(families[slotRole])
    const distance = from === -1 || to === -1 ? 3 : Math.abs(from - to)
    const penalty = distance === 1 ? 2 : distance === 2 ? 4 : 6
    return Math.max(1, Math.round(player.overall - penalty))
  }

  function targetInfo(player) {
    if (!comparing || !player) return null
    const counterpart = player.id === anchorPlayer?.id ? focusedPlayer : anchorPlayer
    if (!counterpart) return null
    const slot = slotFor(counterpart.id)
    if (!slot) return null
    const rating = ratingAt(player, slot.role)
    return {
      role: slot.role,
      position: slot.position,
      rating,
      delta: rating - ratingAt(player, currentRole(player)),
    }
  }

  function infoValues(player) {    return {
      position: positionLabel(player.position),
      age: player.age ?? '—',
      height: player.height ? `${player.height} см` : '—',
      weight: player.weight ? `${player.weight} кг` : '—',
      foot: player.foot || '—',
      weakFoot: player.weak_foot ?? '—',
      skillMoves: player.skill_moves ?? '—',
      shirtNumber: player.shirt_number ?? '—',
      potential: player.pot ?? '—',
      marketValue: formatValue(player.market_value),
      citizenship: player.citizenship.join(', ') || '—',
    }
  }

  function revealName(event) {
    const wrapper = event.currentTarget.querySelector('.player-name-wrap')
    const name = wrapper?.querySelector('.player-name')
    if (!name || name.classList.contains('is-scrolling')) return
    const shift = wrapper.clientWidth - name.scrollWidth
    if (shift >= -1) return
    name.style.setProperty('--name-shift', `${shift}px`)
    name.classList.remove('is-scrolling')
    void name.offsetWidth
    name.classList.add('is-scrolling')
    name.addEventListener('animationend', () => name.classList.remove('is-scrolling'), {
      once: true,
    })
  }

  function handleBack() {
    if (tab === 'squad') {
      if (view === 'details') {
        closeDetails()
        return
      }
      if (view === 'plan') {
        if (anchorId) {
          anchorId = null
          return
        }
        backToOverview()
        return
      }
      setTab('centre')
      return
    }
    if (tab !== 'centre') {
      setTab('centre')
      return
    }
    onexit()
  }

  function closeDetails() {
    view = 'plan'
    tick().then(() => focusPlayer(focusPlayerId))
  }

  function toggleDetails() {
    if (tab !== 'squad' || !focusedPlayer) return
    if (view === 'details') {
      closeDetails()
      return
    }
    if (view === 'plan') {
      detailsPage = 0
      view = 'details'
      tick().then(() => {
        document.querySelector('.details-panel')?.focus({ preventScroll: true })
      })
    }
  }

  async function backToOverview() {
    view = 'overview'
    anchorId = null
    focusPlayerId = null
    await tick()
    focusFirst()
  }

  async function setTab(next) {
    if (!enabledTabs.includes(next)) return
    tab = next
    view = 'overview'
    anchorId = null
    focusPlayerId = null
    await tick()
    focusFirst()
  }

  function switchTab(direction) {
    if (tab === 'squad' && view === 'details') {
      switchDetailsPage(direction)
      return
    }
    const index = enabledTabs.indexOf(tab)
    const offset = direction === 'right' ? 1 : -1
    const next = enabledTabs[(index + offset + enabledTabs.length) % enabledTabs.length]
    setTab(next)
  }

  function switchDetailsPage(direction) {
    const offset = direction === 'right' ? 1 : -1
    detailsPage = (detailsPage + offset + detailPages.length) % detailPages.length
  }

  async function openPlan(playerId = null) {
    tab = 'squad'
    view = 'plan'
    anchorId = null
    focusPlayerId = playerId ?? lineup.slots[0]?.player.id ?? null
    await tick()
    focusPlayer(focusPlayerId)
  }

  function focusPlayer(playerId) {
    if (!playerId) return
    const element = document.querySelector(`[data-player="${playerId}"]`)
    focusElement(element)
  }

  async function activatePlayer(player) {
    if (swapping) return
    if (!anchorId) {
      anchorId = player.id
      focusPlayerId = player.id
      return
    }
    if (anchorId === player.id) {
      anchorId = null
      return
    }
    if (!canSwap) return
    swapping = true
    const anchor = anchorId
    const updated = await onswap(anchor, player.id)
    swapping = false
    if (!updated) return
    anchorId = null
    focusPlayerId = player.id
    await tick()
    focusPlayer(player.id)
  }

  function pitchX(x, y) {
    return 50 + (x - 50) * (0.62 + 0.38 * (y / 100))
  }

  function pitchY(y) {
    return 8 + y * 0.84
  }

  function radarPoints(values, radius = 44, centre = 72) {
    if (!values.length) return ''
    return values
      .map((axis, index) => {
        const angle = (Math.PI * 2 * index) / values.length - Math.PI / 2
        const reach = (axis.value / 100) * radius
        return `${(centre + Math.cos(angle) * reach).toFixed(1)},${(centre + Math.sin(angle) * reach).toFixed(1)}`
      })
      .join(' ')
  }

  function radarGrid(values, radius = 44, centre = 72) {
    return values
      .map((_, index) => {
        const angle = (Math.PI * 2 * index) / values.length - Math.PI / 2
        return `${(centre + Math.cos(angle) * radius).toFixed(1)},${(centre + Math.sin(angle) * radius).toFixed(1)}`
      })
      .join(' ')
  }

  function radarLabelPos(index, count, radius = 58, centre = 72) {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2
    return {
      x: centre + Math.cos(angle) * radius,
      y: centre + Math.sin(angle) * radius,
    }
  }
</script>

<div class="app">
  <header class="topbar hub-topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Карьера</div>
        <div class="brand-sub">{career.manager.name}</div>
      </div>
    </div>

    <Tabs {tabs} active={tab} onselect={setTab} />

    <div class="hub-club-strip">
      <img class="strip-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
      <div>
        <div class="strip-club">{career.club.name}</div>
        <div class="strip-meta">{formatDate(career.date)} · {tierLabel(career.club)}</div>
      </div>
    </div>
  </header>

  <main class="screen hub-screen">
    {#snippet radarChart(values, secondary)}
      <svg class="radar" viewBox="0 0 144 144" aria-hidden="true">
        <polygon class="radar-grid" points={radarGrid(values)}></polygon>
        <polygon class="radar-grid inner" points={radarGrid(values, 22)}></polygon>
        {#if secondary?.length}
          <polygon class="radar-compare" points={radarPoints(secondary)}></polygon>
        {/if}
        <polygon class="radar-fill" points={radarPoints(values)}></polygon>
        {#each values as axis, index (axis.label)}
          {@const pos = radarLabelPos(index, values.length)}
          <text class="radar-label" x={pos.x} y={pos.y}>{axis.label}</text>
        {/each}
      </svg>
    {/snippet}

    {#snippet strengthBadge()}
      <div class="team-strength">
        <svg class="team-shield" viewBox="0 0 64 72" aria-hidden="true">
          <path d="M32 2 60 11v25c0 16-12 27-28 34C16 63 4 52 4 36V11z"></path>
        </svg>
        <strong>{teamDisplay}</strong>
        {#if comparing && teamDelta > 0.05}
          <span class="team-delta up" aria-label="Сила состава вырастет">▲</span>
        {/if}
        {#if comparing && teamDelta < -0.05}
          <span class="team-delta down" aria-label="Сила состава упадёт">▼</span>
        {/if}
      </div>
    {/snippet}

    {#snippet playerBlock(player, mirrored)}
      {@const target = targetInfo(player)}
      {@const role = currentRole(player)}
      <div class="head-side" class:mirrored={mirrored}>
        <div class="head-photo-block">
          <span class="player-photo-large">
            <img src={player.photo} alt="" onerror={hideBrokenImage} />
          </span>
          <span class="photo-fatigue" title={`Усталость ${player.fatigue}`}>
            <span class="fatigue-bar"><i style={`width:${player.fatigue}%`}></i></span>
          </span>
        </div>
        <div class="head-info" class:right={mirrored}>
          <div class="head-name-row">
            {#if player.shirt_number}
              <span class="head-number">{player.shirt_number}</span>
            {/if}
            <strong class="head-name">{playerInitialName(player)}</strong>
          </div>
          <div class="head-rating-row">
            <span class="pos-badge {posTone(role)}">{shortRole(role)}</span>
            <strong class="head-ovr {ovrClass(ratingAt(player, role))}">{ratingAt(player, role)}</strong>
            <span class="head-shift">›</span>
            {#if target}
              <span class="pos-badge {posTone(target.role)}">{shortRole(target.role)}</span>
              <strong class="head-ovr {ovrClass(target.rating)}">{target.rating}</strong>
              {#if target.delta > 0}
                <span class="rating-delta up">▲</span>
              {:else if target.delta < 0}
                <span class="rating-delta down">▼</span>
              {/if}
            {:else}
              <span class="rating-dash">–</span>
            {/if}
          </div>
        </div>
      </div>
    {/snippet}

    {#if saveError}
      <div class="notice error hub-notice">{saveError}</div>
    {:else if saveNotice}
      <div class="notice hub-notice">{saveNotice}</div>
    {/if}

    {#if soonNotice && !saveNotice && !saveError}
      <div class="notice hub-notice">{soonNotice}</div>
    {/if}

    {#if tab === 'centre'}
      <div class="hub-grid">
        <button
          class="widget widget-next"
          style="grid-area: next"
          data-nav
          data-autofocus
          onclick={() => showSoon('Календарь и перемотка появятся в тикете #3')}
        >
          <div class="widget-head">
            <div>
              <span class="eyebrow">Далее</span>
              <strong class="widget-title">{monthLabel(career.date)}</strong>
            </div>
            <span class="soon-tag">нужен #3</span>
          </div>
          <div class="day-strip">
            {#each days as day (day.key)}
              <div class="day" class:today={day.today}>
                <span class="day-week">{day.weekday}</span>
                <span class="day-num">{day.day}</span>
              </div>
            {/each}
          </div>
          <div class="next-meta">
            <span>Сезон {seasonLabel(career.date)}</span>
            <span>{career.club.league_name}</span>
          </div>
          <div class="widget-action-bar is-disabled">
            <span>Продолжить</span>
            <span>после календаря</span>
          </div>
        </button>

        <section class="widget widget-centre is-soon" style="grid-area: centre">
          <div class="widget-head">
            <div>
              <span class="eyebrow">Переговоры</span>
              <strong class="widget-title">Центр трансферов</strong>
            </div>
            <span class="soon-tag">нужен #4</span>
          </div>
          <Icon name="shirt" size={76} />
          <p class="widget-note">Предложения, переговоры и подписания — после трансферного тикета.</p>
          <div class="widget-dots" aria-hidden="true"><i class="active"></i><i></i><i></i></div>
        </section>

        <section class="widget widget-table is-soon" style="grid-area: table">
          <div class="widget-head">
            <strong class="widget-title widget-title-sm">Таблицы</strong>
            <span class="soon-tag">нужен #3</span>
          </div>
          <Icon name="table" size={56} />
          <p class="widget-note">Место, очки и разница мячей появятся с календарём лиги.</p>
        </section>

        <section class="widget widget-news is-soon" style="grid-area: news">
          <div class="widget-head">
            <strong class="widget-title widget-title-sm">Срочные новости</strong>
            <span class="soon-tag">после #4</span>
          </div>
          <Icon name="news" size={68} />
          <p class="widget-note">Лента новостей и результаты матчей — после календаря и матчей.</p>
        </section>

        <section class="widget widget-training is-soon" style="grid-area: training">
          <div class="widget-head">
            <strong class="widget-title widget-title-sm">Тренировка</strong>
            <span class="soon-tag">после #4</span>
          </div>
          <Icon name="chart" size={56} />
          <p class="widget-note">До пяти тренировок в неделю: характеристики, рейтинг и стоимость.</p>
        </section>
      </div>
    {:else if tab === 'squad' && view === 'overview'}
      <div class="squad-overview">
        <button class="squad-team" data-nav data-autofocus onclick={() => openPlan()}>
          <div class="squad-team-head">
            <img class="squad-team-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
            <div class="squad-team-title">
              <span class="eyebrow">Состав клуба</span>
              <strong>{career.club.name}: по умолч.</strong>
              <span>{lineup.formation} · {career.club.league_name}</span>
            </div>
            <span class="widget-action">A · план игры</span>
          </div>

          <div class="pitch pitch-plan">
            <span class="pitch-surface"></span>
            <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <polygon points="13,2 87,2 98,98 2,98"></polygon>
              <line x1="7" y1="50" x2="93" y2="50"></line>
              <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
              <polygon points="33,2 67,2 70,18 30,18"></polygon>
              <polygon points="25,98 75,98 70,80 30,80"></polygon>
            </svg>
            {#each lineup.slots as slot (slot.position + slot.player.id)}
              <span
                class="pitch-player is-preview"
                style={`left:${pitchX(slot.x, slot.y)}%; top:${pitchY(slot.y)}%`}
              >
                <span class="player-photo">
                  <img src={slot.player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                </span>
                <span class="player-plate">
                  <span class="player-pos {posTone(slot.role)}">{shortRole(slot.role)}</span>
                  <span class="player-ovr">{Math.round(slot.player.overall)}</span>
                </span>
                <span class="player-name-wrap">
                  <span class="player-name">{playerInitialName(slot.player)}</span>
                </span>
                <span class="fatigue-bar"><i style={`width:${slot.player.fatigue}%`}></i></span>
              </span>
            {/each}
            {@render strengthBadge()}
          </div>

          <div class="squad-team-foot">
            <span>{summary.squad_size} игроков · средний возраст {summary.average_age ?? '—'}</span>
            <span>{formatValue(summary.total_market_value)}</span>
          </div>
        </button>

        <div class="squad-tiles">
          {#each squadTiles as tile (tile.id)}
            {#if tile.selected}
              <div class="squad-tile is-selected" aria-current="true">
                <span class="squad-tile-label">{tile.label}</span>
                <span class="squad-tile-icon">
                  <img src={career.club.logo} alt="" onerror={hideBrokenImage} />
                  <span class="squad-tile-check"><Icon name="check" size={14} /></span>
                </span>
                <span class="squad-tile-note">{career.club.name}</span>
              </div>
            {:else}
              <div class="squad-tile is-disabled" aria-disabled="true">
                <span class="squad-tile-label">{tile.label}</span>
                <span class="squad-tile-icon"><Icon name={tile.icon} size={44} /></span>
                <span class="squad-tile-note">{tile.note}</span>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {:else if tab === 'squad' && (view === 'plan' || view === 'details') && focusedPlayer}
      <div class="plan">
        <div class="plan-stage">
          <nav class="plan-tabs" aria-label="План игры">
            {#each planTabs as item (item.label)}
              <span class="plan-tab" class:active={item.active}>{item.label}</span>
            {/each}
          </nav>

          {#if comparing}
            <div class="player-head compare-head">
              {@render playerBlock(anchorPlayer, false)}
              {#if radar.length && focusedPlayer.role !== 'GK'}
                {@render radarChart(anchorRadar.length ? anchorRadar : radar, anchorRadar.length ? radar : null)}
              {:else}
                <span class="radar-empty">Вратарский профиль не входит в канон</span>
              {/if}
              {@render playerBlock(focusedPlayer, true)}
            </div>
          {:else}
            <div class="player-head">
              {@render playerBlock(focusedPlayer, false)}
              {#if radar.length && focusedPlayer.role !== 'GK'}
                {@render radarChart(radar)}
              {:else}
                <span class="radar-empty">Вратарский профиль не входит в канон</span>
              {/if}
            </div>
          {/if}

          {#if view === 'details'}
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
              {:else}
                <div class="details-list">
                  {#each detailGroups as group (group.id)}
                    <div class="details-group">
                      <span class="details-group-label">{group.label}</span>
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
                  {/each}
                </div>
              {/if}

              <div class="details-dots" aria-hidden="true">
                {#each detailPages as page, index (page.id)}
                  <i class:active={index === detailsPage}></i>
                {/each}
              </div>
            </section>
          {:else}
            <div class="pitch pitch-plan-large">
              <span class="pitch-surface"></span>
              <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                <polygon points="13,2 87,2 98,98 2,98"></polygon>
                <line x1="7" y1="50" x2="93" y2="50"></line>
                <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
                <polygon points="33,2 67,2 70,18 30,18"></polygon>
                <polygon points="25,98 75,98 70,80 30,80"></polygon>
              </svg>
              {#each lineup.slots as slot (slot.position + slot.player.id)}
                <button
                  class="pitch-player"
                  class:is-anchor={anchorId === slot.player.id}
                  data-nav
                  data-player={slot.player.id}
                  style={`left:${pitchX(slot.x, slot.y)}%; top:${pitchY(slot.y)}%`}
                  onfocus={(event) => {
                    focusPlayerId = slot.player.id
                    revealName(event)
                  }}
                  onmouseenter={revealName}
                  onclick={() => activatePlayer(slot.player)}
                >
                  <span class="player-photo">
                    <img src={slot.player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                  </span>
                  <span class="player-plate">
                    <span class="player-pos {posTone(slot.role)}">{shortRole(slot.role)}</span>
                    <span class="player-ovr">{Math.round(slot.player.overall)}</span>
                  </span>
                  <span class="player-name-wrap">
                    <span class="player-name">{playerInitialName(slot.player)}</span>
                  </span>
                  <span class="fatigue-bar"><i style={`width:${slot.player.fatigue}%`}></i></span>
                </button>
              {/each}
              {@render strengthBadge()}
            </div>

            <div class="bench-panel">
              <div class="bench-head">
                <strong>Запасные</strong>
                <span>{lineup.bench.length} игроков</span>
              </div>
              <div class="bench-row scroll-area">
                {#each lineup.bench as player (player.id)}
                  <button
                    class="bench-card"
                    class:is-anchor={anchorId === player.id}
                    data-nav
                    data-player={player.id}
                    onfocus={() => (focusPlayerId = player.id)}
                    onclick={() => activatePlayer(player)}
                  >
                    <span class="bench-top">
                      <span class="player-pos {posTone(player.role)}">{shortRole(player.role)}</span>
                      <span class="bench-ovr">{Math.round(player.overall)}</span>
                    </span>
                    <span class="bench-photo">
                      <img src={player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                    </span>
                    <span class="bench-name">{player.name}</span>
                    <span class="fatigue-bar"><i style={`width:${player.fatigue}%`}></i></span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>

        <div class="plan-crest" aria-hidden="true">
          <img src={career.club.logo} alt="" onerror={hideBrokenImage} />
        </div>
      </div>
    {/if}
  </main>

  <Controls
    {hints}
    showDefaults={false}
    note={saving ? 'Сохранение…' : swapping ? 'Обмен…' : `${career.club.name} · ${formatTimestamp(career.updated_at)}`}
  />
</div>
