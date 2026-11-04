<script>
  import CentreInfoRow from '../shared/CentreInfoRow.svelte'
  import CentreProfile from '../shared/CentreProfile.svelte'
  import SquadActions from '../shared/SquadActions.svelte'
  import {
    formatDate,
    formatValue,
    hideBrokenImage,
    moraleFace,
    playerInitialName,
    plural,
    posTone,
    shortRole,
    statusLabel,
  } from '../../format.js'

  let {
    finance,
    players,
    player,
    centrePlayerId,
    openId,
    onFocus,
    onToggle,
    noticeFor,
    onTransferStatus,
    onManageTeam,
    onNumber,
    onNegotiation,
    onRelease,
  } = $props()
</script>

<div class="centre-finance">
  <div class="finance-summary">
    <div class="finance-stat">
      <span>Баланс клуба</span>
      <strong>{formatValue(finance.balance)}</strong>
    </div>
    <div class="finance-stat">
      <span>Стоимость состава</span>
      <strong>{formatValue(finance.total_market_value)}</strong>
    </div>
    <div class="finance-stat">
      <span>Зарплатная ведомость</span>
      <strong>{formatValue(finance.weekly_wage_bill)} <i>/ нед.</i></strong>
    </div>
  </div>

  <div class="finance-body">
    <section class="finance-table" aria-label="Финансы игроков">
      <div class="finance-head" aria-hidden="true">
        <span>Поз</span>
        <span>Игрок</span>
        <span>Возр.</span>
        <span>Стоимость</span>
        <span>Зарплата</span>
        <span>Контракт</span>
      </div>
      <div class="finance-list scroll-area">
        {#each players as row, index (row.id)}
          <div class="centre-row-wrap" data-row={row.id}>
            <button
              class="finance-row"
              class:is-open={openId === row.id}
              data-nav
              data-player={row.id}
              data-current={row.id === centrePlayerId ? '' : undefined}
              data-autofocus={index === 0 ? '' : undefined}
              onfocus={() => onFocus(row.id)}
              onclick={() => onToggle(row)}
            >
              <span class="pos-badge {posTone(row.role)}">{shortRole(row.role)}</span>
              <span class="finance-name-cell">
                <span class="finance-row-photo">
                  <img src={row.photo} alt="" onerror={hideBrokenImage} />
                  {#if row.injury}
                    <span
                      class="player-status-flag"
                      class:is-injury={Boolean(row.injury)}
                      title={statusLabel(row)}
                    >
                      +
                    </span>
                  {/if}
                </span>
                <span class="finance-name">{playerInitialName(row)}</span>
                {#if noticeFor(row)}
                  <span class="squad-notice" title="Готов ответ по контракту">!</span>
                {/if}
              </span>
              <span class="finance-cell">{row.age ?? '—'}</span>
              <span class="finance-cell is-value">{formatValue(row.market_value)}</span>
              <span class="finance-cell">{formatValue(row.contract?.weekly_wage ?? 0)}</span>
              <span class="finance-cell">
                {row.contract?.years ?? 1}
                {plural(row.contract?.years ?? 1, 'год', 'года', 'лет')}
              </span>
            </button>

            {#if openId === row.id}
              <SquadActions
                player={row}
                notice={noticeFor(row)}
                {onTransferStatus}
                {onManageTeam}
                {onNumber}
                {onNegotiation}
                {onRelease}
              />
            {/if}
          </div>
        {/each}
      </div>
    </section>

    {#if player}
      <aside class="centre-panel finance-panel is-fit" aria-label="Финансы игрока">
        <CentreProfile {player} eyebrow={'Финансы игрока'} />

        <div class="finance-player-meta">
          <span class="pos-badge {posTone(player.role)}">{shortRole(player.role)}</span>
          <span>Возраст {player.age ?? '—'}</span>
          <span>{player.squad_role_short}</span>
          <span>
            Настрой
            {player.expected_minutes > 0 ? `${moraleFace(player.morale)} ${player.morale}%` : '—'}
          </span>
        </div>

        <section class="centre-block">
          <div class="centre-block-head">Финансы</div>
          <CentreInfoRow label={'Стоимость'} value={formatValue(player.market_value)} />
          <CentreInfoRow
            label={'Зарплата'}
            value={`${formatValue(player.contract?.weekly_wage ?? 0)} / нед.`}
          />
          <CentreInfoRow
            label={'Отступные'}
            value={formatValue(player.contract?.release_clause ?? 0)}
          />
        </section>

        <section class="centre-block">
          <div class="centre-block-head">Контракт</div>
          <CentreInfoRow label={'Срок'} value={`${player.contract?.years ?? 1} ${plural(
              player.contract?.years ?? 1,
              'год',
              'года',
              'лет',
            )}`} />
          <CentreInfoRow label={'Амплуа'} value={player.squad_role_label ?? '—'} />
        </section>

        <section class="centre-block">
          <div class="centre-block-head">Статус</div>
          {#if player.injury}
            <CentreInfoRow label={'Травма'} value={player.injury.type} />
            <CentreInfoRow label={'Возвращение'} value={formatDate(player.injury.until)} />
          {:else if player.suspension}
            <CentreInfoRow label={'Дисквалификация'} value={`${player.suspension.matches} ${plural(
                player.suspension.matches,
                'матч',
                'матча',
                'матчей',
              )}`} />
          {:else}
            <CentreInfoRow label={'Доступность'} value={'Готов к игре'} />
          {/if}
          <CentreInfoRow label={'Кондиция'} value={`${player.fatigue}%`} />
        </section>
      </aside>
    {/if}
  </div>
</div>
