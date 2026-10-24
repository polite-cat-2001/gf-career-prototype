<script>
  import { onMount, tick } from 'svelte'
  import { registerBack } from './actions.js'
  import Controls from './Controls.svelte'
  import { focusFirst } from './input.js'
  import { formatDate, formatTimestamp, hideBrokenImage } from './format.js'

  let { saves = [], error = '', onload, onback } = $props()

  onMount(() => {
    const stopBack = registerBack(onback)
    tick().then(focusFirst)
    return stopBack
  })
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">GF</div>
      <div>
        <div class="brand-title">Загрузить карьеру</div>
        <div class="brand-sub">Выберите сохранение</div>
      </div>
    </div>
    <div class="topbar-meta">
      <span class="pill"><strong>{saves.length}</strong> сохранений</span>
    </div>
  </header>

  <main class="screen load-screen">
    {#if error}
      <div class="notice error">{error}</div>
    {/if}

    <div class="load-list">
      {#if saves.length === 0}
        <div class="empty-state">
          <span class="empty-icon">—</span>
          <h2>Сохранений нет</h2>
          <p>Создайте новую карьеру в главном меню.</p>
        </div>
      {:else}
        {#each saves as save, index (save.id)}
          <button
            class="load-card"
            class:incompatible={!save.compatible}
            data-nav
            data-autofocus={index === 0 ? '' : undefined}
            onclick={() => onload(save.id)}
          >
            {#if save.club_logo}
              <img class="load-crest" src={save.club_logo} alt="" onerror={hideBrokenImage} />
            {:else}
              <span class="load-crest placeholder-crest">!</span>
            {/if}
            <span class="load-main">
              <span class="load-title">{save.club_name}</span>
              {#if save.compatible}
                <span class="load-sub">{save.manager_name} · {save.league_name} · {save.country_name}</span>
                <span class="load-meta">Дата карьеры: {formatDate(save.date)} · изменение: {formatTimestamp(save.updated_at)}</span>
              {:else}
                <span class="load-sub error-text">{save.problem}</span>
                <span class="load-meta">Версия сейва: {save.version}</span>
              {/if}
            </span>
            <span class="load-state">
              {#if save.compatible}
                <span class="pill subtle">{formatTimestamp(save.updated_at)}</span>
              {:else}
                <span class="pill danger">несовместим</span>
              {/if}
            </span>
          </button>
        {/each}
      {/if}
    </div>
  </main>

  <Controls hints={[]} />
</div>
