<script>
  import { hideBrokenImage } from '../../format.js'

  let { scout, status, selected = false, autofocus = false, onFocus, onOpen } = $props()
</script>

<button
  class="sc-tile"
  class:is-selected={selected}
  data-nav
  data-scout={scout.id}
  data-autofocus={autofocus ? '' : undefined}
  onfocus={onFocus}
  onclick={onOpen}
>
  <span class="sc-tile-flag">
    {#if scout.flag}<img src={scout.flag} alt="" onerror={hideBrokenImage} />{/if}
  </span>
  <strong class="sc-tile-name">{scout.name}</strong>
  <span class="sc-tile-status" class:is-free={status.tone === 'free'}>{status.title}</span>
  {#if status.detail}
    <span class="sc-tile-detail">{status.detail}</span>
  {:else}
    <span class="sc-tile-arrow">→</span>
  {/if}
  <span class="sc-tile-stars">
    {#each [0, 1, 2, 3, 4] as star (star)}
      <i class:on={star < scout.judgement}>★</i>
    {/each}
    <small>Решение</small>
  </span>
</button>
