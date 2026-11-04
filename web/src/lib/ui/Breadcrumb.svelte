<script>
  let { items = [] } = $props()
</script>

<nav class="gf-crumbs" aria-label="Путь">
  {#each items as item, i}
    {#if i > 0}
      <span class="gf-crumbs__sep" aria-hidden="true"></span>
    {/if}
    <span class="gf-crumbs__item" class:is-current={i === items.length - 1}>{item}</span>
  {/each}
</nav>
