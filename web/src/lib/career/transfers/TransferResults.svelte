<script>
  import TransferPlayers from '../../TransferPlayers.svelte'
  import ScoutPicker from './ScoutPicker.svelte'

  let {
    players,
    total,
    loading = false,
    error = '',
    hasMore = false,
    date,
    view = $bindable(),
    selectedId = $bindable(),
    actionsOpen = $bindable(),
    scouts,
    reportForPlayer,
    onloadmore,
    onaction,
    onassign,
    onoffer,
    onnegotiate,
    scoutPickerOpen = false,
    scoutPickerPlayer = null,
    onCloseScoutPicker,
    onAssignScout,
  } = $props()
</script>

<TransferPlayers
  {players}
  {total}
  title="Результаты поиска"
  {loading}
  {error}
  {hasMore}
  {date}
  bind:view
  bind:selectedId
  bind:actionsOpen
  {scouts}
  {reportForPlayer}
  {onloadmore}
  {onaction}
  {onassign}
  {onoffer}
  {onnegotiate}
/>

{#if scoutPickerOpen && scoutPickerPlayer}
  <ScoutPicker
    player={scoutPickerPlayer}
    {scouts}
    onAssign={onAssignScout}
    onClose={onCloseScoutPicker}
  />
{/if}
