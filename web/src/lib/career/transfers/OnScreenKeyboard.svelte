<script>
  import { OSK_ROWS } from '../constants/scouting.js'

  let { text, onPress, onBackspace, onClear, onApply, onClose } = $props()
</script>

<div class="gf-modal-layer gf-modal-layer--osk" onclick={onClose} role="presentation"></div>
<section class="gf-osk" data-osk aria-label="Поиск игрока">
  <header class="gf-osk__head">
    <span class="gf-osk__eyebrow">Поиск игрока</span>
    <div class="gf-osk__display">{text || '—'}</div>
  </header>
  <div class="gf-osk__body">
    <div class="gf-osk__keys">
      {#each OSK_ROWS as row, rowIndex (row)}
        <div class="gf-osk__row">
          {#each [...row] as key (key)}
            <button
              class="gf-osk__key osk-key"
              data-nav
              data-autofocus={rowIndex === 0 && key === 'Q' ? '' : undefined}
              onclick={() => onPress(key)}
            >
              {key}
            </button>
          {/each}
        </div>
      {/each}
    </div>
    <div class="gf-osk__actions">
      <button class="gf-action" data-nav onclick={() => onPress(' ')}>
        <span class="gf-action__label">Пробел</span>
      </button>
      <button class="gf-action" data-nav onclick={onBackspace}>
        <span class="gf-action__label">Удалить</span>
      </button>
      <button class="gf-action" data-nav onclick={onClear}>
        <span class="gf-action__label">Очистить</span>
      </button>
      <button class="gf-action gf-action--primary" data-nav onclick={onApply}>
        <span class="gf-action__label">Готово</span>
        <span class="gf-action__key">A</span>
      </button>
    </div>
  </div>
</section>
