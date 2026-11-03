<script>
  import Icon from '../../Icon.svelte'
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

<div class="hub-grid" inert={inert ? true : undefined}>
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

  <section class="widget widget-centre is-soon" style="grid-area: centre">
    <div class="widget-head">
      <div>
        <span class="eyebrow">Переговоры</span>
        <strong class="widget-title">Центр трансферов</strong>
      </div>
      <span class="soon-tag">нужен #4</span>
    </div>
    <Icon name="shirt" size={76} />
    <p class="widget-note">Предложения, переговоры и подписания — после трансферного тикета.</p>
    <div class="widget-dots" aria-hidden="true"><i class="active"></i><i></i><i></i></div>
  </section>

  <LeagueTableTile rows={tableRows} clubId={career.club.id} round={tableRound} />

  <section class="widget widget-news is-soon" style="grid-area: news">
    <div class="widget-head">
      <strong class="widget-title widget-title-sm">Срочные новости</strong>
      <span class="soon-tag">после #4</span>
    </div>
    <Icon name="news" size={68} />
    <p class="widget-note">Лента новостей и результаты матчей — после календаря и матчей.</p>
  </section>

  <section class="widget widget-training is-soon" style="grid-area: training">
    <div class="widget-head">
      <strong class="widget-title widget-title-sm">Тренировка</strong>
      <span class="soon-tag">после #4</span>
    </div>
    <Icon name="chart" size={56} />
    <p class="widget-note">До пяти тренировок в неделю: характеристики, рейтинг и стоимость.</p>
  </section>
</div>
