<script>
  import {
    hideBrokenImage,
    ovrClass,
    playerInitialName,
    posTone,
    shortRole,
    statusLabel,
  } from '../../format.js'
  import { currentRole, ratingAt, targetInfo } from '../utils/squad.js'

  let { player, mirrored = false, comparing, anchorPlayer, focusedPlayer, lineup } = $props()

  let target = $derived(targetInfo(player, comparing, anchorPlayer, focusedPlayer, lineup))
  let role = $derived(currentRole(lineup, player))
</script>

<div class="head-side" class:mirrored={mirrored}>
  <div class="head-photo-block">
    <span class="player-photo-large">
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
    <span class="photo-fatigue" title={`Кондиция ${player.fatigue}%`}>
      <span class="fatigue-bar" class:is-low={player.fatigue < 50}>
        <i style={`width:${player.fatigue}%`}></i>
      </span>
    </span>
  </div>
  <div class="head-info" class:right={mirrored}>
    <div class="head-name-row">
      {#if player.shirt_number}
        <span class="head-number">{player.shirt_number}</span>
      {/if}
      <strong class="head-name">{playerInitialName(player)}</strong>
    </div>
    <div class="head-rating-row">
      <span class="pos-badge {posTone(role)}">{shortRole(role)}</span>
      <strong class="head-ovr {ovrClass(ratingAt(player, role))}">{ratingAt(player, role)}</strong>
      <span class="head-shift">›</span>
      {#if target}
        <span class="pos-badge {posTone(target.role)}">{shortRole(target.role)}</span>
        <strong class="head-ovr {ovrClass(target.rating)}">{target.rating}</strong>
        {#if target.delta > 0}
          <span class="rating-delta up">▲</span>
        {:else if target.delta < 0}
          <span class="rating-delta down">▼</span>
        {/if}
      {:else}
        <span class="rating-dash">–</span>
      {/if}
    </div>
    <div class="head-season">
      <span>{player.season_stats?.apps ?? 0} М</span>
      <span>{player.season_stats?.goals ?? 0} Г</span>
      <span>{player.season_stats?.assists ?? 0} А</span>
      <span>{player.season_stats?.minutes ?? 0} мин</span>
    </div>
  </div>
</div>
