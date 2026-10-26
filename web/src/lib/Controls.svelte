<script>
  import { inputDevice } from './input.js'

  let { hints = [], note = '', showDefaults = true } = $props()

  const defaults = [
    { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Навигация' },
    { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
    { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
  ]

  let shown = $derived(showDefaults ? [...defaults, ...hints] : hints)
  let device = $derived($inputDevice)
</script>

<footer class="control-bar">
  <div class="control-hints">
    {#each shown as hint}
      <span class="control-hint">
        {#each hint[device] || [] as key}
          <kbd>{key}</kbd>
        {/each}
        <span>{hint.label}</span>
      </span>
    {/each}
  </div>
  <div class="control-note">{note}</div>
</footer>
