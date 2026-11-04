<script>
  let { name = 'play', size = 96 } = $props()
</script>

<svg
  class="glyph"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.5"
  stroke-linecap="square"
  stroke-linejoin="miter"
  aria-hidden="true"
>
  {#if name === 'shirt'}
    <path
      d="M9 4.2 4.6 6.4 3.2 10.9 6.4 12.2 7.4 10.4V19.6h9.2v-9.2l1 1.8 3.2-1.3-1.4-4.5L15 4.2l-1.6 1.6h-2.8Z"
    />
  {:else if name === 'play'}
    <path d="M8.5 5.5 19 12 8.5 18.5Z" fill="currentColor" stroke="none" />
  {:else if name === 'trophy'}
    <path d="M7.5 4h9v4.6a4.5 4.5 0 0 1-9 0Z" />
    <path d="M7.5 5.6H5v1.6a3 3 0 0 0 3 3M16.5 5.6H19v1.6a3 3 0 0 1-3 3" />
    <path d="M12 13.2V17M8.5 20h7" />
  {:else if name === 'network'}
    <circle cx="12" cy="5.4" r="2.6" />
    <circle cx="5.6" cy="18" r="2.6" />
    <circle cx="18.4" cy="18" r="2.6" />
    <path d="M10.3 7.7 7 15.6M13.7 7.7 17 15.6M8.2 18h7.6" />
  {:else if name === 'sliders'}
    <path d="M4 7h16M4 12h16M4 17h16" />
    <rect x="7.5" y="5" width="3.4" height="4" fill="currentColor" stroke="none" />
    <rect x="13.4" y="10" width="3.4" height="4" fill="currentColor" stroke="none" />
    <rect x="6.2" y="15" width="3.4" height="4" fill="currentColor" stroke="none" />
  {:else if name === 'gamepad'}
    <path d="M7.6 7.5h8.8a4 4 0 0 1 3.9 3l.9 3.6a2.3 2.3 0 0 1-3.9 2.1l-1.8-1.7H8.5l-1.8 1.7a2.3 2.3 0 0 1-3.9-2.1l.9-3.6a4 4 0 0 1 3.9-3Z" />
    <path d="M8.2 10.6v3M6.7 12.1h3" />
    <circle cx="15.6" cy="11.2" r=".85" fill="currentColor" stroke="none" />
    <circle cx="17.4" cy="13" r=".85" fill="currentColor" stroke="none" />
  {:else if name === 'globe'}
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18" />
    <path d="M12 3c2.7 2.6 4.2 5.7 4.2 9s-1.5 6.4-4.2 9c-2.7-2.6-4.2-5.7-4.2-9S9.3 5.6 12 3Z" />
  {:else if name === 'keyboard'}
    <rect x="2.6" y="7.2" width="18.8" height="9.6" />
    <path
      d="M6 10.4h1.2M9 10.4h1.2M12 10.4h1.2M15 10.4h1.2M18 10.4h.4M6 13.6h1.2M17 13.6h1.2M9.2 13.6h5.6"
    />
  {:else if name === 'monitor'}
    <rect x="3.5" y="5" width="17" height="11.5" />
    <path d="M9 20h6M12 16.5V20" />
  {:else if name === 'volume'}
    <path d="M5 9.6h3.2L13 5.8v12.4L8.2 14.4H5Z" fill="currentColor" stroke="none" />
    <path d="M15.8 8.8a4.4 4.4 0 0 1 0 6.4M18.2 6.4a7.8 7.8 0 0 1 0 11.2" />
  {:else if name === 'pitch'}
    <rect x="3" y="5" width="18" height="14" />
    <path d="M12 5v14" />
    <circle cx="12" cy="12" r="3" />
    <path d="M3 9h3v6H3M21 9h-3v6h3" />
  {:else if name === 'tactics'}
    <rect x="4" y="4" width="16" height="16" />
    <path d="M8 4v16" />
    <circle cx="6" cy="8" r="1" fill="currentColor" stroke="none" />
    <circle cx="6" cy="12" r="1" fill="currentColor" stroke="none" />
    <circle cx="6" cy="16" r="1" fill="currentColor" stroke="none" />
    <path d="M12 9h5M12 12h5M12 15h5" />
  {:else if name === 'sides'}
    <path d="M3 5v14M21 5v14" />
    <path d="M8 8 4 12l4 4M16 8l4 4-4 4" />
  {:else if name === 'layers'}
    <path d="M12 3l9 5-9 5-9-5 9-5z" />
    <path d="M3 13l9 5 9-5" />
  {:else}
    <circle cx="12" cy="12" r="9.2" />
  {/if}
</svg>

<style>
  .glyph {
    display: block;
    flex: 0 0 auto;
  }
</style>
