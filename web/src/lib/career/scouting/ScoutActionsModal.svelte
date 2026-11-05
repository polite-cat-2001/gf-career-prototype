<script>
  import { onMount } from 'svelte'
  import Legend from '../../ui/Legend.svelte'
  import { trapModalFocus } from '../../ui/modalFocus.js'
  import { portal } from '../../ui/portal.js'

  let {
    scout,
    hasReport = false,
    canRecall = false,
    hints = [],
    onViewReport,
    onMove,
    onRecall,
    onDismiss,
    onClose,
  } = $props()

  let layer = $state(null)

  onMount(() => trapModalFocus(layer))
</script>

<div class="sc-modal-layer" bind:this={layer} use:portal>
  <div class="sc-modal-shell">
    <div
      class="sc-modal sc-actions"
      role="dialog"
      aria-modal="true"
      aria-label={`${scout.name}: выберите действие`}
    >
      <header class="sc-modal-head">
        <strong>{scout.name}: выберите действие</strong>
      </header>
      <div class="sc-action-list">
        <button
          class="sc-confirm-row"
          data-nav
          data-autofocus={hasReport ? '' : undefined}
          disabled={!hasReport}
          onclick={onViewReport}
        >
          <span class="sc-action-label">Просмотр отчёта скаута</span>
          <span class="sc-key">A</span>
        </button>
        <button class="sc-confirm-row" data-nav onclick={onMove}>
          <span class="sc-action-label">Отправить в другой регион</span>
          <span class="sc-key">A</span>
        </button>
        <button
          class="sc-confirm-row"
          data-nav
          disabled={!canRecall}
          onclick={onRecall}
        >
          <span class="sc-action-label">Отозвать скаута</span>
          <span class="sc-key">A</span>
        </button>
        <button class="sc-confirm-row" data-nav onclick={onDismiss}>
          <span class="sc-action-label">Уволить скаута</span>
          <span class="sc-key">A</span>
        </button>
        <button class="sc-confirm-row" data-nav onclick={onClose}>
          <span class="sc-action-label">Отмена</span>
          <span class="sc-key">B</span>
        </button>
      </div>
    </div>
    <Legend {hints} />
  </div>
</div>
