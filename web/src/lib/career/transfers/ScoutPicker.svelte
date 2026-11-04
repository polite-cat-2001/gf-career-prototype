<script>
  import { onMount } from 'svelte'
  import { hideBrokenImage } from '../../format.js'
  import { trapModalFocus } from '../../ui/modalFocus.js'

  let { player, scouts, onAssign, onClose } = $props()

  let modalLayer = $state(null)

  onMount(() => trapModalFocus(modalLayer))
</script>

<div class="gf-modal-layer" bind:this={modalLayer}>
  <div
    class="gf-modal gf-picker"
    role="dialog"
    aria-modal="true"
    aria-label="Поручить скауту"
  >
    <header class="gf-picker__head">
      <span class="gf-modal__eyebrow">Поручить скауту</span>
      <strong class="gf-picker__title">Кому поручить</strong>
    </header>
    <p class="gf-picker__text">Кому поручить следить за {player.name}?</p>
    <div class="gf-picker__list">
      {#each scouts as scout, index (scout.id)}
        <button
          class="gf-action gf-picker__row"
          class:is-disabled={Boolean(scout.report)}
          data-nav
          data-autofocus={index === 0 && !scout.report ? '' : undefined}
          onclick={() => onAssign(scout)}
        >
          <span class="gf-picker__flag">
            {#if scout.flag}
              <img src={scout.flag} alt="" onerror={hideBrokenImage} />
            {/if}
          </span>
          <span class="gf-picker__main">
            <strong>{scout.name}</strong>
            <small>
              {scout.report
                ? `Занят: следит за ${scout.report.player_name}`
                : `Опыт ${scout.experience} · Решение ${scout.judgement}`}
            </small>
          </span>
          <span class="gf-picker__stars">
            {#each [0, 1, 2, 3, 4] as star (star)}
              <i class:on={star < scout.judgement}>★</i>
            {/each}
          </span>
        </button>
      {/each}
    </div>
    <button class="gf-action gf-picker__cancel" data-nav onclick={onClose}>
      <span class="gf-action__label">Отмена</span>
      <span class="gf-action__key">B</span>
    </button>
  </div>
</div>
