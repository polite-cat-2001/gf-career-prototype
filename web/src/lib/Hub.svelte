<script>
  import { onMount, tick } from 'svelte'
  import { registerBack, registerSave, registerTabs } from './actions.js'
  import Controls from './Controls.svelte'
  import Tabs from './Tabs.svelte'
  import { focusFirst, inputDevice } from './input.js'
  import {
    formatDate,
    formatNumber,
    formatTimestamp,
    formatValue,
    hideBrokenImage,
    initials,
    ovrClass,
    roleLabel,
    tierLabel,
  } from './format.js'

  let {
    career,
    saving = false,
    saveNotice = '',
    saveError = '',
    onsave,
    onexit,
  } = $props()

  const tabs = [
    { id: 'home', label: 'Главная' },
    { id: 'squad', label: 'Состав' },
    { id: 'transfers', label: 'Трансферы', disabled: true },
    { id: 'academy', label: 'Академия', disabled: true },
    { id: 'office', label: 'Офис', disabled: true },
  ]
  const enabledTabs = tabs.filter((tab) => !tab.disabled).map((tab) => tab.id)

  let tab = $state('home')
  let detail = $state(false)
  let selectedPlayerId = $state(null)

  let summary = $derived(career.squad.summary)
  let groups = $derived(career.squad.groups)
  let lineup = $derived(career.squad.lineup)
  let allPlayers = $derived([
    ...lineup.slots.map((slot) => slot.player),
    ...lineup.bench,
  ])
  let selectedPlayer = $derived(
    allPlayers.find((player) => player.id === selectedPlayerId) ?? lineup.slots[0]?.player ?? null,
  )
  let hints = $derived([
    { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Разделы' },
    { gamepad: ['Start'], keyboard: ['S'], label: 'Сохранить' },
  ])
  let confirmKey = $derived($inputDevice === 'gamepad' ? 'A' : 'Enter')

  onMount(() => {
    const stopBack = registerBack(handleBack)
    const stopTabs = registerTabs(switchTab)
    const stopSave = registerSave(handleSave)
    tick().then(focusFirst)
    return () => {
      stopBack()
      stopTabs()
      stopSave()
    }
  })

  async function handleSave() {
    if (!saving) onsave()
  }

  function handleBack() {
    if (detail) {
      closeDetail()
      return
    }
    if (tab !== 'home') {
      setTab('home')
      return
    }
    onexit()
  }

  async function setTab(next) {
    if (!enabledTabs.includes(next)) return
    tab = next
    detail = false
    await tick()
    focusFirst()
  }

  function switchTab(direction) {
    const index = enabledTabs.indexOf(tab)
    const offset = direction === 'right' ? 1 : -1
    const next = enabledTabs[(index + offset + enabledTabs.length) % enabledTabs.length]
    setTab(next)
  }

  async function openDetail() {
    detail = true
    selectedPlayerId = lineup.slots[0]?.player.id ?? null
    await tick()
    focusFirst()
  }

  async function closeDetail() {
    detail = false
    await tick()
    focusFirst()
  }

  function selectPlayer(player) {
    selectedPlayerId = player.id
  }

  function pitchX(x, y) {
    return 50 + (x - 50) * (0.62 + 0.38 * (y / 100))
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
        <div class="strip-meta">{formatDate(career.date)} · seed {formatNumber(career.seed)}</div>
      </div>
    </div>
  </header>

  <main class="screen hub-screen">
    {#if saveError}
      <div class="notice error">{saveError}</div>
    {:else if saveNotice}
      <div class="notice">{saveNotice}</div>
    {/if}

    {#if tab === 'home'}
      <div class="home-layout">
        <section class="home-hero">
          <div class="home-hero-top">
            <img class="home-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
            <div>
              <span class="eyebrow">{career.club.country_name} · {career.club.league_name}</span>
              <h1>{career.club.name}</h1>
              <p>{career.manager.name} · {career.manager.nationality}</p>
            </div>
          </div>

          <div class="home-stats">
            <div class="stat-card">
              <span>Состав</span>
              <strong>{summary.squad_size}</strong>
              <small>{groups.length} групп</small>
            </div>
            <div class="stat-card">
              <span>Средний OVR</span>
              <strong>{summary.average_overall}</strong>
              <small>стартовый состав</small>
            </div>
            <div class="stat-card">
              <span>Средний возраст</span>
              <strong>{summary.average_age ?? '—'}</strong>
              <small>лет</small>
            </div>
            <div class="stat-card">
              <span>Стоимость</span>
              <strong>{formatValue(summary.total_market_value)}</strong>
              <small>суммарно</small>
            </div>
          </div>

          <button class="home-action" data-nav data-autofocus onclick={() => setTab('squad')}>
            <span class="eyebrow">Состав</span>
            <span class="home-action-title">Открыть поле и замены</span>
            <span class="home-action-arrow">→</span>
          </button>

          <div class="placeholder-strip">
            <div>
              <span class="detail-label">Ближайший матч</span>
              <strong>Календарь появится в тикете #3</strong>
            </div>
            <div>
              <span class="detail-label">Новости</span>
              <strong>Лента появится позже</strong>
            </div>
            <div>
              <span class="detail-label">Таблица</span>
              <strong>Лига подключится в тикете #3</strong>
            </div>
          </div>
        </section>

        <aside class="home-side">
          <div class="side-card">
            <span class="detail-label">Клуб</span>
            <strong>{career.club.name}</strong>
            <span>{tierLabel(career.club)} · {career.club.league_name}</span>
          </div>
          <div class="side-card">
            <span class="detail-label">Стадион</span>
            <strong>{career.club.stadium.name || '—'}</strong>
            <span>{career.club.stadium.seats ? `${formatNumber(career.club.stadium.seats)} мест` : 'Вместимость неизвестна'}</span>
          </div>
          <div class="side-card">
            <span class="detail-label">Менеджер</span>
            <strong>{career.manager.name}</strong>
            <span>{career.manager.nationality}</span>
          </div>
          <div class="side-card">
            <span class="detail-label">Сейв</span>
            <strong>{saving ? 'Сохраняем…' : 'Автосейв включён'}</strong>
            <span>изменён {formatTimestamp(career.updated_at)}</span>
          </div>
        </aside>
      </div>
    {:else if tab === 'squad' && !detail}
      <div class="squad-widget-layout">
        <button class="squad-widget" data-nav data-autofocus onclick={openDetail}>
          <span class="widget-head">
            <span>
              <span class="eyebrow">Стартовый состав</span>
              <strong>{lineup.formation}</strong>
            </span>
            <span class="widget-action">{confirmKey} · управление составом</span>
          </span>

          <span class="pitch pitch-preview">
            <span class="pitch-surface"></span>
            <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <polygon points="13,2 87,2 98,98 2,98"></polygon>
              <line x1="7" y1="50" x2="93" y2="50"></line>
              <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
              <polygon points="33,2 67,2 70,18 30,18"></polygon>
              <polygon points="25,98 75,98 70,80 30,80"></polygon>
            </svg>
            {#each lineup.slots as slot}
              <span class="preview-player" style={`left:${pitchX(slot.x, slot.y)}%; top:${slot.y}%`}>
                <span class="player-photo">
                  <img src={slot.player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                </span>
                <span class="player-strip">
                  <span class="player-rating">{Math.round(slot.player.overall)}</span>
                  <span class="fatigue-bar"><i style={`width:${slot.player.fatigue}%`}></i></span>
                </span>
                <span class="preview-name">{slot.player.name}</span>
              </span>
            {/each}
          </span>

          <span class="widget-foot">
            <span>{summary.squad_size} игроков · средний OVR {summary.average_overall}</span>
            <span>Нажмите {confirmKey}, чтобы открыть поле и замены</span>
          </span>
        </button>
      </div>
    {:else if tab === 'squad' && detail}
      <div class="squad-detail">
        <div class="squad-play">
          <div class="detail-title-row">
            <div>
              <span class="eyebrow">Team Management</span>
              <h1>Состав · {lineup.formation}</h1>
            </div>
            <span class="pill">{summary.squad_size} игроков</span>
          </div>

          <div class="pitch pitch-large">
            <span class="pitch-surface"></span>
            <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <polygon points="13,2 87,2 98,98 2,98"></polygon>
              <line x1="7" y1="50" x2="93" y2="50"></line>
              <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
              <polygon points="33,2 67,2 70,18 30,18"></polygon>
              <polygon points="25,98 75,98 70,80 30,80"></polygon>
            </svg>
            {#each lineup.slots as slot, index (slot.position + slot.player.id)}
              <button
                class="pitch-player"
                class:selected={selectedPlayer?.id === slot.player.id}
                data-nav
                data-autofocus={index === 0 ? '' : undefined}
                style={`left:${pitchX(slot.x, slot.y)}%; top:${slot.y}%`}
                onfocus={() => selectPlayer(slot.player)}
                onclick={() => selectPlayer(slot.player)}
              >
                <span class="player-photo">
                  <img src={slot.player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                </span>
                <span class="player-strip">
                  <span class="player-rating">{Math.round(slot.player.overall)}</span>
                  <span class="fatigue-bar"><i style={`width:${slot.player.fatigue}%`}></i></span>
                </span>
                <span class="pitch-name">{slot.player.name}</span>
              </button>
            {/each}
          </div>

          <div class="bench-panel">
            <div class="bench-head">
              <strong>Запасные</strong>
              <span>{lineup.bench.length} игроков</span>
            </div>
            <div class="bench-grid">
              {#each lineup.bench as player (player.id)}
                <button
                  class="bench-player"
                  class:selected={selectedPlayer?.id === player.id}
                  data-nav
                  onfocus={() => selectPlayer(player)}
                  onclick={() => selectPlayer(player)}
                >
                  <span class="bench-rating {ovrClass(player.overall)}">{Math.round(player.overall)}</span>
                  <span class="bench-photo">
                    <img src={player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
                  </span>
                  <span class="bench-name">{player.name}</span>
                  <span class="bench-pos">{player.role || '—'}</span>
                </button>
              {/each}
            </div>
          </div>
        </div>

        {#if selectedPlayer}
          <aside class="player-panel">
            <div class="player-card-head">
              <span class="player-photo-large">
                <img src={selectedPlayer.photo} alt="" onerror={hideBrokenImage} />
              </span>
              <div class="player-card-rating {ovrClass(selectedPlayer.overall)}">
                {Math.round(selectedPlayer.overall)}
              </div>
              <div>
                <span class="player-card-name">{selectedPlayer.name}</span>
                <span class="player-card-sub">{selectedPlayer.position} · {selectedPlayer.citizenship[0] || '—'}</span>
              </div>
            </div>

            <div class="player-info-grid">
              <div><span>Возраст</span><strong>{selectedPlayer.age ?? '—'}</strong></div>
              <div><span>Рост</span><strong>{selectedPlayer.height ? `${selectedPlayer.height} см` : '—'}</strong></div>
              <div><span>Нога</span><strong>{selectedPlayer.foot || '—'}</strong></div>
              <div><span>Номер</span><strong>{selectedPlayer.shirt_number ?? '—'}</strong></div>
              <div><span>Потенциал</span><strong>{selectedPlayer.pot}</strong></div>
              <div><span>Стоимость</span><strong>{formatValue(selectedPlayer.market_value)}</strong></div>
              <div><span>Роль</span><strong>{roleLabel(selectedPlayer.role) || '—'}</strong></div>
              <div><span>Позиция</span><strong>{selectedPlayer.position}</strong></div>
            </div>

            <div class="player-init">
              <span class="initials">{initials(selectedPlayer.name)}</span>
              <span>
                <strong>{selectedPlayer.first_name} {selectedPlayer.last_name}</strong>
                <span>Профиль и развитие — в следующих тикетах.</span>
              </span>
            </div>
          </aside>
        {/if}
      </div>
    {/if}
  </main>

  <Controls
    {hints}
    note={saving ? 'Сохранение…' : `${career.club.name} · ${formatTimestamp(career.updated_at)}`}
  />
</div>
