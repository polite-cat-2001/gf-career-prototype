<script>
  import { onMount, tick } from 'svelte'
  import AppShell from './ui/AppShell.svelte'
  import Breadcrumb from './ui/Breadcrumb.svelte'
  import Tile from './ui/Tile.svelte'
  import { focusFirst } from './input.js'
  import { formatTimestamp, hideBrokenImage } from './format.js'

  let {
    latest = null,
    savesCount = 0,
    loading = false,
    error = '',
    oncontinue,
    onnew,
    onload,
  } = $props()

  const hints = [
    { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Навигация' },
    { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
  ]

  let status = $derived(
    error ? 'ошибка API' : loading ? 'загрузка сохранений…' : 'canon.db · реальные данные',
  )

  onMount(() => {
    tick().then(focusFirst)
  })

  $effect(() => {
    if (!loading) tick().then(focusFirst)
  })

  function careerWord(count) {
    if (count % 10 === 1 && count % 100 !== 11) return 'карьера'
    if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'карьеры'
    return 'карьер'
  }
</script>

<AppShell {status} statusError={Boolean(error)} {hints}>
  {#snippet header()}
    <Breadcrumb items={['GameplayFootball', 'Карьера']} />
  {/snippet}

  {#if error}
    <p class="gf-notice is-error">{error}</p>
  {/if}

  <section class="gf-grid" aria-label="Карьера">
    <Tile
      hero
      autofocus
      disabled={!latest || loading}
      title="Продолжить"
      sub={latest
        ? `${latest.club_name} · ${latest.manager_name}`
        : 'Сначала создайте новую карьеру'}
      meta={latest ? `Последний сейв · ${formatTimestamp(latest.updated_at)}` : 'Нет сохранений'}
      glyph={latest ? '' : 'trophy'}
      glyphSize={152}
      style="--push-x: -6px; --push-y: -6px"
      onclick={oncontinue}
    >
      {#snippet art()}
        {#if latest}
          <img src={latest.club_logo} alt="" onerror={hideBrokenImage} />
        {/if}
      {/snippet}
    </Tile>

    <Tile
      wide
      title="Новая игра"
      sub="Страна, лига, клуб и менеджер"
      tags={['Случайный seed', 'Автосохранение']}
      glyph="shirt"
      glyphSize={120}
      style="--push-x: 6px; --push-y: -6px"
      onclick={onnew}
    />

    <Tile
      wide
      disabled={savesCount === 0}
      title="Загрузить"
      sub={savesCount === 0 ? 'Сохранений пока нет' : `${savesCount} ${careerWord(savesCount)}`}
      meta="Список карьер"
      glyph="layers"
      glyphSize={120}
      style="--push-x: 6px; --push-y: 6px"
      onclick={onload}
    />
  </section>
</AppShell>
