<script>
  let { display, comparing = false, delta = 0 } = $props()
</script>

<div class="team-strength">
  <svg class="team-shield" viewBox="0 0 64 72" aria-hidden="true">
    <path d="M32 2 60 11v25c0 16-12 27-28 34C16 63 4 52 4 36V11z"></path>
  </svg>
  <strong>{display}</strong>
  {#if comparing && delta > 0.05}
    <span class="team-delta up" aria-label="Сила состава вырастет">▲</span>
  {/if}
  {#if comparing && delta < -0.05}
    <span class="team-delta down" aria-label="Сила состава упадёт">▼</span>
  {/if}
</div>
