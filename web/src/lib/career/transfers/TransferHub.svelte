<script>
  import Icon from '../../Icon.svelte'
  import { hideBrokenImage, shortDate } from '../../format.js'
  import TransferHubCard from './TransferHubCard.svelte'

  let {
    scouting,
    reportPageEntries,
    reportPage,
    reportPageCount,
    feedCount,
    cards,
    onOpenReports,
    onShiftReport,
    onOpenCard,
  } = $props()
</script>

<div class="tf-hub">
  <div
    class="tf-reports"
    role="button"
    tabindex="0"
    aria-label="Отчёты скаутов — открыть"
    data-nav
    data-autofocus
    onclick={onOpenReports}
  >
    <div class="tf-reports-head">
      <strong>Отчёты скаутов</strong>
      <div class="tf-reports-count">
        <span><b>{scouting?.counts?.new ?? 0}</b> Новое</span>
        <span><b>{scouting?.counts?.updates ?? 0}</b> Обновления</span>
      </div>
    </div>
    <div class="tf-report-feed">
      {#each reportPageEntries as entry, index (entry.player.id)}
        <div class="tf-report-tile">
          <span class="tf-report-photo">
            <img src={entry.player.photo} alt="" onerror={hideBrokenImage} />
          </span>
          <span class="tf-report-main">
            <strong>{entry.player.name}</strong>
            <span class="tf-report-club">{entry.player.club_name ?? 'Свободный агент'}</span>
            <span class="tf-report-meta">{entry.scout_name} · {shortDate(entry.date)}</span>
          </span>
          <span class="tf-report-ovr">
            <b>{Math.round(entry.player.overall ?? 0)}</b>
            <small>ОБЩ.</small>
          </span>
          {#if !entry.acknowledged}
            <i class="tf-report-new" title="Новый"></i>
          {/if}
        </div>
      {/each}
      {#if reportPageEntries.length < 6}
        {#each Array(6 - reportPageEntries.length) as _, index (index)}
          <div class="tf-report-tile is-empty">
            <Icon name="users" size={22} />
            <span>—</span>
          </div>
        {/each}
      {/if}
    </div>
    <div class="tf-reports-foot">
      <p>
        {#if feedCount}
          {reportPage + 1} / {reportPageCount}
        {:else}
          Скаутских отчётов пока нет. Назначьте скаута в поиске игроков.
        {/if}
      </p>
      {#if reportPageCount > 1}
        <div class="tf-report-pager">
          <button
            class="tf-report-arrow"
            type="button"
            tabindex="-1"
            aria-label="Предыдущая страница"
            onclick={(event) => {
              event.stopPropagation()
              onShiftReport('left')
            }}>‹</button
          >
          <button
            class="tf-report-arrow"
            type="button"
            tabindex="-1"
            aria-label="Следующая страница"
            onclick={(event) => {
              event.stopPropagation()
              onShiftReport('right')
            }}>›</button
          >
        </div>
      {/if}
    </div>
  </div>
  {#each cards as card (card.id)}
    <TransferHubCard {card} onOpen={() => onOpenCard(card)} />
  {/each}
</div>
