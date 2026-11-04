<script>
  import Icon from '../../Icon.svelte'
  import { hideBrokenImage } from '../../format.js'

  let { tile, club, onOpen } = $props()
</script>

{#if tile.selected}
  <div class="squad-tile is-selected" aria-current="true">
    <span class="squad-tile-label">{tile.label}</span>
    <span class="squad-tile-icon">
      <img src={club.logo} alt="" onerror={hideBrokenImage} />
      <span class="squad-tile-check"><Icon name="check" size={18} /></span>
    </span>
    <span class="squad-tile-note">{club.name}</span>
  </div>
{:else if tile.id === 'centre'}
  <button class="squad-tile" data-nav onclick={onOpen}>
    <span class="squad-tile-label">{tile.label}</span>
    <span class="squad-tile-icon"><Icon name={tile.icon} size={44} /></span>
    <span class="squad-tile-note">{tile.note}</span>
  </button>
{:else}
  <div class="squad-tile is-disabled" aria-disabled="true">
    <span class="squad-tile-label">{tile.label}</span>
    <span class="squad-tile-icon"><Icon name={tile.icon} size={44} /></span>
    <span class="squad-tile-note">{tile.note}</span>
  </div>
{/if}
