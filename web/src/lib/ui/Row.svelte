<script>
  let {
    title = '',
    sub = '',
    meta = '',
    tags = [],
    disabled = false,
    autofocus = false,
    onclick,
    lead,
    trail,
    children,
    style = '',
    ...rest
  } = $props()
</script>

<button
  type="button"
  class="gf-row"
  data-nav
  data-autofocus={autofocus ? '' : undefined}
  {disabled}
  style={style}
  {onclick}
  {...rest}
>
  {#if lead}
    <span class="gf-row__lead">{@render lead()}</span>
  {/if}

  <span class="gf-row__main">
    <span class="gf-row__title">{title}</span>
    {#if sub}
      <span class="gf-row__sub">{sub}</span>
    {/if}
    {#if children}
      {@render children()}
    {/if}
  </span>

  {#if meta || tags.length || trail}
    <span class="gf-row__side">
      {#if meta}
        <span class="gf-row__meta">{meta}</span>
      {/if}
      {#if tags.length}
        <span class="gf-row__tags">{tags.join(' · ')}</span>
      {/if}
      {#if trail}
        {@render trail()}
      {/if}
    </span>
  {/if}
</button>
