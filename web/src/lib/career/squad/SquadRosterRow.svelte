<script>
  import MoraleFace from '../shared/MoraleFace.svelte'
  import {
    hideBrokenImage,
    ovrClass,
    playerInitialName,
    posTone,
    shortRole,
    statusLabel,
  } from '../../format.js'

  let { player, index, mode, current = false, open = false, notice = false, onFocus, onToggle } =
    $props()
</script>

<button
  class="centre-player-row"
  class:is-stats={mode === 'stats'}
  class:is-attributes={mode === 'attributes'}
  class:is-open={open}
  data-nav
  data-player={player.id}
  data-current={current ? '' : undefined}
  data-autofocus={index === 0 ? '' : undefined}
  onfocus={() => onFocus(player.id)}
  onclick={() => onToggle(player)}
>
  <span class="centre-row-photo">
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
  <span class="centre-row-main">
    <span class="centre-row-name-row">
      <span class="centre-row-name">{playerInitialName(player)}</span>
      {#if notice}
        <span class="squad-notice" title="Готов ответ по контракту">!</span>
      {/if}
    </span>
    <span class="centre-row-meta">
      <span class="pos-badge {posTone(player.role)}">{shortRole(player.role)}</span>
      <span>{player.squad_role_short}</span>
    </span>
  </span>
  {#if mode === 'stats'}
    <span class="centre-row-totals">
      {player.season_stats?.apps ?? 0} И · {player.season_stats?.goals ?? 0} Г ·
      {player.season_stats?.assists ?? 0} А · {player.season_stats?.minutes ?? 0} мин
    </span>
  {:else}
    <strong class="centre-row-ovr {ovrClass(player.overall)}">
      {Math.round(player.overall)}
    </strong>
    {#if mode === 'status'}
      <span
        class="centre-row-face"
        title={player.expected_minutes > 0
          ? `Настрой ${player.morale}%`
          : 'Нет данных о настрое'}
      >
        {#if player.expected_minutes > 0}
          <MoraleFace value={player.morale} size={20} />
        {:else}
          —
        {/if}
      </span>
    {/if}
  {/if}
</button>
