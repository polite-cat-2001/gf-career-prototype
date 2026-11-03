<script>
  import { hideBrokenImage } from '../../format.js'

  let { field, label, editing, meta, value, onToggle, onStep } = $props()
</script>

<button
  type="button"
  class="tf-cell"
  class:is-editing={editing}
  data-nav
  data-filter={field}
  data-edit={editing ? 'true' : undefined}
  onclick={onToggle}
>
  <span class="tf-label">{label}</span>
  <div class="tf-value-bar">
    {#if editing}
      <span
        class="tf-arrow"
        onclick={(event) => {
          event.stopPropagation()
          onStep(-1)
        }}>‹</span
      >
    {/if}
    <span class="tf-bar-main">
      {#if meta.logo}
        <img src={meta.logo} alt="" onerror={hideBrokenImage} />
      {/if}
      {#if meta.badge}
        <span class="tf-badge">{meta.badge}</span>
      {/if}
      <strong>{value}</strong>
    </span>
    {#if editing}
      <span
        class="tf-arrow"
        onclick={(event) => {
          event.stopPropagation()
          onStep(1)
        }}>›</span
      >
    {/if}
  </div>
</button>
