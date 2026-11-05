<script>
  import CentreProfile from '../shared/CentreProfile.svelte'
  import MoraleFace from '../shared/MoraleFace.svelte'
  import RadarChart from '../shared/RadarChart.svelte'
  import {
    formatValue,
    plural,
    posTone,
    positionLabel,
    shortRole,
    statTone,
  } from '../../format.js'
  import { starCount } from '../utils/squad.js'

  let { player, radar, pages, page, group, onShift } = $props()
</script>

<aside class="centre-panel scroll-area" aria-label="Характеристики игрока">
  <CentreProfile {player} eyebrow={'Характеристики игрока'} />

  <div class="attribute-layout">
    <div class="attribute-radar">
      <RadarChart values={radar} />
    </div>
    <div class="attribute-detail">
      <div class="centre-pager" role="group" aria-label="Группы характеристик">
        <button
          class="pager-arrow"
          type="button"
          tabindex="-1"
          aria-label="Предыдущая страница"
          onmousedown={(event) => event.preventDefault()}
          onclick={() => onShift(-1)}
        >
          ‹
        </button>
        <span class="pager-stick">R</span>
        <button
          class="pager-arrow"
          type="button"
          tabindex="-1"
          aria-label="Следующая страница"
          onmousedown={(event) => event.preventDefault()}
          onclick={() => onShift(1)}
        >
          ›
        </button>
        <span class="pager-dots" aria-hidden="true">
          {#each pages as item (item.id)}
            <i class:active={page === item.id}></i>
          {/each}
        </span>
      </div>
      {#if page === 'overview'}
        <div class="attribute-group-title">Общая информация</div>
        <div class="attribute-facts">
          <span class="pos-badge {posTone(player.role)}">{shortRole(player.role)}</span>
          <span>{positionLabel(player.position)}</span>
          <span>Возраст {player.age ?? '—'}</span>
          <span>{player.squad_role_short}</span>
        </div>
        <div class="attribute-trait-grid">
          <div class="attribute-trait">
            <span>Настрой</span>
            <strong>
              {#if player.expected_minutes > 0}
                <MoraleFace value={player.morale} size={16} /> {player.morale}%
              {:else}
                —
              {/if}
            </strong>
          </div>
          <div class="attribute-trait">
            <span>Финты</span>
            <span class="trait-stars">
              {#each Array.from({ length: 5 }) as _, index (index)}
                <i class:filled={index < starCount(player.skill_moves)}>★</i>
              {/each}
            </span>
          </div>
          <div class="attribute-trait">
            <span>Слабая нога</span>
            <span class="trait-stars">
              {#each Array.from({ length: 5 }) as _, index (index)}
                <i class:filled={index < starCount(player.weak_foot)}>★</i>
              {/each}
            </span>
          </div>
          <div class="attribute-trait">
            <span>Потенциал</span>
            <strong>{player.pot ?? '—'}</strong>
          </div>
          <div class="attribute-trait">
            <span>Стоимость</span>
            <strong>{formatValue(player.market_value)}</strong>
          </div>
          <div class="attribute-trait">
            <span>Контракт</span>
            <strong>
              {player.contract?.years ?? 1}
              {plural(player.contract?.years ?? 1, 'год', 'года', 'лет')}
            </strong>
          </div>
        </div>
        <div class="attribute-group-title">Радар</div>
        <div class="attribute-axis-grid">
          {#each radar as axis (axis.label)}
            <div class="attribute-axis">
              <span>{axis.label}</span>
              <strong>{axis.value}</strong>
            </div>
          {/each}
        </div>
      {:else if group}
        <div class="attribute-group-title">{group.label}</div>
        <div class="attribute-rows">
          {#each group.rows as row (row.key)}
            <div class="attribute-row">
              <span>{row.label}</span>
              <strong class="attribute-value {statTone(row.value)}">{row.value}</strong>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</aside>
