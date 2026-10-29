<script>
  import {
    hideBrokenImage,
    posTone,
    shortRole,
    statusLabel,
  } from './format.js'

  let {
    player,
    selected = false,
    onfocus = undefined,
    onclick = undefined,
  } = $props()
</script>

<button
  class="bench-player-card"
  class:is-anchor={selected}
  class:is-unavailable={player.available === false}
  data-nav
  data-player={player.id}
  type="button"
  {onfocus}
  {onclick}
>
  <span class="bench-player-top">
    <span class="bench-position">
      <i class="position-dot {posTone(player.role)}"></i>
      {shortRole(player.role)}
    </span>
    <span class="bench-player-photo">
      <img src={player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
      {#if player.injury || player.suspension}
        <span
          class="player-status-flag"
          class:is-injury={Boolean(player.injury)}
          title={statusLabel(player)}
        >
          {player.injury ? '+' : '!'}
        </span>
      {/if}
    </span>
    <strong class="bench-rating">{Math.round(player.overall)}</strong>
  </span>
  <span
    class="fatigue-bar"
    class:is-low={player.fatigue < 50}
    title={`Кондиция ${player.fatigue}%`}
  >
    <i style={`width:${player.fatigue}%`}></i>
  </span>
  <span class="bench-player-name">{player.last_name || player.name}</span>
</button>
