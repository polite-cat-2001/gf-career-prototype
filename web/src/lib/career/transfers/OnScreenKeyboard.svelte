<script>
  import { OSK_ROWS } from '../constants/scouting.js'

  let { text, onPress, onBackspace, onClear, onApply, onClose } = $props()
</script>

<div class="osk-scrim" onclick={onClose} role="presentation"></div>
<section class="osk" data-osk aria-label="Поиск игрока">
  <header class="osk-head">
    <span class="eyebrow">Поиск игрока</span>
    <div class="osk-display">{text || '—'}</div>
  </header>
  <div class="osk-keys">
    {#each OSK_ROWS as row, rowIndex (row)}
      <div class="osk-row">
        {#each [...row] as key (key)}
          <button
            class="osk-key"
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
  <div class="osk-actions">
    <button class="osk-action" data-nav onclick={() => onPress(' ')}>Пробел</button>
    <button class="osk-action" data-nav onclick={onBackspace}>Удалить</button>
    <button class="osk-action" data-nav onclick={onClear}>Очистить</button>
    <button class="osk-action is-primary" data-nav onclick={onApply}>Готово</button>
  </div>
</section>
