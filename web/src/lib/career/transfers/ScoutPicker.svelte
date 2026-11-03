<script>
  import { hideBrokenImage } from '../../format.js'

  let { player, scouts, onAssign, onClose } = $props()
</script>

<div class="sc-modal-layer">
  <div class="sc-modal sc-confirm is-picker" role="dialog" aria-modal="true" aria-label="Поручить скауту">
    <p class="sc-confirm-text">Кому поручить следить за {player.name}?</p>
    {#each scouts as scout, index (scout.id)}
      <button
        class="sc-confirm-row sc-picker-row"
        class:is-disabled={Boolean(scout.report)}
        data-nav
        data-autofocus={index === 0 && !scout.report ? '' : undefined}
        onclick={() => onAssign(scout)}
      >
        <span class="sc-picker-flag">
          {#if scout.flag}
            <img src={scout.flag} alt="" onerror={hideBrokenImage} />
          {/if}
        </span>
        <span class="sc-picker-main">
          <strong>{scout.name}</strong>
          <small>
            {scout.report
              ? `Занят: следит за ${scout.report.player_name}`
              : `Опыт ${scout.experience} · Решение ${scout.judgement}`}
          </small>
        </span>
        <span class="sc-picker-stars">
          {#each [0, 1, 2, 3, 4] as star (star)}
            <i class:on={star < scout.judgement}>★</i>
          {/each}
        </span>
      </button>
    {/each}
    <button class="sc-confirm-row" data-nav onclick={onClose}>
      <span>Отмена</span>
    </button>
  </div>
</div>
