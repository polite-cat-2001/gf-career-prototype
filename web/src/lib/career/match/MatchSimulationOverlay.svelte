<script>
  import AppShell from '../../ui/AppShell.svelte'
  import MatchScreen from '../../MatchScreen.svelte'

  let { setup, phase, minute, result, loading = false, error = '' } = $props()

  let hints = $derived(
    phase === 'live'
      ? [
          {
            gamepad: ['Y'],
            keyboard: ['R'],
            label: loading ? 'Симуляция…' : 'Пропустить',
          },
        ]
      : phase === 'done'
        ? [{ gamepad: ['A'], keyboard: ['Enter'], label: 'Далее' }]
        : [
            {
              gamepad: ['A'],
              keyboard: ['Enter'],
              label: loading ? 'Загрузка…' : 'Начать симуляцию',
            },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ],
  )

  let note = $derived(
    phase === 'live'
      ? 'Симуляция · 1 минута в секунду'
      : phase === 'done'
        ? 'Матч завершён'
        : 'Симуляция матча',
  )
</script>

{#if setup}
  <div class="match-overlay">
    <AppShell fill {hints} {note}>
      <MatchScreen {phase} {minute} {setup} simulation={result} {loading} {error} />
    </AppShell>
  </div>
{/if}
