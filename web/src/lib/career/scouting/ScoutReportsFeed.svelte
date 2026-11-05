<script>
  import Icon from '../../Icon.svelte'
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    plural,
    posTone,
    shortRole,
    statTone,
  } from '../../format.js'
  import ScoutReportCard from './ScoutReportCard.svelte'

  let {
    filter,
    filters,
    scoutFilter,
    entries,
    selectedEntry,
    failedPhotos,
    entryActionsOpen,
    onFilter,
    onFocusEntry,
    onOpenEntry,
    onEntryFail,
    scoutName,
    footLabel,
    positionLabel,
    playerStatRows,
  } = $props()
</script>

<div class="sc-body sc-reports">
  <section class="sc-report-main" inert={entryActionsOpen ? true : undefined}>
    <div class="sc-report-toolbar">
      <div class="sc-report-tabs">
        {#each filters as tab (tab.id)}
          <button
            class="sc-tab"
            class:is-active={filter === tab.id}
            data-nav
            onclick={() => onFilter(tab.id)}
          >
            {tab.label}
          </button>
        {/each}
      </div>
      {#if scoutFilter}
        <span class="sc-filter-note">{scoutName(scoutFilter)}</span>
      {/if}
    </div>

    <div class="sc-entry-list scroll-area" data-nav-grid>
      {#each entries as entry, index (entry.player.id)}
        <ScoutReportCard
          {entry}
          selected={selectedEntry?.player.id === entry.player.id}
          autofocus={index === 0}
          failed={Boolean(failedPhotos[entry.player.id])}
          onFocus={() => onFocusEntry(entry.player.id)}
          onOpen={() => onOpenEntry(entry)}
          onFail={() => onEntryFail(entry.player.id)}
        />
      {/each}
      {#if !entries.length}
        <div class="sc-empty">
          {#if filter === 'requests'}
            <p>Отчётов по запросу пока нет.</p>
            <span>Откройте карточку игрока в поиске и выберите «Поручить скауту».</span>
          {:else if filter === 'all'}
            <p>Скауты пока ничего не рекомендуют.</p>
            <span>Создайте сеть поиска в стране, и скаут начнёт присылать игроков.</span>
          {:else}
            <p>По этой позиции пока никого нет.</p>
            <span>Измените фильтр или дождитесь новых отчётов скаутов.</span>
          {/if}
        </div>
      {/if}
    </div>
  </section>

  <aside class="sc-report-detail" inert={entryActionsOpen ? true : undefined}>
    {#if selectedEntry}
      {@const player = selectedEntry.player}
      <div class="sc-report-top">
        <span
          class="sc-report-photo"
          class:is-empty={!player.photo || failedPhotos[player.id]}
        >
          {#if !player.photo || failedPhotos[player.id]}
            <span class="sc-entry-photo-fallback">
              <Icon name="users" size={36} />
            </span>
          {:else}
            <img src={player.photo} alt="" onerror={() => onEntryFail(player.id)} />
          {/if}
        </span>
        <div class="sc-report-info">
          {#if !selectedEntry.acknowledged}
            <span class="sc-report-badge">Новый</span>
          {:else if selectedEntry.kind === 'recommendation'}
            <span class="sc-report-badge is-soft">Рекомендация</span>
          {:else}
            <span class="sc-report-badge is-soft">Отчёт</span>
          {/if}
          <strong class="sc-report-name">{player.name}</strong>
          <div class="sc-report-facts">
            <span>Лет <b>{player.age ?? '—'}</b></span>
            <span>Амплуа <b>{shortRole(player.role)}</b></span>
            <span>Рост <b>{player.height ? `${player.height} см` : '—'}</b></span>
            <span>Нога <b>{footLabel(player.foot)}</b></span>
          </div>
          <div class="sc-report-traits">{positionLabel(player.position)}</div>
        </div>
        <span class="sc-report-club">
          {#if player.club_logo}
            <img src={player.club_logo} alt="" onerror={hideBrokenImage} />
          {/if}
          <span>{player.club_name ?? 'Свободный агент'}</span>
        </span>
      </div>

      <div class="sc-report-ovr">
        <span>ОБЩ.</span>
        <strong class={statTone(player.overall ?? 0)}>{Math.round(player.overall ?? 0)}</strong>
        <span>ПОТ. <b class={statTone(player.pot ?? 0)}>{player.pot ?? '—'}</b></span>
      </div>

      <div class="sc-report-traits-center">
        <div class="sc-trait-item">
          <span>Слабая нога</span>
          <b class="sc-trait-stars">
            {#each [0, 1, 2, 3, 4] as star (star)}
              <i class:on={star < (player.weak_foot ?? 0)}>★</i>
            {/each}
          </b>
        </div>
        <div class="sc-trait-item">
          <span>Финты</span>
          <b class="sc-trait-stars">
            {#each [0, 1, 2, 3, 4] as star (star)}
              <i class:on={star < (player.skill_moves ?? 0)}>★</i>
            {/each}
          </b>
        </div>
      </div>

      <div class="sc-report-grid">
        <div class="sc-report-column">
          <div class="sc-report-head">Финансы</div>
          <div class="sc-money-list">
            <div>
              <span>Зарплата</span>
              <b>{formatValue(player.weekly_wage ?? 0)} <small>/ нед.</small></b>
            </div>
            <div>
              <span>Стоимость</span>
              <b>{formatValue(player.market_value ?? 0)}</b>
            </div>
            <div>
              <span>Отступные</span>
              <b class="is-accent">{formatValue(player.release_clause ?? 0)}</b>
            </div>
          </div>
        </div>
        <div class="sc-report-column">
          <div class="sc-report-head">Сводка</div>
          <ul class="sc-stat-list">
            {#each playerStatRows(player) as row (row.key)}
              <li>
                <span>{row.label}</span>
                <b class={statTone(row.value)}>{row.value}</b>
              </li>
            {/each}
          </ul>
        </div>
      </div>

      <div class="sc-report-foot">
        <span>
          <Icon name="check" size={14} />
          {selectedEntry.kind === 'report' ? 'Отчёт готов' : 'Игрок изучен'}
          · {selectedEntry.scout_name} · {formatDate(selectedEntry.date)}
        </span>
      </div>
    {:else}
      <p class="sc-panel-muted">Выберите игрока в списке.</p>
    {/if}
  </aside>
</div>
