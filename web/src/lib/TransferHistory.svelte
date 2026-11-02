<script>
  import { onMount, tick } from 'svelte'
  import { registerBack, registerTabs } from './actions.js'
  import { focusFirst } from './input.js'
  import {
    formatValue,
    hideBrokenImage,
    shortDate,
    shortRole,
  } from './format.js'

  let { career, onclose = () => {}, hints = $bindable([]) } = $props()

  const FILTERS = [
    { id: 'all', label: 'Все лиги' },
    { id: 'league', label: 'Моя лига' },
    { id: 'club', label: 'Мой клуб' },
  ]

  const STATUS_LABELS = {
    completed: 'Завершено',
    agreed: 'Согласовано',
    signed: 'Подписано',
    pending: 'Ожидает',
    accepted: 'Принято',
    refused: 'Отклонено',
    counter: 'Контрпредложение',
    expired: 'Истекло',
  }

  let filter = $state('all')

  let entries = $derived(career.transfers?.history ?? [])

  let rows = $derived.by(() => {
    const filtered = entries.filter((entry) => {
      if (filter === 'league') return entry.in_my_league
      if (filter === 'club') return entry.with_manager
      return true
    })
    return filtered.slice().sort((left, right) => {
      const rating = Number(right.overall || 0) - Number(left.overall || 0)
      if (rating) return rating
      return String(right.date || '').localeCompare(String(left.date || ''))
    })
  })

  let hintList = $derived([
    { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Навигация' },
    { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Фильтр' },
    { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
  ])

  $effect(() => {
    hints = hintList
  })

  function statusLabel(status) {
    return STATUS_LABELS[status] || status || '—'
  }

  function setFilter(next) {
    if (filter === next) return
    filter = next
    tick().then(() => {
      const tab = document.querySelector(
        `.tf-history-tab[data-history-tab="${filter}"]`,
      )
      if (tab) tab.focus({ preventScroll: true })
      else focusFirst()
    })
  }

  function cycleFilter(direction) {
    const index = FILTERS.findIndex((item) => item.id === filter)
    const next =
      (index + (direction === 'right' ? 1 : -1) + FILTERS.length) %
      FILTERS.length
    setFilter(FILTERS[next].id)
  }

  function handleBack() {
    onclose()
  }

  function handleTabs(direction) {
    cycleFilter(direction)
  }

  onMount(() => {
    const stopBack = registerBack(handleBack)
    const stopTabs = registerTabs(handleTabs)
    tick().then(focusFirst)
    return () => {
      stopBack()
      stopTabs()
    }
  })
</script>

<div class="tf-history">
  <header class="tf-filters-head">
    <span class="tf-crumbs">Трансферы <i>›</i> История</span>
    <span class="tf-crumbs-note">Сортировка по рейтингу на момент перехода</span>
  </header>

  <nav class="centre-tabs tf-history-tabs" aria-label="Фильтр истории">
    {#each FILTERS as item (item.id)}
      <button
        class="centre-tab tf-history-tab"
        class:active={filter === item.id}
        data-nav
        data-autofocus={filter === item.id ? '' : undefined}
        data-history-tab={item.id}
        onclick={() => setFilter(item.id)}
      >
        {item.label}
      </button>
    {/each}
  </nav>

  <div class="tf-history-list scroll-area">
    {#each rows as entry (entry.id)}
      <button
        type="button"
        class="tf-history-row"
        class:is-world={entry.source === 'world'}
        data-nav
        aria-label={`${entry.player_name}: ${entry.from_club_name || 'Свободный агент'} — ${entry.to_club_name}`}
      >
        <span class="tf-history-photo">
          {#if entry.photo}
            <img src={entry.photo} alt="" onerror={hideBrokenImage} />
          {/if}
        </span>
        <span class="tf-history-main">
          <strong>{entry.player_name}</strong>
          <span class="tf-history-player-meta">
            {shortRole(entry.role)} · {entry.age ?? '—'} лет
          </span>
        </span>
        <span class="tf-history-clubs">
          <span class="tf-history-club">
            {#if entry.from_club_logo}
              <img src={entry.from_club_logo} alt="" onerror={hideBrokenImage} />
            {/if}
            <span>{entry.from_club_name || 'Свободный агент'}</span>
          </span>
          <i>→</i>
          <span class="tf-history-club is-to">
            {#if entry.to_club_logo}
              <img src={entry.to_club_logo} alt="" onerror={hideBrokenImage} />
            {/if}
            <span>{entry.to_club_name || '—'}</span>
          </span>
        </span>
        <span class="tf-history-fee">{formatValue(entry.fee)}</span>
        <span class="tf-history-rating">
          <b>{Math.round(entry.overall ?? 0)}</b>
          <small>ОБЩ.</small>
        </span>
        <span class="tf-history-meta">
          <span>{shortDate(entry.date)}</span>
          <span class="tf-history-status" class:is-done={entry.status === 'completed'}>
            {statusLabel(entry.status)}
          </span>
        </span>
      </button>
    {/each}

    {#if !rows.length}
      <div class="tf-history-empty">
        <strong>Сделок пока нет</strong>
        <span>
          Подходящие переходы появятся здесь, когда клубы начнут работу на трансферном
          рынке.
        </span>
      </div>
    {/if}
  </div>
</div>
