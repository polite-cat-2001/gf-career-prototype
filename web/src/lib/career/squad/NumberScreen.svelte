<script>
  import { playerInitialName } from '../../format.js'

  let { player, candidate, onConfirm } = $props()
</script>

<div class="number-screen">
  <div class="number-stage">
    <button
      class="number-shirt"
      data-nav
      data-cycle="number"
      data-autofocus
      aria-label={`Игровой номер ${candidate ?? '—'}`}
      onclick={onConfirm}
    >
      <svg viewBox="0 0 120 120" aria-hidden="true">
        <path
          class="number-shirt-shape"
          d="M36 8 44 4 48 12Q60 20 72 12L76 4 84 8 116 32 104 50 94 44 94 112 26 112 26 44 16 50 4 32Z"
        ></path>
        <text x="60" y="84" text-anchor="middle">{candidate ?? '—'}</text>
      </svg>
    </button>
    <div class="number-copy">
      <span class="squad-kicker">Смена игрового номера</span>
      <strong class="number-name">{playerInitialName(player)}</strong>
      <span class="number-note">Свободные номера 1–99 · занятые пропускаются</span>
      <span class="number-note">Текущий номер: {player.shirt_number ?? '—'}</span>
    </div>
  </div>
</div>
