<script>
  import { plural } from '../../format.js'

  let { scout, task, report, criteriaLine, pitchZone, onOpenReports } = $props()
</script>

<aside class="sc-panel scroll-area" aria-label="Подробности задачи">
  {#if scout}
    <div class="sc-panel-title">Подробности</div>
    <div class="sc-panel-stats">
      <span>Найдены игроки <b>{task ? task.found_count : 0}</b></span>
      <span>
        Дней работы скаута
        <b>{task ? task.days_worked : report ? report.days_worked : 0}</b>
      </span>
    </div>
    <div class="sc-pitch" class:is-task={Boolean(task)}>
      <span class="sc-pitch-zone {task ? pitchZone(task.criteria.role) : 'all'}"></span>
      <span class="sc-pitch-line halfway"></span>
      <span class="sc-pitch-circle"></span>
      <span class="sc-pitch-box top"></span>
      <span class="sc-pitch-box bottom"></span>
    </div>
    <div class="sc-panel-section">
      <div class="sc-panel-row"><span>Скаут</span><b>{scout.name}</b></div>
      {#if task}
        <div class="sc-panel-row"><span>Регион</span><b>{task.region_name}</b></div>
        <div class="sc-panel-row"><span>Страна</span><b>{task.country_name}</b></div>
        <div class="sc-panel-muted">{criteriaLine(task.criteria)}</div>
      {:else if report}
        <div class="sc-panel-row"><span>Игрок</span><b>{report.player_name}</b></div>
        <div class="sc-panel-muted">
          Осталось {report.days_left}
          {plural(report.days_left, 'день', 'дня', 'дней')}
        </div>
      {:else}
        <div class="sc-panel-muted">Задача не назначена. Выберите регион и страну поиска.</div>
      {/if}
    </div>
    {#if task}
      <button class="sc-wide-action" data-nav onclick={onOpenReports}>
        <span>Список найденных игроков</span>
        <span class="sc-key">A</span>
      </button>
    {/if}
  {/if}
</aside>
