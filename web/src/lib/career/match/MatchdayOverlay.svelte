<script>
  import MatchdayScreen from '../../MatchdayScreen.svelte'

  let { data, step, clubId } = $props()
</script>

{#if data}
  <MatchdayScreen {step} matchday={data} {clubId} />
{/if}
