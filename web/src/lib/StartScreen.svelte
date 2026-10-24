<script>
  import { onMount, tick } from 'svelte'
  import Controls from './Controls.svelte'
  import { focusFirst } from './input.js'
  import { formatDate, formatTimestamp, hideBrokenImage } from './format.js'

  let {
    latest = null,
    savesCount = 0,
    loading = false,
    error = '',
    oncontinue,
    onnew,
    onload,
  } = $props()

  onMount(() => {
    tick().then(focusFirst)
  })

  $effect(() => {
    if (!loading) tick().then(focusFirst)
  })

  function careerWord(count) {
    if (count % 10 === 1 && count % 100 !== 11) return 'карьера'
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'карьеры'
    return 'карьер'
  }
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Career Mode</div>
        <div class="brand-sub">Прототип карьеры менеджера</div>
      </div>
    </div>
    <div class="topbar-meta">
      <span class="pill"><strong>canon.db</strong> реальные данные</span>
      {#if latest}
        <span class="pill"><strong>{formatTimestamp(latest.updated_at)}</strong> последний сейв</span>
      {/if}
    </div>
  </header>

  <main class="screen start-screen">
    <div class="start-heading">
      <span class="eyebrow">GameplayFootball</span>
      <h1>Карьера менеджера</h1>
      <p>Выберите, с чего продолжить. Управление — геймпад или клавиатура.</p>
    </div>

    {#if error}
      <div class="notice error">{error}</div>
    {/if}

    <div class="start-grid">
      <button
        class="start-card"
        data-nav
        disabled={!latest || loading}
        onclick={oncontinue}
      >
        <span class="start-card-head">
          <span class="start-card-title">Продолжить</span>
          <span class="start-card-action">
            {#if latest}Последний сейв{:else}Нет сохранений{/if}
          </span>
        </span>

        {#if latest}
          <span class="start-card-body">
            <img class="club-crest" src={latest.club_logo} alt="" onerror={hideBrokenImage} />
            <span class="start-card-name">{latest.club_name}</span>
            <span class="start-card-sub">{latest.manager_name}</span>
            <span class="start-card-meta">{latest.league_name} · {formatDate(latest.date)}</span>
          </span>
        {:else}
          <span class="start-card-empty">
            <span class="empty-icon">—</span>
            <span>Сначала создайте новую карьеру</span>
          </span>
        {/if}
      </button>

      <button class="start-card" data-nav onclick={onnew}>
        <span class="start-card-head">
          <span class="start-card-title">Новая игра</span>
          <span class="start-card-action">Создать</span>
        </span>
        <span class="start-card-body">
          <span class="big-plus">+</span>
          <span class="start-card-sub">Страна, лига, клуб и менеджер</span>
          <span class="start-card-meta">Случайный seed · автосохранение</span>
        </span>
      </button>

      <button
        class="start-card"
        data-nav
        disabled={savesCount === 0}
        onclick={onload}
      >
        <span class="start-card-head">
          <span class="start-card-title">Загрузить</span>
          <span class="start-card-action">{savesCount} {careerWord(savesCount)}</span>
        </span>
        <span class="start-card-body">
          <span class="menu-lines" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="start-card-sub">Список существующих карьер</span>
          <span class="start-card-meta">Выбор → загрузка сейва</span>
        </span>
      </button>
    </div>
  </main>

  <Controls hints={[]} note="Сервер — единственный источник истины" />
</div>
