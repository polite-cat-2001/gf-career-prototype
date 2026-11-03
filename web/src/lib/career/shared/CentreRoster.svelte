<script>
  import {
    hideBrokenImage,
    moraleFace,
    ovrClass,
    playerInitialName,
    posTone,
    shortRole,
    statusLabel,
  } from '../../format.js'
  import SquadActions from './SquadActions.svelte'

  let {
    players,
    mode,
    centrePlayerId,
    openId,
    onFocus,
    onToggle,
    noticeFor,
    onTransferStatus,
    onManageTeam,
    onNumber,
    onNegotiation,
    onRelease,
  } = $props()
</script>

<section class="centre-list scroll-area" aria-label="Игроки состава">
  {#each players as player, index (player.id)}
    <div class="centre-row-wrap" data-row={player.id}>
      <button
        class="centre-player-row"
        class:is-stats={mode === 'stats'}
        class:is-attributes={mode === 'attributes'}
        class:is-open={openId === player.id}
        data-nav
        data-player={player.id}
        data-current={player.id === centrePlayerId ? '' : undefined}
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
            {#if noticeFor(player)}
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
              {player.expected_minutes > 0 ? moraleFace(player.morale) : '—'}
            </span>
          {/if}
        {/if}
      </button>

      {#if openId === player.id}
        <SquadActions
          {player}
          notice={noticeFor(player)}
          {onTransferStatus}
          {onManageTeam}
          {onNumber}
          {onNegotiation}
          {onRelease}
        />
      {/if}
    </div>
  {/each}
</section>
