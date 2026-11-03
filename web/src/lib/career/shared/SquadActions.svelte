<script>
  import { slide } from 'svelte/transition'

  let {
    player,
    notice = false,
    onTransferStatus,
    onManageTeam,
    onNumber,
    onNegotiation,
    onRelease,
  } = $props()
</script>

<div
  class="squad-actions"
  data-actions={player.id}
  aria-label="Действия с игроком"
  transition:slide={{ duration: 180 }}
>
  <div class="squad-actions-col">
    <div class="squad-actions-head">
      <i class="squad-actions-dot is-transfer"></i>
      Трансфер
    </div>
    <button
      class="squad-action"
      data-nav
      data-action="transfer"
      onclick={() => onTransferStatus('transfer')}
    >
      {player.transfer_status === 'transfer' ? 'Снять с трансфера' : 'На трансфер'}
    </button>
    <button
      class="squad-action"
      data-nav
      data-action="loan"
      onclick={() => onTransferStatus('loan')}
    >
      {player.transfer_status === 'loan' ? 'Убрать из аренды' : 'Добавить в аренду'}
    </button>
    <button
      class="squad-action"
      data-nav
      data-action="blocked"
      onclick={() => onTransferStatus('blocked')}
    >
      {player.transfer_status === 'blocked' ? 'Разблокировать' : 'Блокировать'}
    </button>
  </div>
  <div class="squad-actions-col">
    <div class="squad-actions-head">
      <i class="squad-actions-dot is-squad"></i>
      Состав
    </div>
    <button class="squad-action" data-nav data-action="plan" onclick={onManageTeam}>
      Рук-во командой
    </button>
    <button class="squad-action" data-nav data-action="number" onclick={onNumber}>
      Смена номера
    </button>
  </div>
  <div class="squad-actions-col">
    <div class="squad-actions-head">
      <i class="squad-actions-dot is-contract"></i>
      Контракт
    </div>
    <button class="squad-action" data-nav data-action="renew" onclick={onNegotiation}>
      <span>Продление контракта</span>
      {#if notice}
        <span class="squad-action-notice" title="Готов ответ по контракту">!</span>
      {/if}
    </button>
    <button
      class="squad-action is-danger"
      data-nav
      data-action="release"
      onclick={onRelease}
    >
      Отпустить игрока
    </button>
  </div>
</div>
