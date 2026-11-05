<script>
  let { value = 0, size = 18 } = $props()

  const mood = $derived(Number(value) >= 70 ? 'good' : Number(value) >= 40 ? 'ok' : 'low')
</script>

<svg
  class="morale-face"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  aria-hidden="true"
>
  <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.6" />
  <circle cx="8.6" cy="9.8" r="1.15" fill="currentColor" />
  <circle cx="15.4" cy="9.8" r="1.15" fill="currentColor" />
  {#if mood === 'good'}
    <path
      d="M8.2 14.2c.9 1.6 2.3 2.4 3.8 2.4s2.9-.8 3.8-2.4"
      fill="none"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
  {:else if mood === 'ok'}
    <path
      d="M8.8 15h6.4"
      fill="none"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
  {:else}
    <path
      d="M8.2 16.2c.9-1.6 2.3-2.4 3.8-2.4s2.9.8 3.8 2.4"
      fill="none"
      stroke="currentColor"
      stroke-width="1.6"
      stroke-linecap="round"
    />
  {/if}
</svg>
