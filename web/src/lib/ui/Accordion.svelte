<script>
  let { open = false, children } = $props()
</script>

<div
  class="gf-accordion"
  class:is-open={open}
  inert={!open}
  data-nav-trap
>
  <div class="gf-accordion__inner">
    {@render children?.()}
  </div>
</div>
