<script>
  import { contractRoleLabel, formatValue, plural } from '../../format.js'

  let { terms } = $props()
</script>

<div class="gf-terms">
  <div class="gf-term">
    <span>Зарплата / нед.</span>
    <strong>{formatValue(terms.weekly_wage)}</strong>
  </div>
  <div class="gf-term">
    <span>Срок</span>
    <strong>
      {terms.years}
      {plural(terms.years, 'год', 'года', 'лет')}
    </strong>
  </div>
  <div class="gf-term">
    <span>Амплуа</span>
    <strong>{contractRoleLabel(terms.squad_role)}</strong>
  </div>
  <div class="gf-term">
    <span>Отступные</span>
    <strong>{formatValue(terms.release_clause)}</strong>
  </div>
</div>

<style>
  .gf-terms {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 2px;
  }

  .gf-term {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.82);
    color: var(--ink);
  }

  .gf-term span {
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-2);
  }

  .gf-term strong {
    overflow: hidden;
    font-family: var(--font-heading);
    font-size: 22px;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: 0.01em;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: var(--ink);
  }
</style>
