<script>
  import PlayerCard from '../../PlayerCard.svelte'
  import { formatValue, hideBrokenImage } from '../../format.js'
  import StrengthBadge from '../shared/StrengthBadge.svelte'
  import { pitchSpot } from '../utils/pitch.js'
  import SquadTile from './SquadTile.svelte'

  let {
    career,
    lineup,
    summary,
    squadTiles,
    teamDisplay,
    comparing,
    teamDelta,
    onPlan,
    onCentre,
  } = $props()
</script>

<div class="squad-overview">
  <button class="squad-team" data-nav data-autofocus onclick={onPlan}>
    <div class="squad-team-head">
      <img class="squad-team-crest" src={career.club.logo} alt="" onerror={hideBrokenImage} />
      <div class="squad-team-title">
        <span class="squad-kicker">Состав клуба</span>
        <strong>{career.club.name}: по умолч.</strong>
        <span>{lineup.formation} · {career.club.league_name}</span>
      </div>
      <span class="squad-team-action">A · план игры</span>
    </div>

    <div class="pitch pitch-plan">
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
          preview
          positionStyle={`left:${spot.left}%; top:${spot.top}`}
        />
      {/each}
      <StrengthBadge display={teamDisplay} {comparing} delta={teamDelta} />
    </div>

    <div class="squad-team-foot">
      <span>{summary.squad_size} игроков · средний возраст {summary.average_age ?? '—'}</span>
      <span>{formatValue(summary.total_market_value)}</span>
    </div>
  </button>

  <div class="squad-tiles">
    {#each squadTiles as tile (tile.id)}
      <SquadTile {tile} club={career.club} onOpen={onCentre} />
    {/each}
  </div>
</div>
