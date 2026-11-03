<script>
  import Icon from '../../Icon.svelte'

  let { card, onOpen } = $props()
</script>

<button
  class="tf-hub-card tf-card-{card.id}"
  class:is-disabled={!card.enabled}
  data-nav
  data-autofocus={card.enabled ? '' : undefined}
  disabled={!card.enabled}
  onclick={onOpen}
>
  <div class="tf-hub-card-head">
    <span class="eyebrow">{card.enabled ? 'Открыто' : 'Скоро'}</span>
    {#if card.soon}<span class="soon-tag">{card.soon}</span>{/if}
  </div>
  <strong class="tf-hub-card-title">{card.label}</strong>
  <span class="tf-hub-card-note">{card.note}</span>
  <span class="tf-hub-card-icon">
    <Icon name={card.icon} size={card.enabled ? 68 : 38} />
  </span>
</button>
