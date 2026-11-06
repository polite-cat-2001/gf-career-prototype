<script>
  let {
    clubName,
    currentFormation,
    formations,
    page,
    pageCount,
    onPreview,
    onSelect,
    onScroll,
  } = $props()

  function handleWheel(event) {
    if (!event.deltaY) return
    event.preventDefault()
    onScroll?.(event.deltaY)
  }
</script>

<section class="scheme-panel" aria-label="Схемы клуба">
  <header class="scheme-panel-head">
    <span class="scheme-panel-title">Схемы: {clubName}</span>
    <span class="scheme-page">{page + 1} / {pageCount}</span>
  </header>
  <div class="scheme-viewport">
    <div class="scheme-cards" onwheel={handleWheel}>
      {#each formations as formation (formation.id)}
        {@const selected = formation.id === currentFormation}
        <button
          class="scheme-card"
          class:is-current={selected}
          data-nav
          data-step
          data-formation={formation.id}
          aria-pressed={selected}
          onfocus={() => onPreview?.(formation.id)}
          onclick={() => onSelect(formation.id)}
        >
          <span class="scheme-card-name">{formation.label}</span>
          <span class="scheme-mini" aria-hidden="true">
            <span class="scheme-mini-surface"></span>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none">
              <polygon points="10,0 90,0 100,100 0,100"></polygon>
              <line x1="0" y1="50" x2="100" y2="50"></line>
              <ellipse cx="50" cy="50" rx="14" ry="17"></ellipse>
              <polygon points="30,0 70,0 75,20 25,20"></polygon>
              <polygon points="24,100 76,100 70,80 30,80"></polygon>
            </svg>
            {#each formation.slots as slot (slot.position + slot.x + slot.y)}
              <i
                class:is-keeper={slot.position === 'GK'}
                style={`left:${slot.x}%; top:${slot.y}%`}
              ></i>
            {/each}
          </span>
          {#if selected}
            <span class="scheme-check" aria-hidden="true">✓</span>
          {/if}
        </button>
      {/each}
    </div>
    <span class="scheme-rail" aria-hidden="true">
      <span
        class="scheme-rail-thumb"
        style={`height:${100 / pageCount}%; top:${(100 / pageCount) * page}%`}
      ></span>
    </span>
  </div>
</section>
