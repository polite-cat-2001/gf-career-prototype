<script>
  import MatchScreen from '../../MatchScreen.svelte'

  let { setup, phase, minute, result, loading = false, error = '' } = $props()
</script>

{#if setup}
  <MatchScreen {phase} {minute} {setup} simulation={result} {loading} {error} />
{/if}
