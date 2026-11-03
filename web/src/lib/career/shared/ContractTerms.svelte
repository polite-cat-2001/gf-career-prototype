<script>
  import { contractRoleLabel, formatValue, plural } from '../../format.js'

  let { terms } = $props()
</script>

<div class="neg-term-grid">
  <div class="neg-term">
    <span>Зарплата / нед.</span>
    <strong>{formatValue(terms.weekly_wage)}</strong>
  </div>
  <div class="neg-term">
    <span>Срок</span>
    <strong>
      {terms.years}
      {plural(terms.years, 'год', 'года', 'лет')}
    </strong>
  </div>
  <div class="neg-term">
    <span>Амплуа</span>
    <strong>{contractRoleLabel(terms.squad_role)}</strong>
  </div>
  <div class="neg-term">
    <span>Отступные</span>
    <strong>{formatValue(terms.release_clause)}</strong>
  </div>
</div>
