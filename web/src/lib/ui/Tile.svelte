<script>
  import Glyph from './Glyph.svelte'

  let {
    title = '',
    sub = '',
    meta = '',
    tags = [],
    glyph = '',
    glyphSize = 76,
    hero = false,
    wide = false,
    bare = false,
    disabled = false,
    autofocus = false,
    onclick,
    art,
    children,
    style = '',
    ...rest
  } = $props()
</script>

<button
  type="button"
  class="gf-tile"
  class:gf-tile--hero={hero}
  class:gf-tile--wide={wide}
  data-nav
  data-autofocus={autofocus ? '' : undefined}
  {disabled}
  style={style}
  {onclick}
  {...rest}
>
  {#if !bare}
    <span class="gf-tile__title">{title}</span>
    {#if sub}
      <span class="gf-tile__sub">{sub}</span>
    {/if}

    {#if meta || tags.length}
      <span class="gf-tile__meta">
        {#if meta}
          <span class="gf-tile__note">{meta}</span>
        {/if}
        {#if tags.length}
          <span class="gf-tile__tags">{tags.join(' · ')}</span>
        {/if}
      </span>
    {/if}

    {#if glyph}
      <span class="gf-tile__glyph"><Glyph name={glyph} size={glyphSize} /></span>
    {/if}

    {#if art}
      <span class="gf-tile__art">{@render art()}</span>
    {/if}
  {/if}

  {#if children}
    {@render children()}
  {/if}
</button>
