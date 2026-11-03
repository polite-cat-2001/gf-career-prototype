<script>
  import PlayerAttributesPane from './PlayerAttributesPane.svelte'
  import PlayerFinancePane from './PlayerFinancePane.svelte'
  import PlayerStatsPane from './PlayerStatsPane.svelte'
  import PlayerStatusPane from './PlayerStatusPane.svelte'
  import SquadCentreTabs from './SquadCentreTabs.svelte'
  import SquadRoster from './SquadRoster.svelte'

  let {
    tabs,
    activeTab,
    onSelectTab,
    players,
    player,
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
    totals,
    competitions,
    radar,
    attributePages,
    attributePage,
    attributeGroup,
    onShiftAttributePage,
    finance,
  } = $props()
</script>

<div class="centre">
  <SquadCentreTabs {tabs} active={activeTab} onSelect={onSelectTab} />

  {#if activeTab === 'status'}
    <div class="centre-body">
      <SquadRoster
        mode="status"
        {players}
        {centrePlayerId}
        {openId}
        {onFocus}
        {onToggle}
        {noticeFor}
        {onTransferStatus}
        {onManageTeam}
        {onNumber}
        {onNegotiation}
        {onRelease}
      />
      {#if player}
        <PlayerStatusPane {player} />
      {/if}
    </div>
  {:else if activeTab === 'stats'}
    <div class="centre-body">
      <SquadRoster
        mode="stats"
        {players}
        {centrePlayerId}
        {openId}
        {onFocus}
        {onToggle}
        {noticeFor}
        {onTransferStatus}
        {onManageTeam}
        {onNumber}
        {onNegotiation}
        {onRelease}
      />
      {#if player}
        <PlayerStatsPane {player} {totals} {competitions} />
      {/if}
    </div>
  {:else if activeTab === 'attributes'}
    <div class="centre-body">
      <SquadRoster
        mode="attributes"
        {players}
        {centrePlayerId}
        {openId}
        {onFocus}
        {onToggle}
        {noticeFor}
        {onTransferStatus}
        {onManageTeam}
        {onNumber}
        {onNegotiation}
        {onRelease}
      />
      {#if player}
        <PlayerAttributesPane
          {player}
          {radar}
          pages={attributePages}
          page={attributePage}
          group={attributeGroup}
          onShift={onShiftAttributePage}
        />
      {/if}
    </div>
  {:else}
    <PlayerFinancePane
      {finance}
      {players}
      {player}
      {centrePlayerId}
      {openId}
      {onFocus}
      {onToggle}
      {noticeFor}
      {onTransferStatus}
      {onManageTeam}
      {onNumber}
      {onNegotiation}
      {onRelease}
    />
  {/if}
</div>
