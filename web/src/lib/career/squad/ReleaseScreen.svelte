<script>
  import { playerInitialName } from '../../format.js'

  let { player, onConfirm, onCancel } = $props()
</script>

<div class="release-screen">
  <div class="release-card">
    <span class="squad-kicker">Расторжение контракта</span>
    <strong class="release-title">Отпустить {playerInitialName(player)}?</strong>
    <p class="release-note">Игрок покинет клуб и исчезнет из состава. Действие нельзя отменить.</p>
    <div class="release-actions">
      <button class="shelf-action is-danger" data-nav onclick={onConfirm}>
        Отпустить игрока
      </button>
      <button class="shelf-action" data-nav data-autofocus onclick={onCancel}>
        Отмена
      </button>
    </div>
  </div>
</div>
