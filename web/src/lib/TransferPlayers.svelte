<script>
  import { tick } from 'svelte'
  import Icon from './Icon.svelte'
  import PlayerActionsModal from './PlayerActionsModal.svelte'
  import { focusElement, focusFirst } from './input.js'
  import {
    attributeGroups,
    formatValue,
    hideBrokenImage,
    playerInitialName,
    plural,
    posTone,
    shortRole,
    statTone,
  } from './format.js'

  let {
    players = [],
    total = null,
    title = 'Результаты поиска',
    loading = false,
    error = '',
    emptyText = 'Никого не нашлось — ослабьте фильтры.',
    hasMore = false,
    view = $bindable('grid'),
    selectedId = $bindable(null),
    actionsOpen = $bindable(false),
    date = '',
    scouts = [],
    reportForPlayer = () => null,
    onloadmore = () => {},
    onaction = async () => null,
    onassign = null,
    onoffer = null,
    onnegotiate = null,
  } = $props()

  let shortlistOverrides = $state({})
  let wasOpen = false

  let selected = $derived(
    players.find((player) => player.id === selectedId) ?? players[0] ?? null,
  )
  let actionsPlayer = $derived(
    players.find((player) => player.id === selectedId) ??
      (actionsOpen ? selected : null),
  )
  let contractMonths = $derived(
    actionsPlayer ? monthsUntil(actionsPlayer.contract_expires) : null,
  )

  $effect(() => {
    if (!players.length) {
      if (!actionsOpen) selectedId = null
      return
    }
    if (!players.some((player) => player.id === selectedId)) {
      selectedId = players[0].id
    }
  })

  $effect(() => {
    if (actionsOpen && !actionsPlayer) actionsOpen = false
  })

  $effect(() => {
    if (actionsOpen) {
      wasOpen = true
      return
    }
    if (!wasOpen) return
    wasOpen = false
    const playerId = selectedId
    tick().then(() => {
      const card = playerId
        ? document.querySelector(`.tf-result[data-player-id="${playerId}"]`)
        : null
      if (card) focusElement(card)
      else focusFirst()
    })
  })

  function isShortlisted(player) {
    return shortlistOverrides[player.id] ?? Boolean(player.shortlisted)
  }

  function monthsUntil(value) {
    if (!value || !date) return null
    const target = new Date(`${value}T00:00:00`)
    const current = new Date(`${date}T00:00:00`)
    if (Number.isNaN(target.getTime()) || Number.isNaN(current.getTime())) return null
    const days = (target.getTime() - current.getTime()) / 86_400_000
    if (days <= 0) return 0
    return Math.ceil(days / 30.44)
  }

  function onResultFocus(player, index) {
    selectedId = player.id
    if (index > players.length - 5 && hasMore) onloadmore()
  }

  function onScroll(event) {
    const element = event.currentTarget
    if (element.scrollTop + element.clientHeight >= element.scrollHeight - 220) {
      if (hasMore) onloadmore()
    }
  }

  function openActions(playerId) {
    selectedId = playerId
    actionsOpen = true
    tick().then(focusFirst)
  }

  async function toggleShortlist() {
    const player = actionsPlayer
    if (!player) return
    const next = !isShortlisted(player)
    const updated = await onaction({
      type: 'shortlist_toggle',
      player_id: player.id,
    })
    if (!updated) return
    shortlistOverrides = { ...shortlistOverrides, [player.id]: next }
  }

  function scoutingStateLabel(player) {
    if (player.scouting_state === 'studying') {
      const left = player.scouting_days_left ?? 0
      return `Изучается · ${left} ${plural(left, 'день', 'дня', 'дней')}`
    }
    if (player.scouting_state === 'reported') return 'Отчёт готов'
    if (player.scouting_state === 'found') return 'Найден скаутом'
    if (player.scouting_state === 'none') return 'Не изучается'
    if (player.scouted) return 'Отчёт готов'
    return null
  }

  function negotiationStateLabel(status) {
    if (status === 'pending') return 'Ждёт ответа'
    if (status === 'counter') return 'Контрпредложение'
    if (status === 'accepted') return 'Согласовано'
    if (status === 'refused') return 'Отказ'
    return null
  }

  function stateLabels(player) {
    const labels = []
    const scouting = scoutingStateLabel(player)
    if (scouting) labels.push(scouting)
    const negotiation = negotiationStateLabel(
      player.transfer_contract?.status ?? player.negotiation_status,
    )
    if (negotiation) labels.push(negotiation)
    return labels
  }

  function statusLabel(value) {
    if (value === 'free') return 'Свободный агент'
    if (value === 'loan') return 'В аренде'
    if (value === 'transfer') return 'На трансфере'
    if (value === 'blocked') return 'Заблокирован'
    return 'В клубе'
  }

  function footLabel(value) {
    if (value === 'left') return 'Левая'
    if (value === 'right') return 'Правая'
    return value || '—'
  }
