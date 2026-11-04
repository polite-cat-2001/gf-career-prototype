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
  <span class="tf-hub-card-head">
    <span class="tf-hub-card-status">{card.enabled ? 'Открыто' : 'Скоро'}</span>
    {#if card.soon}<span class="tf-hub-card-soon">{card.soon}</span>{/if}
  </span>
  <strong class="tf-hub-card-title">{card.label}</strong>
  <span class="tf-hub-card-note">{card.note}</span>
  <span class="tf-hub-card-icon">
    <Icon name={card.icon} size={card.enabled ? 72 : 40} />
  </span>
</button>
