<script>
  import {
    hideBrokenImage,
    playerInitialName,
    posTone,
    shortRole,
    statusLabel,
  } from './format.js'

  let {
    player,
    role,
    interactive = false,
    preview = false,
    selected = false,
    positionStyle = '',
    onfocus = undefined,
    onmouseenter = undefined,
    onclick = undefined,
  } = $props()
</script>

<svelte:element
  this={interactive ? 'button' : 'span'}
  class="pitch-player"
  class:is-preview={preview}
  class:is-anchor={selected}
  class:is-unavailable={player.available === false}
  data-nav={interactive ? '' : undefined}
  data-player={interactive ? player.id : undefined}
  data-role={interactive ? role : undefined}
  role={interactive ? undefined : 'presentation'}
  type={interactive ? 'button' : undefined}
  style={positionStyle}
  {onfocus}
  {onmouseenter}
  {onclick}
>
  <span class="player-photo">
    <img src={player.photo} alt="" loading="lazy" onerror={hideBrokenImage} />
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
  <span class="player-plate">
    <span class="player-pos {posTone(role)}">{shortRole(role)}</span>
    <span class="player-ovr">{Math.round(player.overall)}</span>
  </span>
  <span class="player-name-wrap">
    <span class="player-name">{playerInitialName(player)}</span>
  </span>
  <span
    class="fatigue-bar"
    class:is-low={player.fatigue < 50}
    title={`Кондиция ${player.fatigue}%`}
  >
    <i style={`width:${player.fatigue}%`}></i>
  </span>
</svelte:element>
