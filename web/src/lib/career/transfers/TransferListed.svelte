<script>
  import { tick } from 'svelte'
  import Accordion from '../../ui/Accordion.svelte'
  import { focusElement, focusFirst } from '../../input.js'
  import { hideBrokenImage, playerInitialName, shortRole } from '../../format.js'

  let {
    players = [],
    date = '',
    emptyText = 'Никого нет в списке на трансфер.',
    selectedId = $bindable(null),
    open = $bindable(false),
    onaction = async () => null,
  } = $props()

  let busy = $state(false)
  let wasOpen = $state(false)
  let expandedId = $derived(open ? selectedId : null)

  $effect(() => {
    if (open) {
      wasOpen = true
      return
    }
    if (!wasOpen) return
    wasOpen = false
    const playerId = selectedId
    if (!playerId) return
    tick().then(() => {
      const row = rowElement(playerId)
      if (row) focusElement(row)
      else focusFirst()
    })
  })

  function dayMonth(value) {
    if (!value) return '—'
    const parsed = new Date(`${value}T00:00:00`)
    if (Number.isNaN(parsed.getTime())) return value
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
    }).format(parsed)
  }

  function rowElement(playerId) {
    return document.querySelector(`[data-listed-player="${playerId}"]`)
  }

  function close() {
    open = false
  }

  function toggle(player) {
    if (open && selectedId === player.id) {
      close()
      return
    }
    selectedId = player.id
    open = true
    tick().then(() => {
      const row = rowElement(player.id)?.closest('.tf-listed-row')
      focusElement(row?.querySelector('[data-listed-action]'))
    })
  }

  async function remove(player) {
    if (busy) return
    busy = true
    const updated = await onaction({
      type: 'transfer_status',
      player_id: player.id,
      status: 'none',
    })
    busy = false
    if (!updated) return
    open = false
    selectedId = null
    tick().then(() => {
      const row = rowElement(player.id)
      if (row) focusElement(row)
      else focusFirst()
    })
  }
</script>

<div class="tf-listed">
  <div class="tf-listed-head">
    <span></span>
    <span>Тип</span>
    <span>Поз</span>
    <span>Имя</span>
    <span>Возр.</span>
    <span>Дата</span>
  </div>
  <div class="tf-listed-list scroll-area">
    {#each players as player (player.id)}
      <article class="tf-listed-row" class:is-open={expandedId === player.id}>
        <button
          class="tf-listed-row-main"
          data-nav
          data-listed-player={player.id}
          aria-expanded={expandedId === player.id}
          onclick={() => toggle(player)}
        >
          <span class="tf-listed-status">
            <i
              class="tf-listed-dot"
              class:is-loan={player.status === 'loan'}
              aria-hidden="true"
            ></i>
          </span>
          <span class="tf-listed-kind">
            {player.status === 'loan' ? 'Аренда' : 'Трансфер'}
          </span>
          <span class="tf-listed-pos">{shortRole(player.role)}</span>
          <span class="tf-listed-player">
            <span class="tf-listed-photo">
              <img src={player.photo} alt="" onerror={hideBrokenImage} />
            </span>
            <span class="tf-listed-name">{playerInitialName(player)}</span>
          </span>
          <span class="tf-listed-age">{player.age ?? '—'}</span>
          <span class="tf-listed-date">{dayMonth(date)}</span>
        </button>

        <Accordion open={expandedId === player.id} onclose={close}>
          <div class="tf-listed-accordion">
            <button
              class="tf-listed-action"
              data-nav
              data-listed-action
              disabled={busy}
              onclick={() => remove(player)}
            >
              Удалить из списка
            </button>
          </div>
        </Accordion>
      </article>
    {/each}
    {#if !players.length}
      <div class="transfer-loading">{emptyText}</div>
    {/if}
  </div>
</div>
