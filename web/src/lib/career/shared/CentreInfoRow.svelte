<script>
  let { label, value } = $props()
</script>

<div class="gf-info-row">
  <span>{label}</span>
  <strong>{value}</strong>
</div>

<style>
  .gf-info-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 2px;
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.82);
    color: var(--ink);
  }

  .gf-info-row span {
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--ink-2);
  }

  .gf-info-row strong {
    font-size: 18px;
    font-weight: 600;
    text-align: right;
    color: var(--ink);
  }
</style>