</script>

<div class="tf-results">
  <section class="tf-results-main" inert={actionsOpen ? true : undefined}>
    <div class="tf-results-title">
      <strong>{title}</strong>
      {#if total !== null}
        <span>{total.toLocaleString('ru-RU')}</span>
      {/if}
    </div>
    {#if error}<p class="transfer-error">{error}</p>{/if}
    <div
      class="tf-result-list scroll-area"
      class:is-list={view === 'list'}
      onscroll={onScroll}
    >
      {#each players as player, index (player.id)}
        <button
          class="tf-result"
          class:is-selected={selected?.id === player.id}
          data-nav
          data-player-id={player.id}
          data-autofocus={index === 0 ? '' : undefined}
          onfocus={() => onResultFocus(player, index)}
          onclick={() => openActions(player.id)}
        >
          <span class="tf-result-photo">
            <img src={player.photo} alt="" onerror={hideBrokenImage} />
          </span>
          <span class="tf-result-main">
            <span class="tf-result-name">{playerInitialName(player)}</span>
            <span class="tf-result-meta">
              {player.age ?? '—'} {plural(player.age ?? 0, 'год', 'года', 'лет')}
              <span class="pos-badge {posTone(player.role)}">{shortRole(player.role)}</span>
            </span>
            {#if stateLabels(player).length}
              <span class="tf-result-state">
                {#each stateLabels(player) as label (label)}
                  <span>{label}</span>
                {/each}
              </span>
            {/if}
          </span>
          {#if player.club_logo}
            <img class="tf-result-crest" src={player.club_logo} alt="" onerror={hideBrokenImage} />
          {/if}
        </button>
      {/each}
      {#if loading}
        <div class="transfer-loading">Загрузка…</div>
      {:else if !players.length && !error}
        <div class="transfer-loading">{emptyText}</div>
      {/if}
    </div>
  </section>

  <aside class="tf-detail" inert={actionsOpen ? true : undefined}>
    {#if selected}
      <div class="tf-detail-top">
        <span class="tf-detail-photo">
          <img src={selected.photo} alt="" onerror={hideBrokenImage} />
        </span>
        <div class="tf-detail-info">
          <strong class="tf-detail-name">{selected.name}</strong>
          <div class="tf-detail-facts">
            <span>ЛЕТ <b>{selected.age ?? '—'}</b></span>
            <span>РОСТ <b>{selected.height ?? '—'} см</b></span>
            <span>АМПЛУА <b>{shortRole(selected.role)}</b></span>
            <span>СТАТУС <b>{statusLabel(selected.status)}</b></span>
          </div>
        </div>
        <span class="tf-detail-club">
          {#if selected.club_logo}
            <img src={selected.club_logo} alt="" onerror={hideBrokenImage} />
          {/if}
          <span>{selected.club_name ?? 'Свободный агент'}</span>
        </span>
      </div>

      {#if scoutingStateLabel(selected) || negotiationStateLabel(selected.negotiation_status)}
        <div class="tf-detail-state">
          {#if scoutingStateLabel(selected)}
            <span><i>Скаутинг</i> {scoutingStateLabel(selected)}</span>
          {/if}
          {#if negotiationStateLabel(selected.transfer_contract?.status ?? selected.negotiation_status)}
            <span>
              <i>Переговоры</i>
              {negotiationStateLabel(
                selected.transfer_contract?.status ?? selected.negotiation_status,
              )}
            </span>
          {/if}
          {#if isShortlisted(selected)}
            <span class="is-lime"><i>Шортлист</i> В списке</span>
          {/if}
        </div>
      {/if}

      <div class="tf-detail-clause">
        <span>Сумма отступных</span>
        <strong>{formatValue(selected.release_clause)}</strong>
      </div>
      {#if selected.scouted}
        {@const known = attributeGroups(selected.stats)
          .flatMap((group) => group.rows)
          .slice(0, 6)}
        <div class="tf-detail-report">
          <div class="tf-report-col">
            <div class="tf-report-head">
              <Icon name="check" size={16} />
              Отчёт готов
            </div>
            <p>
              Скаут изучил игрока {selected.last_name || selected.name}.
              OVR, статы, зарплата и рабочая нога раскрыты.
            </p>
          </div>
          <div class="tf-report-col">
            <div class="tf-report-head">Сводка</div>
            <ul class="tf-scouted-stats">
              {#each known as row (row.key)}
                <li>
                  <span>{row.label}</span>
                  <b class={statTone(row.value)}>{row.value}</b>
                </li>
              {/each}
            </ul>
          </div>
        </div>
        <div class="transfer-fog-chips is-open">
          <span>ОБЩ. <b>{Math.round(selected.overall ?? 0)}</b></span>
          <span>ЗАРПЛАТА <b>{formatValue(selected.weekly_wage ?? 0)}</b></span>
          <span>НОГА <b>{footLabel(selected.foot)}</b></span>
          <span>ЦЕНА <b>{formatValue(selected.market_value ?? 0)}</b></span>
        </div>
      {:else if reportForPlayer(selected.id)}
        {@const activeReport = reportForPlayer(selected.id)}
        <div class="tf-detail-report">
          <div class="tf-report-col">
            <div class="tf-report-head">
              <Icon name="clock" size={16} />
              Изучается
            </div>
            <p>
              Скаут работает над отчётом. Осталось
              {activeReport.days_left}
              {plural(activeReport.days_left, 'день', 'дня', 'дней')}.
            </p>
            <div class="tf-report-progress">
              <i style={`width:${Math.round(activeReport.progress * 100)}%`}></i>
            </div>
          </div>
          <div class="tf-report-col">
            <div class="tf-report-head">Предварительный отчёт</div>
            <ul>
              {#each ['Разгон', 'Скорость рывков', 'Ловкость', 'Баланс', 'Дриблинг'] as stat (stat)}
                <li>??? {stat}</li>
              {/each}
            </ul>
          </div>
        </div>
        <div class="transfer-fog-chips">
          {#each ['OVR', 'Статы', 'Зарплата', 'Нога', 'Стоимость'] as hidden (hidden)}
            <span>??? {hidden}</span>
          {/each}
        </div>
      {:else}
        <div class="tf-detail-report">
          <div class="tf-report-col">
            <div class="tf-report-head">
              <Icon name="lock" size={16} />
              Не изучается
            </div>
            <p>
              На данный момент мы не изучаем игрока
              {selected.last_name || selected.name}.
            </p>
          </div>
          <div class="tf-report-col">
            <div class="tf-report-head">Предварительный отчёт</div>
            <ul>
              {#each ['Разгон', 'Скорость рывков', 'Ловкость', 'Баланс', 'Дриблинг'] as stat (stat)}
                <li>??? {stat}</li>
              {/each}
            </ul>
          </div>
        </div>
        <div class="transfer-fog-chips">
          {#each ['OVR', 'Статы', 'Зарплата', 'Нога', 'Стоимость'] as hidden (hidden)}
            <span>??? {hidden}</span>
          {/each}
        </div>
      {/if}
    {:else}
      <p class="transfer-detail-empty">Выберите игрока в списке.</p>
    {/if}
  </aside>

  {#if actionsOpen && actionsPlayer}
    <PlayerActionsModal
      player={actionsPlayer}
      revealed={Boolean(actionsPlayer.scouted)}
      scouts={scouts}
      activeReport={reportForPlayer(actionsPlayer.id)}
      contractMonths={contractMonths}
      shortlisted={isShortlisted(actionsPlayer)}
      onassign={onassign ? () => onassign(actionsPlayer) : null}
      onshortlist={toggleShortlist}
      ontransfer={onoffer ? () => onoffer(actionsPlayer, 'transfer') : null}
      onloan={onoffer ? () => onoffer(actionsPlayer, 'loan') : null}
      ondiscuss={onnegotiate ? () => onnegotiate(actionsPlayer) : null}
    />
  {/if}
</div>
