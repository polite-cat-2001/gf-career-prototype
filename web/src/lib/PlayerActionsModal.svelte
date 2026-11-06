<script>
  import { onMount } from 'svelte'
  import { inputDevice } from './input.js'
  import PlayerPhoto from './ui/PlayerPhoto.svelte'
  import { trapModalFocus } from './ui/modalFocus.js'
  import { portal } from './ui/portal.js'
  import {
    attributeGroups,
    formatDate,
    formatValue,
    plural,
    shortRole,
    statTone,
  } from './format.js'

  let {
    player,
    revealed = false,
    scouts = [],
    activeReport = null,
    contractMonths = null,
    shortlisted = false,
    note = '',
    removeLabel = null,
    onassign = null,
    onshortlist = null,
    onremove = null,
    ontransfer = null,
    onloan = null,
    ondiscuss = null,
  } = $props()

  let modalLayer = $state(null)

  onMount(() => trapModalFocus(modalLayer))

  let knownStats = $derived(
    revealed && player?.stats
      ? attributeGroups(player.stats).flatMap((group) => group.rows).slice(0, 6)
      : [],
  )
  let expiring = $derived(
    contractMonths !== null && contractMonths > 0 && contractMonths <= 6,
  )
  let offerState = $derived(player?.latest_offer ?? null)
  let canNegotiate = $derived(Boolean(offerState?.can_negotiate))
  let transferSigned = $derived(Boolean(offerState?.signed))
  let transferJoinOn = $derived(offerState?.execute_on ?? null)
  let canDiscuss = $derived(
    Boolean(
      player?.can_discuss ??
        (player?.status === 'free' ||
          (contractMonths !== null && contractMonths <= 6)),
    ),
  )
  let canAssign = $derived(
    !revealed &&
      !player?.scouted &&
      !activeReport &&
      Array.isArray(scouts) &&
      scouts.length > 0,
  )

  function footLabel(value) {
    if (value === 'left') return 'Левая'
    if (value === 'right') return 'Правая'
    return value || '—'
  }

  function statusLabel(value) {
    if (value === 'free') return 'Свободный агент'
    if (value === 'loan') return 'В аренде'
    if (value === 'transfer') return 'На трансфере'
    if (value === 'blocked') return 'Заблокирован'
    return 'В клубе'
  }
</script>

