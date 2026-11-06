<script>
  import PlayerPhoto from '../../ui/PlayerPhoto.svelte'
  import { hideBrokenImage, plural, posTone, shortRole } from '../../format.js'

  let { entry, selected = false, autofocus = false, onFocus, onOpen } = $props()
</script>

<button
  class="sc-entry"
  class:is-selected={selected}
  data-nav
  data-entry={entry.player.id}
  data-autofocus={autofocus ? '' : undefined}
  onfocus={onFocus}
  onclick={onOpen}
>
  <span class="sc-entry-photo">
    <PlayerPhoto src={entry.player.photo} />
  </span>
  <span class="sc-entry-main">
    <strong>{entry.player.name}</strong>
    <span class="sc-entry-meta">
      {entry.player.age ?? '—'}
      {plural(entry.player.age ?? 0, 'год', 'года', 'лет')}
      <i class="pos-badge {posTone(entry.player.role)}">{shortRole(entry.player.role)}</i>
    </span>
  </span>
  <span class="sc-entry-side">
    {#if !entry.acknowledged}<i class="sc-new" title="Новый"></i>{/if}
    <b class="sc-entry-ovr">{Math.round(entry.player.overall ?? 0)}</b>
    {#if entry.player.club_logo}
      <img
        class="sc-entry-crest"
        src={entry.player.club_logo}
        alt=""
        onerror={hideBrokenImage}
      />
    {/if}
  </span>
</button>
