<script>
  import { onMount, tick } from 'svelte'
  import AppShell from './ui/AppShell.svelte'
  import Breadcrumb from './ui/Breadcrumb.svelte'
  import Row from './ui/Row.svelte'
  import { registerBack } from './actions.js'
  import { focusFirst } from './input.js'
  import { formatDate, formatTimestamp, hideBrokenImage, plural } from './format.js'

  let { saves = [], error = '', onload, onback } = $props()

  const hints = [
    { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Навигация' },
    { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
    { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
  ]

  let status = $derived(
    error ? 'ошибка API' : `${saves.length} ${plural(saves.length, 'сохранение', 'сохранения', 'сохранений')}`,
  )

  let firstLoadable = $derived(saves.findIndex((save) => save.compatible))

  onMount(() => {
    const stopBack = registerBack(onback)
    tick().then(focusFirst)
    return stopBack
  })

  function tagsFor(save) {
    return [save.league_name, save.country_name].filter(Boolean)
  }
</script>

<AppShell fill {status} statusError={Boolean(error)} {hints}>
  {#snippet header()}
    <Breadcrumb items={['Карьера', 'Загрузить']} />
  {/snippet}

  <div class="load-body">
    {#if error}
      <p class="gf-notice is-error">{error}</p>
    {/if}

    {#if saves.length === 0}
      <div class="load-empty" role="status">
        <span class="load-empty__title">Сохранений нет</span>
        <span class="load-empty__text">Создайте новую карьеру в главном меню.</span>
      </div>
    {:else}
      <div class="load-list">
        <div class="gf-rows">
          {#each saves as save, index (save.id)}
            <Row
              title={save.club_name}
              sub={save.manager_name}
              meta={save.compatible
                ? `Обновлено ${formatTimestamp(save.updated_at)}`
                : `Несовместим · версия ${save.version}`}
              tags={tagsFor(save)}
              autofocus={index === firstLoadable}
              onclick={() => onload(save.id)}
            >
              {#snippet lead()}
                {#if save.club_logo}
                  <img src={save.club_logo} alt="" onerror={hideBrokenImage} />
                {:else}
                  <span class="load-crest-fallback" aria-hidden="true">
                    {(save.club_name || '?').slice(0, 1)}
                  </span>
                {/if}
              {/snippet}

              {#if save.compatible}
                <span class="load-date">Дата карьеры · {formatDate(save.date)}</span>
              {:else}
                <span class="load-problem">{save.problem}</span>
              {/if}
            </Row>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</AppShell>
