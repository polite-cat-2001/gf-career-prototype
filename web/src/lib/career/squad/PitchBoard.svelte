<script>
  import PlayerCard from '../../PlayerCard.svelte'
  import StrengthBadge from '../shared/StrengthBadge.svelte'
  import { pitchSpot } from '../utils/pitch.js'

  let {
    lineup,
    anchorId,
    teamDisplay,
    comparing,
    teamDelta,
    onCardFocus,
    onCardEnter,
    onCardActivate,
  } = $props()
</script>

<div class="pitch pitch-plan-large">
  <span class="pitch-surface"></span>
  <svg class="pitch-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
    <polygon points="13,2 87,2 98,98 2,98"></polygon>
    <line x1="7" y1="50" x2="93" y2="50"></line>
    <ellipse cx="50" cy="50" rx="12" ry="16"></ellipse>
    <polygon points="33,2 67,2 70,18 30,18"></polygon>
    <polygon points="25,98 75,98 70,80 30,80"></polygon>
  </svg>
  {#each lineup.slots as slot (slot.position + slot.player.id)}
    {@const spot = pitchSpot(slot)}
    <PlayerCard
      player={slot.player}
      role={slot.role}
      line={spot.line}
      interactive
      selected={anchorId === slot.player.id}
      positionStyle={`left:${spot.left}%; top:${spot.top}`}
      onfocus={(event) => onCardFocus(slot.player, event)}
      onmouseenter={onCardEnter}
      onclick={() => onCardActivate(slot.player)}
    />
  {/each}
  <StrengthBadge display={teamDisplay} {comparing} delta={teamDelta} />
</div>
