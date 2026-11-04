<script>
  import Glyph from '../../ui/Glyph.svelte'
  import LeagueTableTile from './LeagueTableTile.svelte'
  import NextMatchTile from './NextMatchTile.svelte'

  let {
    career,
    season,
    nextMatch,
    displayDate,
    trackDays,
    trackWidth,
    trackShift,
    isMatchDay,
    simulating,
    advancing,
    ownRow,
    tableRows,
    tableRound,
    inert,
    onPlay,
    onOpenSimulation,
    onNext,
  } = $props()
</script>

<div class="home-grid" inert={inert ? true : undefined}>
  <NextMatchTile
    {career}
    {season}
    {nextMatch}
    {displayDate}
    {trackDays}
    {trackWidth}
    {trackShift}
    {isMatchDay}
    {simulating}
    {advancing}
    {ownRow}
    onPlay={onPlay}
    onOpenSimulation={onOpenSimulation}
    onNext={onNext}
  />

  <section class="gf-tile home-tile home-transfer is-soon">
    <span class="home-eyebrow">Переговоры</span>
    <h2 class="gf-tile__title">Центр трансферов</h2>
    <span class="home-soon">скоро</span>
    <p class="gf-tile__sub">Предложения, переговоры и подписания — скоро.</p>
    <span class="gf-tile__glyph"><Glyph name="shirt" size={68} /></span>
  </section>

  <LeagueTableTile
    rows={tableRows}
    standings={season?.standings ?? []}
    clubId={career.club.id}
    round={tableRound}
  />

  <section class="gf-tile home-tile home-news is-soon">
    <h2 class="gf-tile__title">Срочные новости</h2>
    <span class="home-soon">скоро</span>
    <p class="gf-tile__sub">Лента новостей и результаты матчей — скоро.</p>
    <span class="gf-tile__glyph"><Glyph name="globe" size={68} /></span>
  </section>

  <section class="gf-tile home-tile home-training is-soon">
    <h2 class="gf-tile__title">Тренировка</h2>
    <span class="home-soon">скоро</span>
    <p class="gf-tile__sub">До пяти тренировок в неделю: характеристики и стоимость.</p>
    <span class="gf-tile__glyph"><Glyph name="tactics" size={64} /></span>
  </section>
</div>
