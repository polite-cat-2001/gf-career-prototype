<script>
  import { radarGrid, radarLabelPos, radarPoints } from '../utils/radar.js'

  let { values, secondary = null } = $props()
</script>

<svg class="radar" viewBox="-10 -10 164 164" aria-hidden="true">
  <polygon class="radar-grid" points={radarGrid(values)}></polygon>
  <polygon class="radar-grid inner" points={radarGrid(values, 22)}></polygon>
  {#if secondary?.length}
    <polygon class="radar-compare" points={radarPoints(secondary)}></polygon>
  {/if}
  <polygon class="radar-fill" points={radarPoints(values)}></polygon>
  {#each values as axis, index (axis.label)}
    {@const pos = radarLabelPos(index, values.length)}
    <text class="radar-label" x={pos.x} y={pos.y}>{axis.label}</text>
  {/each}
</svg>
