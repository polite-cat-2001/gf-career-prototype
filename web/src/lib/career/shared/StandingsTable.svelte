<script>
  import { tick } from 'svelte'

  import { hideBrokenImage } from '../../format.js'

  let { standings = [], clubId, showDelta = false } = $props()

  let wrap = $state(null)

  $effect(() => {
    const rows = standings
    const node = wrap
    if (!node || !rows.length) return
    tick().then(() => {
      if (!node.isConnected) return
      const own = node.querySelector('tr.is-own')
      if (!own) return
      const wrapRect = node.getBoundingClientRect()
      const ownRect = own.getBoundingClientRect()
      const header = node.querySelector('thead')?.getBoundingClientRect().height ?? 0
      const visibleTop = wrapRect.top + header
      if (ownRect.top >= visibleTop && ownRect.bottom <= wrapRect.bottom) return
      const max = node.scrollHeight - node.clientHeight
      const offset =
        ownRect.bottom > wrapRect.bottom
          ? ownRect.bottom - wrapRect.bottom
          : ownRect.top - visibleTop
      const rowHeight = node.querySelector('tbody tr')?.offsetHeight || 1
      const target = Math.ceil((node.scrollTop + offset) / rowHeight) * rowHeight
      node.scrollTop = Math.max(0, Math.min(target, max))
    })
  })

  function deltaLabel(row) {
    if (row.delta > 0) return `Поднялся на ${row.position}-е место`
    if (row.delta < 0) return `Опустился на ${row.position}-е место`
    return 'Позиция не изменилась'
  }

  function difference(value) {
    return value > 0 ? `+${value}` : `${value}`
  }
</script>

<div class="matchday-table-wrap" data-stick-scroll bind:this={wrap}>
  <table class="matchday-table">
    <thead>
      <tr>
        <th class="is-pos">#</th>
        {#if showDelta}
          <th class="is-delta"></th>
        {/if}
        <th class="is-club">Клуб</th>
        <th>И</th>
        <th>В</th>
        <th>Н</th>
        <th>П</th>
        <th>ГЗ</th>
        <th>ГП</th>
        <th>РГ</th>
        <th class="is-points">О</th>
      </tr>
    </thead>
    <tbody>
      {#each standings as row (row.club_id)}
        <tr class:is-own={row.club_id === clubId}>
          <td class="is-pos">{row.position}</td>
          {#if showDelta}
            <td class="is-delta">
              {#if row.delta > 0}
                <span class="position-delta up" title={deltaLabel(row)}>↑</span>
              {:else if row.delta < 0}
                <span class="position-delta down" title={deltaLabel(row)}>↓</span>
              {:else}
                <span class="position-delta same" title={deltaLabel(row)}>—</span>
              {/if}
            </td>
          {/if}
          <td class="is-club">
            <img src={row.club_logo} alt="" onerror={hideBrokenImage} />
            <span>{row.club_name}</span>
          </td>
          <td>{row.played}</td>
          <td>{row.won}</td>
          <td>{row.drawn}</td>
          <td>{row.lost}</td>
          <td>{row.goals_for}</td>
          <td>{row.goals_against}</td>
          <td>{difference(row.goal_difference)}</td>
          <td class="is-points">{row.points}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
