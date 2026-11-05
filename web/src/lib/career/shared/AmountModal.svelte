<script>
  import { onMount } from 'svelte'
  import { inputDevice } from '../../input.js'
  import { trapModalFocus } from '../../ui/modalFocus.js'
  import { portal } from '../../ui/portal.js'

  let {
    label,
    groups,
    index,
    places,
    hint = null,
    finish,
    confirmLabel = 'Готово',
  } = $props()

  let layer = $state(null)

  onMount(() => trapModalFocus(layer))

  function mountLayer(node) {
    return portal(node)
  }
</script>

<div class="gf-amount-layer" bind:this={layer} use:mountLayer>
  <div class="gf-amount-shell">
    <div class="gf-amount__card" role="dialog" aria-modal="true" aria-label={label}>
      <span class="gf-amount__label">{label}</span>
      <button
        class="gf-amount__value"
        data-nav
        data-amount
        data-cycle="amount"
        data-autofocus
        aria-label="Сумма"
        onclick={finish}
      >
        {#each groups as group, groupIndex (groupIndex)}
          <span class="gf-amount__group">
            {#each group.digits as digit, digitIndex (digitIndex)}
              <span
                class="gf-amount__digit"
                class:is-selected={group.start + digitIndex === index}
              >
                {digit}
              </span>
            {/each}
          </span>
        {/each}
      </button>
      <span class="gf-amount__place">Разряд: {places[index]}</span>
      {#if hint}
        <span class="gf-amount__hint">{hint}</span>
      {/if}
    </div>

    <footer class="gf-modal__foot">
      {#if $inputDevice === 'gamepad'}
        <span><kbd>←</kbd><kbd>→</kbd> Разряд</span>
        <span><kbd>↑</kbd><kbd>↓</kbd> Цифра</span>
        <span><kbd>A</kbd> {confirmLabel}</span>
        <span><kbd>B</kbd> Назад</span>
      {:else}
        <span><kbd>←</kbd><kbd>→</kbd> Разряд</span>
        <span><kbd>↑</kbd><kbd>↓</kbd> Цифра</span>
        <span><kbd>Enter</kbd> {confirmLabel}</span>
        <span><kbd>Esc</kbd> Назад</span>
      {/if}
    </footer>
  </div>
</div>
