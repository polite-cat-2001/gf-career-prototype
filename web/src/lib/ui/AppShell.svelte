<script>
  import Legend from './Legend.svelte'

  let {
    status = '',
    statusError = false,
    hints = [],
    note = '',
    brand = 'GF',
    brandAccent = 'CAREER',
    fill = false,
    header,
    children,
  } = $props()
</script>

<div class="gf-stage">
  <img class="gf-stage__photo" src="/stadium.jpg" alt="" />
</div>

<div class="gf-app">
  {#if status}
    <div class="gf-status" class:is-error={statusError}>{status}</div>
  {/if}

  <div class="gf-frame" class:is-fill={fill}>
    <div class="gf-panel-wrap" class:is-fill={fill}>
      {#if header}
        {@render header()}
      {/if}
      <div class="gf-content" class:is-fill={fill}>
        {#if children}
          {@render children()}
        {/if}
      </div>
      <Legend {hints} {note} />
    </div>
  </div>

  <div class="gf-brand">{brand} <span>{brandAccent}</span></div>
</div>
