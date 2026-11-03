<script>
  import { formatValue, hideBrokenImage, plural } from '../../format.js'

  let { scout, status, criteriaLine } = $props()
</script>

<aside class="sc-panel scroll-area" aria-label="Сведения о скауте">
  {#if scout}
    <div class="sc-panel-head">
      <span class="sc-panel-flag">
        {#if scout.flag}
          <img src={scout.flag} alt="" onerror={hideBrokenImage} />
        {/if}
      </span>
      <div>
        <strong class="sc-panel-name">{scout.name}</strong>
        <span class="sc-panel-country">{scout.nationality}</span>
      </div>
      <div class="sc-stars" aria-label={`Решение ${scout.judgement} из 5`}>
        {#each [0, 1, 2, 3, 4] as star (star)}
          <i class:on={star < scout.judgement}>★</i>
        {/each}
      </div>
    </div>

    <div class="sc-panel-status" class:is-free={status.tone === 'free'}>
      <span>{status.title}</span>
      {#if status.detail}<small>{status.detail}</small>{/if}
    </div>

    {#if scout.task}
      <div class="sc-panel-section">
        <div class="sc-panel-label">Сеть поиска</div>
        <div class="sc-panel-big">{scout.task.country_name}</div>
        <div class="sc-panel-muted">{scout.task.region_name}</div>
        <div class="sc-panel-stats">
          <span>Дней работы <b>{scout.task.days_worked}</b></span>
          <span>Найдено <b>{scout.task.found_count}</b></span>
        </div>
        <div class="sc-panel-muted">{criteriaLine(scout.task.criteria)}</div>
      </div>
    {/if}

    {#if scout.report}
      <div class="sc-panel-section">
        <div class="sc-panel-label">Отчёт по запросу</div>
        <div class="sc-panel-big">{scout.report.player_name}</div>
        <div class="sc-progress">
          <span><i style={`width:${Math.round(scout.report.progress * 100)}%`}></i></span>
          <small>{scout.report.days_worked} / {scout.report.days_total}</small>
        </div>
        <div class="sc-panel-muted">
          Осталось {scout.report.days_left}
          {plural(scout.report.days_left, 'день', 'дня', 'дней')}
        </div>
      </div>
    {/if}

    <div class="sc-panel-section">
      <div class="sc-panel-label">Характеристики</div>
      <div class="sc-panel-row"><span>Опыт</span><b>{scout.experience} / 5</b></div>
      <div class="sc-panel-row"><span>Решение</span><b>{scout.judgement} / 5</b></div>
      <div class="sc-panel-row"><span>Стоимость</span><b>{formatValue(scout.price)}</b></div>
    </div>
  {:else}
    <p class="sc-panel-muted">Скаутов пока нет — наймите первого.</p>
  {/if}
</aside>
