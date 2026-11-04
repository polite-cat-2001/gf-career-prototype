<script>
  import { hideBrokenImage } from '../../format.js'

  let {
    view,
    regions,
    region,
    country,
    countryLeagues,
    networks,
    scouts,
    assignScoutId,
    onFocusRegion,
    onSelectRegion,
    onFocusCountry,
    onSelectCountry,
    onNext,
    scoutName,
    countryPosition,
  } = $props()
</script>

<div class="sc-body sc-map-screen">
  <section class="sc-map-panel">
    <div class="sc-map-head">
      <strong>{view === 'region' ? 'Карта регионов' : region?.name}</strong>
      <span>
        {view === 'region'
          ? 'Страны региона появятся на следующем шаге'
          : 'Выберите страну для сети'}
      </span>
    </div>
    <div class="sc-map">
      <div class="sc-map-grid" aria-hidden="true"></div>
      {#if view === 'region'}
        {#each regions as item, index (item.id)}
          <button
            class="sc-map-node"
            class:is-selected={region?.id === item.id}
            class:is-locked={Boolean(networks.find((net) => net.region_id === item.id))}
            style={`left:${item.x}%;top:${item.y}%`}
            data-nav
            data-autofocus={region?.id === item.id ? '' : undefined}
            onfocus={() => onFocusRegion(item.id)}
            onclick={() => onSelectRegion(item.id)}
            title={item.name}
          >
            <span class="sc-map-dot"></span>
            <span class="sc-map-label">{item.name}</span>
          </button>
        {/each}
      {:else if region}
        <span class="sc-map-region" style={`left:${region.x}%;top:${region.y}%`}>
          {region.name}
        </span>
        {#each region.countries as item, index (item.id)}
          {@const pos = countryPosition(index)}
          {@const top = parseFloat(pos.top)}
          {@const left = parseFloat(pos.left)}
          <button
            class="sc-map-node is-country"
            class:is-selected={country?.id === item.id}
            class:is-bottom={top > 66}
            class:is-left={left < 22}
            class:is-right={left > 78}
            style={`left:${pos.left};top:${pos.top}`}
            data-nav
            data-autofocus={country?.id === item.id ? '' : undefined}
            onfocus={() => onFocusCountry(item.id)}
            onclick={() => onSelectCountry(item.id)}
            title={item.name}
          >
            <span class="sc-map-flag">
              {#if item.flag}<img src={item.flag} alt="" onerror={hideBrokenImage} />{/if}
            </span>
            <span class="sc-map-label">{item.name}</span>
          </button>
        {/each}
      {/if}
    </div>
  </section>

  <aside class="sc-map-side">
    <div class="sc-map-list scroll-area">
      {#if view === 'region'}
        <div class="sc-map-list-title">{region?.name}</div>
        {#each region?.countries ?? [] as item (item.id)}
          <button
            class="sc-map-row"
            class:is-selected={country?.id === item.id}
            data-nav
            onfocus={() => onFocusCountry(item.id)}
            onclick={() => onSelectCountry(item.id)}
          >
            <span class="sc-hire-flag">
              {#if item.flag}<img src={item.flag} alt="" onerror={hideBrokenImage} />{/if}
            </span>
            <span>{item.name}</span>
          </button>
        {/each}
      {:else}
        <div class="sc-map-list-title">{country?.name}</div>
        {#each countryLeagues as league (league.id)}
          <div class="sc-map-league">
            {#if league.logo}
              <img src={league.logo} alt="" onerror={hideBrokenImage} />
            {/if}
            <span>{league.name}</span>
            <small>{league.clubs_count} клубов</small>
          </div>
        {/each}
        {#if !countryLeagues.length}
          <p class="sc-panel-muted">Лиги загружаются…</p>
        {/if}
      {/if}
    </div>

    <div class="sc-scout-mini">
      <div class="sc-panel-label">Скаут</div>
      <div class="sc-panel-head">
        <span class="sc-panel-flag">
          {#if scouts.find((scout) => scout.id === assignScoutId)?.flag}
            <img
              src={scouts.find((scout) => scout.id === assignScoutId)?.flag}
              alt=""
              onerror={hideBrokenImage}
            />
          {/if}
        </span>
        <div>
          <strong class="sc-panel-name">{scoutName(assignScoutId)}</strong>
          <span class="sc-panel-country">Сеть поиска</span>
        </div>
      </div>
      <div class="sc-panel-row">
        <span>Опыт</span>
        <b>{scouts.find((scout) => scout.id === assignScoutId)?.experience ?? 0} / 5</b>
      </div>
      <div class="sc-panel-row">
        <span>Решение</span>
        <b>{scouts.find((scout) => scout.id === assignScoutId)?.judgement ?? 0} / 5</b>
      </div>
    </div>

    <button class="sc-wide-action" data-nav onclick={onNext}>
      <span>{view === 'region' ? 'Далее' : 'Организовать сеть'}</span>
      <span class="sc-key">A</span>
    </button>
  </aside>
</div>