<div class="gf-modal-layer gf-modal-layer--player" bind:this={modalLayer} use:portal>
  <div class="gf-modal-shell">
    <div class="gf-modal gf-modal--player" role="dialog" aria-modal="true" aria-label="Действия игрока">
    <header class="gf-modal__head">
      <span class="gf-modal__photo">
        <PlayerPhoto src={player.photo} />
      </span>
      <div class="gf-modal__title">
        <span class="gf-modal__eyebrow">Действия игрока</span>
        <strong class="gf-modal__name">{player.name}</strong>
        <div class="gf-modal__facts">
          <span>ЛЕТ <b>{player.age ?? '—'}</b></span>
          <span>АМПЛУА <b>{shortRole(player.role)}</b></span>
          <span>РОСТ <b>{player.height ? `${player.height} см` : '—'}</b></span>
          <span>НОГА <b>{revealed ? footLabel(player.foot) : '?'}</b></span>
        </div>
      </div>
      <span class="gf-modal__club">
        {#if player.club_logo}
          <img src={player.club_logo} alt="" />
        {/if}
        <span>{player.club_name ?? 'Свободный агент'}</span>
      </span>
    </header>

    <div class="gf-modal__body">
      <div class="gf-modal__split">
        <div class="gf-metrics">
          <div class="gf-metric" class:is-visible={revealed}>
            <span>ОБЩ.</span>
            <b>{revealed ? Math.round(player.overall ?? 0) : '?'}</b>
          </div>
          <div class="gf-metric" class:is-visible={revealed}>
            <span>ЦЕНА</span>
            <b>{revealed ? formatValue(player.market_value ?? 0) : '?'}</b>
          </div>
          <div class="gf-metric" class:is-visible={revealed}>
            <span>ЗАРПЛАТА</span>
            <b>{revealed ? formatValue(player.weekly_wage ?? 0) : '?'}</b>
          </div>
          <div class="gf-metric is-visible">
            <span>ОТСТУПНЫЕ</span>
            <b>{formatValue(player.release_clause ?? 0)}</b>
          </div>
        </div>
        <div class="gf-report">
          <span class="gf-report__head">
            {revealed ? 'Сводка' : 'Предварительный отчёт'}
          </span>
          <ul>
            {#if revealed}
              {#each knownStats as row (row.key)}
                <li>
                  <span>{row.label}</span>
                  <b class={statTone(row.value)}>{row.value}</b>
                </li>
              {/each}
            {:else}
              {#each ['Разгон', 'Скорость рывков', 'Ловкость', 'Баланс', 'Дриблинг', 'Владение'] as stat (stat)}
                <li><span>{stat}</span><b>???</b></li>
              {/each}
            {/if}
          </ul>
        </div>
      </div>

      <div class="gf-status-lines">
        <div class="gf-status-line">
          <i class="gf-status-dot"></i>
          <span>{statusLabel(player.status)}</span>
        </div>
        {#if note}
          <div class="gf-status-line"><span>{note}</span></div>
        {/if}
        {#if expiring}
          <div class="gf-status-line is-warn">
            <i class="gf-status-bang">!</i>
            <span>
              Контракт истекает через {contractMonths}
              {plural(contractMonths, 'месяц', 'месяца', 'месяцев')}
            </span>
          </div>
        {/if}
      </div>

      <div class="gf-modal__actions">
        {#if !revealed && !player.scouted}
          {#if activeReport}
            <div class="gf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
              <span class="gf-action__label">
                Отчёт уже готовится · осталось {activeReport.days_left}
                {plural(activeReport.days_left, 'день', 'дня', 'дней')}
              </span>
              <span class="gf-action__ticket">Скаут</span>
            </div>
          {:else if canAssign}
            <button
              class="gf-action tf-action"
              data-nav
              data-autofocus
              data-scout-action="assign"
              onclick={onassign}
            >
              <span class="gf-action__label">Поручить скауту</span>
              <span class="gf-action__key">A</span>
            </button>
          {:else}
            <div class="gf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
              <span class="gf-action__label">Сначала наймите скаута</span>
              <span class="gf-action__ticket">Сеть</span>
            </div>
          {/if}
        {/if}

        <button
          class="gf-action"
          class:is-disabled={!onshortlist}
          data-nav
          onclick={onshortlist}
          disabled={!onshortlist}
        >
          <span class="gf-action__label">
            {shortlisted ? 'Убрать из шортлиста' : 'Добавить в шортлист'}
          </span>
          <span class="gf-action__key">A</span>
        </button>
        {#if canNegotiate && ondiscuss}
          <button class="gf-action" data-nav onclick={ondiscuss}>
            <span class="gf-action__label">Переговоры по контракту</span>
            <span class="gf-action__key">A</span>
          </button>
        {:else if transferSigned}
          <p class="gf-action-note">
            Переход завершён{#if transferJoinOn} · присоединится {formatDate(transferJoinOn)}{/if}
          </p>
        {:else}
          {#if ontransfer}
            <button class="gf-action" data-nav onclick={ontransfer}>
              <span class="gf-action__label">Сделать предложение трансфера</span>
              <span class="gf-action__key">A</span>
            </button>
          {:else}
            <div class="gf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
              <span class="gf-action__label">Сделать предложение трансфера</span>
              <span class="gf-action__ticket">Недоступно</span>
            </div>
          {/if}
          {#if onloan}
            <button class="gf-action" data-nav onclick={onloan}>
              <span class="gf-action__label">Сделать предложение аренды</span>
              <span class="gf-action__key">A</span>
            </button>
          {:else}
            <div class="gf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
              <span class="gf-action__label">Сделать предложение аренды</span>
              <span class="gf-action__ticket">Недоступно</span>
            </div>
          {/if}
          {#if canDiscuss && ondiscuss}
            <button class="gf-action" data-nav onclick={ondiscuss}>
              <span class="gf-action__label">Обсудить переход</span>
              <span class="gf-action__key">A</span>
            </button>
          {:else}
            <div class="gf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
              <span class="gf-action__label">Обсудить переход</span>
              <span class="gf-action__ticket">#17</span>
            </div>
          {/if}
        {/if}

        {#if removeLabel}
          <button class="gf-action is-danger" data-nav data-autofocus onclick={onremove}>
            <span class="gf-action__label">{removeLabel}</span>
            <span class="gf-action__key">X</span>
          </button>
        {/if}
      </div>
    </div>
    </div>

    <footer class="gf-modal__foot">
      {#if $inputDevice === 'gamepad'}
        <span><kbd>A</kbd> Выбор</span>
        <span><kbd>B</kbd> Назад</span>
      {:else}
        <span><kbd>Enter</kbd> Выбор</span>
        <span><kbd>Esc</kbd> Назад</span>
      {/if}
    </footer>
  </div>
</div>
