<script>
  import CentreInfoRow from '../shared/CentreInfoRow.svelte'
  import CentreProfile from '../shared/CentreProfile.svelte'
  import MoraleFace from '../shared/MoraleFace.svelte'
  import { formatDate, formatValue, plural } from '../../format.js'

  let { player } = $props()
</script>

<aside class="centre-panel is-fit" aria-label="Карточка игрока">
  <CentreProfile {player} eyebrow={'Статус игрока'} />

  <div class="centre-morale-block">
    <div class="centre-morale-head">
      <span>Настрой</span>
      <span class="centre-morale-value">
        <span class="centre-morale-face">
          {#if player.expected_minutes > 0}
            <MoraleFace value={player.morale} size={22} />
          {:else}
            —
          {/if}
        </span>
        <strong
          class:is-none={player.expected_minutes <= 0}
          class:is-good={player.expected_minutes > 0 && player.morale >= 70}
          class:is-ok={player.expected_minutes > 0 &&
            player.morale >= 40 &&
            player.morale < 70}
          class:is-low={player.expected_minutes > 0 && player.morale < 40}
        >
          {player.expected_minutes > 0 ? `${player.morale}%` : ''}
        </strong>
      </span>
    </div>
    <div class="centre-morale-meta">
      {#if player.expected_minutes > 0}
        <span>Факт {player.actual_minutes} · План {player.expected_minutes} мин</span>
      {:else}
        <span>Ожидаемые минуты появятся после матчей</span>
      {/if}
      <span>Ожидается {Math.round((player.expected_share ?? 0) * 100)}% времени</span>
    </div>
  </div>

  <section class="centre-block">
    <div class="centre-block-head">Личные данные</div>
    <CentreInfoRow label={'Возраст'} value={player.age ?? '—'} />
    <CentreInfoRow label={'Гражданство'} value={player.citizenship.join(', ') || '—'} />
    <CentreInfoRow label={'Рост'} value={player.height ? `${player.height} см` : '—'} />
    <CentreInfoRow label={'Вес'} value={player.weight ? `${player.weight} кг` : '—'} />
    <CentreInfoRow label={'Рабочая нога'} value={player.foot || '—'} />
    <CentreInfoRow label={'Номер'} value={player.shirt_number ?? '—'} />
  </section>

  <section class="centre-block">
    <div class="centre-block-head">Контракт</div>
    <CentreInfoRow label={'Амплуа'} value={player.squad_role_label ?? '—'} />
    <CentreInfoRow label={'Срок'} value={`${player.contract?.years ?? 1} ${plural(
        player.contract?.years ?? 1,
        'год',
        'года',
        'лет',
      )}`} />
    <CentreInfoRow
      label={'Зарплата'}
      value={`${formatValue(player.contract?.weekly_wage ?? 0)} / нед.`}
    />
    <CentreInfoRow label={'Отступные'} value={formatValue(player.contract?.release_clause ?? 0)} />
  </section>

  <section class="centre-block">
    <div class="centre-block-head">Доступность</div>
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
      <CentreInfoRow label={'Состояние'} value={'Готов к игре'} />
    {/if}
    <CentreInfoRow label={'Кондиция'} value={`${player.fatigue}%`} />
  </section>
</aside>
