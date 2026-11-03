<script>
  import SquadActions from '../shared/SquadActions.svelte'
  import SquadRosterRow from './SquadRosterRow.svelte'

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
      <SquadRosterRow
        {player}
        {index}
        {mode}
        current={player.id === centrePlayerId}
        open={openId === player.id}
        notice={noticeFor(player)}
        {onFocus}
        {onToggle}
      />

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
