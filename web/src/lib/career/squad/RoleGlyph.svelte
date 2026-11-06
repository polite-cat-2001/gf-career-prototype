<script>
  let { role = 'captain' } = $props()

  const mirrored = $derived(role === 'free_kick_right' || role === 'corner_right')
</script>

{#if role === 'captain'}
  <span class="role-glyph-c">C</span>
{:else}
  <svg
    class="role-glyph"
    class:is-mirrored={mirrored}
    viewBox="0 0 64 40"
    aria-hidden="true"
  >
    {#if role === 'penalties'}
      <path d="M16 7h32v13H16z" />
      <path d="M16 7v-2M48 7v-2" />
      <path d="M32 31v-6" />
      <path d="M28.5 27.5 32 24l3.5 3.5" />
      <circle cx="32" cy="34" r="2.6" />
      <path d="M14 36h36" />
    {:else if role === 'corner_left' || role === 'corner_right'}
      <path d="M13 8v24" />
      <path d="M13 8h10l-3 4 3 4H13" />
      <circle cx="19" cy="32" r="2.4" />
      <path d="M20 30c9-4 16-9 22-15" stroke-dasharray="2 3" />
      <path d="M38 16l4-2 0 4" />
    {:else}
      <path d="M46 10h12v20H46" />
      <path d="M46 14h4M46 26h4" />
      {#if role === 'free_kick_long'}
        <path d="M40 18h7v12h-7z" />
        <circle cx="13" cy="31" r="2.4" />
        <path d="M16 30c10-3 17-6 22-10" stroke-dasharray="2 3" />
        <path d="M36 19l5-2 0 4" />
      {:else}
        <path d="M28 19h4v11h-4z M33 18h4v12h-4z M38 20h4v10h-4z" />
        <circle cx="14" cy="31" r="2.4" />
        <path d="M17 29c7-8 14-11 23-12" stroke-dasharray="2 3" />
        <path d="M38 15l5 2-3 3" />
      {/if}
    {/if}
  </svg>
{/if}
