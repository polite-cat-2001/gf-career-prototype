<script>
  import {
    hideBrokenImage,
    playerInitialName,
    positionLabel,
    shortRole,
    statusLabel,
  } from '../../format.js'

  let { player, eyebrow = '' } = $props()
</script>

<div class="centre-profile">
  <span class="centre-photo">
    <img src={player.photo} alt="" onerror={hideBrokenImage} />
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
