<script>
  import Icon from '../../Icon.svelte'

  let {
    scout,
    task,
    report,
    title,
    subtitle,
    selected = false,
    autofocus = false,
    onFocus,
    onOpen,
  } = $props()
</script>

<button
  class="sc-tile sc-task-tile"
  class:is-selected={selected}
  data-nav
  data-scout={scout.id}
  data-autofocus={autofocus ? '' : undefined}
  onfocus={onFocus}
  onclick={onOpen}
>
  <span class="sc-task-owner">{scout.name}</span>
  <strong class="sc-task-title">{title}</strong>
  <span class="sc-task-sub">{subtitle}</span>
  {#if task}
    <span class="sc-task-found">
      <Icon name="users" size={18} />
      {task.found_count}
    </span>
  {/if}
  {#if report}
    <span class="sc-task-found">
      <Icon name="clock" size={18} />
      {report.days_left}
    </span>
  {/if}
</button>
