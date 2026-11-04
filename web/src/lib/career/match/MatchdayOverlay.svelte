<script>
  import AppShell from '../../ui/AppShell.svelte'
  import MatchdayScreen from '../../MatchdayScreen.svelte'

  let { data, step, clubId } = $props()

  let hints = $derived(
    step === 'results'
      ? [
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Таблица' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'В хаб' },
        ]
      : [
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Продолжить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'К результатам' },
        ],
  )

  let note = $derived(step === 'results' ? 'Результаты дня' : 'Таблица после тура')
</script>

{#if data}
  <div class="matchday-overlay">
    <AppShell fill {hints} {note}>
      <MatchdayScreen {step} matchday={data} {clubId} />
    </AppShell>
  </div>
{/if}
