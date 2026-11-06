<script>
  import placeholderUrl from '../../assets/player-placeholder.png'

  let { src = '', alt = '', loading = undefined } = $props()

  let failed = $state(false)

  $effect(() => {
    void src
    failed = false
  })
</script>

{#if src && !failed}
  <img {src} {alt} {loading} onerror={() => (failed = true)} />
{:else}
  <span
    class="gf-player-photo__fallback"
    style:--gf-player-photo-mask={`url("${placeholderUrl}")`}
    aria-hidden="true"
  ></span>
{/if}

<style>
  .gf-player-photo__fallback {
    display: block;
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
    background-color: #bababa;
    background-color: color-mix(in srgb, currentColor 30%, #ffffff 70%);
    -webkit-mask-image: var(--gf-player-photo-mask);
    mask-image: var(--gf-player-photo-mask);
    -webkit-mask-position: center bottom;
    mask-position: center bottom;
    -webkit-mask-size: contain;
    mask-size: contain;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
  }
</style>
