<script>
  import { inputDevice } from '../input.js'

  let { hints = [], note = '' } = $props()

  const defaults = [
    { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Навигация' },
    { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
    { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
  ]

  let shown = $derived(hints.length ? hints : defaults)
  let device = $derived($inputDevice)
</script>

<div class="gf-legend">
  <div class="gf-control-hints">
    {#each shown as hint}
      {@const keys = hint[device] || []}
      {#if keys.length}
        <span class="gf-control-hint">
          {#each keys as key}
            <kbd>{key}</kbd>
          {/each}
          <span>{hint.label}</span>
        </span>
      {/if}
    {/each}
  </div>
  {#if note}
    <span class="gf-legend__note">{note}</span>
  {/if}
</div>
