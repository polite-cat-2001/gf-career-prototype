<script>
  import {
    playerInitialName,
    positionLabel,
    shortRole,
    statusLabel,
  } from '../../format.js'
  import PlayerPhoto from '../../ui/PlayerPhoto.svelte'

  let { player, eyebrow = '' } = $props()
</script>

<div class="centre-profile">
  <span class="centre-photo">
    <PlayerPhoto src={player.photo} />
    {#if player.injury}
      <span
        class="player-status-flag"
        class:is-injury={Boolean(player.injury)}
        title={statusLabel(player)}
      >
        +
      </span>
    {/if}
  </span>
  <div class="centre-profile-info">
    <span class="centre-kicker">{eyebrow}</span>
    <strong class="centre-name">{playerInitialName(player)}</strong>
    <span class="centre-sub">
      {positionLabel(player.position)} · {shortRole(player.role)} ·
      {Math.round(player.overall)} OVR
    </span>
  </div>
</div>
