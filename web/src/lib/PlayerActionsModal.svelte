<script>
  import Icon from './Icon.svelte'
  import { inputDevice } from './input.js'
  import {
    attributeGroups,
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
  } = $props()

  let photoFailed = $state(false)

  let knownStats = $derived(
    revealed && player?.stats
      ? attributeGroups(player.stats).flatMap((group) => group.rows).slice(0, 6)
      : [],
  )
  let expiring = $derived(
    contractMonths !== null && contractMonths > 0 && contractMonths <= 6,
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

<div class="sc-modal-layer">
  <div class="tf-actions sc-actions" role="dialog" aria-modal="true" aria-label="Действия игрока">
    <header class="tf-actions-head">
      <span class="tf-actions-photo" class:is-empty={!player.photo || photoFailed}>
        {#if !player.photo || photoFailed}
          <span class="sc-entry-photo-fallback">
            <Icon name="users" size={40} />
          </span>
        {:else}
          <img
            src={player.photo}
            alt=""
            onerror={() => (photoFailed = true)}
          />
        {/if}
      </span>
      <div class="tf-actions-title">
        <span class="eyebrow">Действия игрока</span>
        <strong class="tf-actions-name">{player.name}</strong>
        <div class="tf-actions-facts">
          <span>ЛЕТ <b>{player.age ?? '—'}</b></span>
          <span>АМПЛУА <b>{shortRole(player.role)}</b></span>
          <span>РОСТ <b>{player.height ? `${player.height} см` : '—'}</b></span>
          <span>НОГА <b>{revealed ? footLabel(player.foot) : '?'}</b></span>
        </div>
      </div>
      <span class="tf-actions-club">
        {#if player.club_logo}
          <img src={player.club_logo} alt="" />
        {/if}
        <span>{player.club_name ?? 'Свободный агент'}</span>
      </span>
    </header>

    <div class="tf-actions-grid">
      <div class="tf-action-metrics">
        <div class="tf-action-metric" class:is-visible={revealed}>
          <span>ОБЩ.</span>
          <b>{revealed ? Math.round(player.overall ?? 0) : '?'}</b>
        </div>
        <div class="tf-action-metric" class:is-visible={revealed}>
          <span>ЦЕНА</span>
          <b>{revealed ? formatValue(player.market_value ?? 0) : '?'}</b>
        </div>
        <div class="tf-action-metric" class:is-visible={revealed}>
          <span>ЗАРПЛАТА</span>
          <b>{revealed ? formatValue(player.weekly_wage ?? 0) : '?'}</b>
        </div>
        <div class="tf-action-metric is-visible">
          <span>ОТСТУПНЫЕ</span>
          <b>{formatValue(player.release_clause ?? 0)}</b>
        </div>
      </div>
      <div class="tf-action-report">
        <span class="tf-action-report-head">
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

    <div class="tf-action-status">
      <div class="tf-action-status-row">
        <i class="tf-status-dot"></i>
        <span>{statusLabel(player.status)}</span>
      </div>
      {#if note}
        <div class="tf-action-status-row"><span>{note}</span></div>
      {/if}
      {#if expiring}
        <div class="tf-action-status-row is-warn">
          <i class="tf-status-bang">!</i>
          <span>
            Контракт истекает через {contractMonths}
            {plural(contractMonths, 'месяц', 'месяца', 'месяцев')}
          </span>
        </div>
      {/if}
    </div>

    <div class="tf-action-list">
      {#if !revealed && !player.scouted}
        {#if activeReport}
          <div class="tf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
            <span>
              Отчёт уже готовится · осталось {activeReport.days_left}
              {plural(activeReport.days_left, 'день', 'дня', 'дней')}
            </span>
            <span class="tf-action-ticket">Скаут</span>
          </div>
        {:else if canAssign}
          <button
            class="tf-action"
            data-nav
            data-autofocus
            data-scout-action="assign"
            onclick={onassign}
          >
            <span>Поручить скауту</span>
            <span class="tf-action-key">A</span>
          </button>
        {:else}
          <div class="tf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
            <span>Сначала наймите скаута</span>
            <span class="tf-action-ticket">Сеть</span>
          </div>
        {/if}
      {/if}

      <button
        class="tf-action"
        class:is-disabled={!onshortlist}
        data-nav
        onclick={onshortlist}
        disabled={!onshortlist}
      >
        <span>{shortlisted ? 'Убрать из шортлиста' : 'Добавить в шортлист'}</span>
        <span class="tf-action-key">A</span>
      </button>
      {#if ontransfer}
        <button class="tf-action" data-nav onclick={ontransfer}>
          <span>Сделать предложение трансфера</span>
          <span class="tf-action-key">A</span>
        </button>
      {:else}
        <div class="tf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
          <span>Сделать предложение трансфера</span>
          <span class="tf-action-ticket">Недоступно</span>
        </div>
      {/if}
      {#if onloan}
        <button class="tf-action" data-nav onclick={onloan}>
          <span>Сделать предложение аренды</span>
          <span class="tf-action-key">A</span>
        </button>
      {:else}
        <div class="tf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
          <span>Сделать предложение аренды</span>
          <span class="tf-action-ticket">Недоступно</span>
        </div>
      {/if}
      <div class="tf-action is-disabled" data-nav role="button" tabindex="0" aria-disabled="true">
        <span>Обсудить переход</span>
        <span class="tf-action-ticket">#17</span>
      </div>

      {#if removeLabel}
        <div class="tf-actions-sep" aria-hidden="true"></div>
        <button class="tf-action is-danger" data-nav data-autofocus onclick={onremove}>
          <span>{removeLabel}</span>
          <span class="tf-action-key">X</span>
        </button>
      {/if}
    </div>

    <footer class="tf-actions-foot">
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
