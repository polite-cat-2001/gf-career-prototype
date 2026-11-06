<script>
  import Icon from '../../Icon.svelte'
  import PlayerPhoto from '../../ui/PlayerPhoto.svelte'
  import { shortDate } from '../../format.js'
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
    <header class="tf-reports-head">
      <div class="tf-reports-heading">
        <span class="tf-reports-kicker">Скаутинг</span>
        <strong class="tf-reports-title">Отчёты скаутов</strong>
      </div>
      <div class="tf-reports-count">
        <span><b>{scouting?.counts?.new ?? 0}</b> Новое</span>
        <span><b>{scouting?.counts?.updates ?? 0}</b> Обновления</span>
      </div>
    </header>

    <div class="tf-scout-feed">
      {#each reportPageEntries as entry, index (entry.player.id)}
        <div class="tf-scout-item">
          <span class="tf-scout-photo">
            <PlayerPhoto src={entry.player.photo} />
          </span>
          <span class="tf-scout-main">
            <strong>{entry.player.name}</strong>
            <span class="tf-scout-club">{entry.player.club_name ?? 'Свободный агент'}</span>
            <span class="tf-scout-meta">{entry.scout_name} · {shortDate(entry.date)}</span>
          </span>
          <span class="tf-scout-ovr">
            <b>{Math.round(entry.player.overall ?? 0)}</b>
            <small>ОБЩ.</small>
          </span>
          {#if !entry.acknowledged}
            <i class="tf-scout-new" title="Новый"></i>
          {/if}
        </div>
      {/each}
      {#if reportPageEntries.length < 6}
        {#each Array(6 - reportPageEntries.length) as _, index (index)}
          <div class="tf-scout-item is-empty">
            <Icon name="users" size={28} />
            <span>Свободный слот</span>
          </div>
        {/each}
      {/if}
    </div>

    <footer class="tf-reports-foot">
      <p>
        {#if feedCount}
          {reportPage + 1} / {reportPageCount}
        {:else}
          Скаутских отчётов пока нет. Назначьте скаута в поиске игроков.
        {/if}
      </p>
      {#if reportPageCount > 1}
        <div class="tf-scout-pager">
          <button
            class="tf-scout-arrow"
            type="button"
            tabindex="-1"
            aria-label="Предыдущая страница"
            onclick={(event) => {
              event.stopPropagation()
              onShiftReport('left')
            }}>‹</button
          >
          <button
            class="tf-scout-arrow"
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
    </footer>
  </div>

  {#each cards as card (card.id)}
    <TransferHubCard {card} onOpen={() => onOpenCard(card)} />
  {/each}
</div>
