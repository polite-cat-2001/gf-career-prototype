<script>
  let {
    taskDraft,
    taskField,
    taskScout,
    activeTask,
    onSelectField,
    roleLabel,
    rangeLabel,
    criteriaLine,
    pitchZone,
    onOpenReports,
  } = $props()
</script>

<div class="sc-body sc-task-edit">
  <section class="sc-task-grid">
    <button
      class="sc-task-cell"
      class:is-editing={taskField === 'role'}
      data-nav
      data-autofocus
      data-edit={taskField === 'role' ? 'true' : undefined}
      onclick={() => onSelectField('role')}
    >
      <span class="sc-task-cell-label">Позиция</span>
      <strong>{roleLabel(taskDraft?.role)}</strong>
      <span class="sc-task-cell-hint">A — выбор позиции</span>
    </button>
    <button class="sc-task-cell is-disabled" aria-disabled="true" disabled>
      <span class="sc-task-cell-label">Особенности</span>
      <strong>Любой</strong>
      <span class="sc-task-cell-hint">Пока не настраивается</span>
    </button>
    <button
      class="sc-task-cell"
      class:is-editing={taskField === 'contract'}
      data-nav
      data-edit={taskField === 'contract' ? 'true' : undefined}
      onclick={() => onSelectField('contract')}
    >
      <span class="sc-task-cell-label">Контракт</span>
      <strong>{rangeLabel(taskDraft?.contract_min ?? null, taskDraft?.contract_max ?? null)}</strong>
      <span class="sc-task-cell-hint">Срок, лет</span>
    </button>
    <button
      class="sc-task-cell"
      class:is-editing={taskField === 'age'}
      data-nav
      data-edit={taskField === 'age' ? 'true' : undefined}
      onclick={() => onSelectField('age')}
    >
      <span class="sc-task-cell-label">Лет</span>
      <strong>{rangeLabel(taskDraft?.age_min ?? null, taskDraft?.age_max ?? null)}</strong>
      <span class="sc-task-cell-hint">Возраст</span>
    </button>
  </section>

  <aside class="sc-panel scroll-area" aria-label="Подробности задачи">
    <div class="sc-panel-title">Подробности</div>
    <div class="sc-panel-stats">
      <span>Найдены игроки <b>{activeTask?.found_count ?? 0}</b></span>
      <span>Дней работы скаута <b>{activeTask?.days_worked ?? 0}</b></span>
    </div>
    <div class="sc-pitch">
      <span class="sc-pitch-zone {pitchZone(taskDraft?.role)}"></span>
      <span class="sc-pitch-line halfway"></span>
      <span class="sc-pitch-circle"></span>
      <span class="sc-pitch-box top"></span>
      <span class="sc-pitch-box bottom"></span>
    </div>
    <div class="sc-panel-section">
      <div class="sc-panel-row"><span>Скаут</span><b>{taskScout?.name}</b></div>
      <div class="sc-panel-row"><span>Регион</span><b>{activeTask?.region_name}</b></div>
      <div class="sc-panel-row"><span>Страна</span><b>{activeTask?.country_name}</b></div>
      <div class="sc-panel-muted">{criteriaLine(taskDraft)}</div>
    </div>
    <button class="sc-wide-action" data-nav onclick={onOpenReports}>
      <span>Список найденных игроков</span>
      <span class="sc-key">A</span>
    </button>
  </aside>
</div>
