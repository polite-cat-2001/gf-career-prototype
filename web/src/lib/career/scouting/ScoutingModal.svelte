<script>
  import { formatValue, hideBrokenImage } from '../../format.js'

  let {
    view,
    candidates,
    balance,
    hireCandidateId,
    onFocusHire,
    onHire,
    confirm,
    onConfirm,
    onCancelConfirm,
  } = $props()
</script>

{#if view === 'hire'}
  <div class="sc-modal-layer">
    <div class="sc-modal sc-hire" role="dialog" aria-modal="true" aria-label="Нанять скаута">
      <header class="sc-modal-head">
        <strong>Нанять скаута</strong>
      </header>
      <div class="sc-hire-top">
        <span>Нанять скаута</span>
        <span>Бюджет {formatValue(balance)}</span>
      </div>
      <div class="sc-hire-head">
        <span>Скаут</span>
        <span>Опыт</span>
        <span>Решение</span>
        <span>Цена</span>
      </div>
      <div class="sc-hire-list scroll-area">
        {#each candidates as candidate, index (candidate.id)}
          <button
            class="sc-hire-row"
            class:is-selected={hireCandidateId === candidate.id}
            class:is-disabled={!candidate.affordable}
            data-nav
            data-autofocus={index === 0 ? '' : undefined}
            onfocus={() => onFocusHire(candidate.id)}
            onclick={() => onHire(candidate.id)}
          >
            <span class="sc-hire-scout">
              <span class="sc-hire-flag">
                {#if candidate.flag}
                  <img src={candidate.flag} alt="" onerror={hideBrokenImage} />
                {/if}
              </span>
              <span class="sc-hire-name">
                <b>{candidate.name}</b>
                <small>{candidate.nationality}</small>
              </span>
            </span>
            <span class="sc-stars">
              {#each [0, 1, 2, 3, 4] as star (star)}
                <i class:on={star < candidate.experience}>★</i>
              {/each}
            </span>
            <span class="sc-stars">
              {#each [0, 1, 2, 3, 4] as star (star)}
                <i class:on={star < candidate.judgement}>★</i>
              {/each}
            </span>
            <span class="sc-hire-price">{formatValue(candidate.price)}</span>
          </button>
        {/each}
        {#if !candidates.length}
          <p class="sc-panel-muted">Свободных скаутов нет.</p>
        {/if}
      </div>
    </div>
  </div>
{/if}

{#if confirm}
  <div class="sc-modal-layer">
    <div class="sc-modal sc-confirm" role="dialog" aria-modal="true">
      <p class="sc-confirm-text">{confirm.title}</p>
      <button
        class="sc-confirm-row is-selected"
        data-nav
        data-autofocus
        onclick={onConfirm}
      >
        <span class="sc-key">A</span>
        <span>{confirm.yes}</span>
      </button>
      <button class="sc-confirm-row" data-nav onclick={onCancelConfirm}>
        <span>{confirm.no}</span>
      </button>
    </div>
  </div>
{/if}
