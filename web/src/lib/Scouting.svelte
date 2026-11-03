<script>
  import ScoutingHub from './career/scouting/ScoutingHub.svelte'

  let {
    career,
    mode = 'scouts',
    initialEntryId = null,
    backToHub = false,
    onclose = () => {},
    onaction = async () => null,
    onoffer = null,
    onnegotiate = null,
    hints = $bindable([]),
  } = $props()
</script>

<ScoutingHub
  {career}
  {mode}
  {initialEntryId}
  {backToHub}
  {onclose}
  {onaction}
  {onoffer}
  {onnegotiate}
  bind:hints
/>
