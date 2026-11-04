<script>
  import { onMount } from 'svelte'

  let { tabs = [], active = '', focused = false, onselect } = $props()

  let bar = $state(null)
  let left = $state(0)
  let width = $state(0)
  let ready = $state(false)

  const index = $derived(Math.max(0, tabs.findIndex((tab) => tab.id === active)))

  function measure() {
    if (!bar) return
    const element = bar.querySelectorAll('.gf-tab')[index]
    if (!element) return
    left = element.offsetLeft
    width = element.offsetWidth
    ready = true
  }

  $effect(() => {
    index
    tabs
    bar
    measure()
  })

  onMount(() => {
    document.fonts?.ready.then(() => measure())
    const onResize = () => measure()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  })
</script>

<nav
  class="gf-tabbar"
  class:is-ready={ready}
  class:is-focused={focused}
  bind:this={bar}
  aria-label="Разделы"
>
  <span class="gf-tabbar__marker" style="transform: translateX({left}px); width: {width}px;"></span>
  {#each tabs as tab (tab.id)}
    <button
      type="button"
      class="gf-tab"
      class:is-active={tab.id === active}
      disabled={tab.disabled}
      tabindex="-1"
      onclick={() => !tab.disabled && onselect?.(tab.id)}
    >
      {tab.label}
    </button>
  {/each}
</nav>
