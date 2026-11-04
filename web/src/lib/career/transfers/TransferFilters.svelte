<script>
  import Icon from '../../Icon.svelte'
  import {
    transferFieldLabel,
    transferPositionShort,
    transferValueMeta,
  } from '../utils/transfers.js'
  import TransferFilterTile from './TransferFilterTile.svelte'

  let {
    filters,
    editing,
    roleRow,
    ageRow,
    countries,
    leagues,
    clubs,
    oskOpen,
    onOpenOsk,
    onToggle,
    onStepActive,
    onRoleStep,
    onRangeStep,
  } = $props()

  const context = $derived({ filters, countries, leagues, clubs })
</script>

<div class="tf-filters" inert={oskOpen ? true : undefined}>
  <div class="tf-filter-grid">
    <button type="button" class="tf-cell tf-name" data-nav data-filter="name" onclick={onOpenOsk}>
      <span class="tf-label">Имя игрока</span>
      <span class="tf-name-art"><Icon name="users" size={64} /></span>
      <span class="tf-value">{filters.name || 'Люб.'}</span>
    </button>

    <button
      type="button"
      class="tf-cell tf-role"
      class:is-editing={editing === 'positionRole'}
      data-nav
      data-filter="positionRole"
      data-edit={editing === 'positionRole' ? 'true' : undefined}
      onclick={() => onToggle('positionRole')}
    >
      <span class="tf-label">Позиция и амплуа</span>
      <div class="tf-age-rows">
        <div class="tf-role-row" class:is-active={editing === 'positionRole' && roleRow === 'group'}>
          <span>Позиция</span>
          <span class="tf-range-control">
            {#if editing === 'positionRole'}
              <span
                class="tf-arrow"
                onclick={(event) => {
                  event.stopPropagation()
                  onRoleStep('group', -1)
                }}>‹</span
              >
            {/if}
            <span class="tf-bar-main">
              <strong>{transferFieldLabel('group', context)}</strong>
            </span>
            {#if editing === 'positionRole'}
              <span
                class="tf-arrow"
                onclick={(event) => {
                  event.stopPropagation()
                  onRoleStep('group', 1)
                }}>›</span
              >
            {/if}
          </span>
        </div>
        <div
          class="tf-role-row"
          class:is-active={editing === 'positionRole' && roleRow === 'position'}
        >
          <span>Амплуа</span>
          <span class="tf-range-control">
            {#if editing === 'positionRole'}
              <span
                class="tf-arrow"
                onclick={(event) => {
                  event.stopPropagation()
                  onRoleStep('position', -1)
                }}>‹</span
              >
            {/if}
            <span class="tf-bar-main">
              <strong>{transferPositionShort(filters.position)}</strong>
            </span>
            {#if editing === 'positionRole'}
              <span
                class="tf-arrow"
                onclick={(event) => {
                  event.stopPropagation()
                  onRoleStep('position', 1)
                }}>›</span
              >
            {/if}
          </span>
        </div>
      </div>
    </button>

    {#each [
      ['citizenship', 'Гражданство'],
      ['league', 'Лига'],
      ['status', 'Трансферный статус'],
      ['country', 'Страна'],
      ['club', 'Клуб'],
    ] as [field, label] (field)}
      {#if field === 'status'}
        <button
          type="button"
          class="tf-cell tf-age"
          class:is-editing={editing === 'age'}
          data-nav
          data-filter="age"
          data-edit={editing === 'age' ? 'true' : undefined}
          onclick={() => onToggle('age')}
        >
          <span class="tf-label">Лет</span>
          <div class="tf-age-rows">
            <div class="tf-range-row" class:is-active={editing === 'age' && ageRow === 'ageMin'}>
              <span>МИН.</span>
              <span class="tf-range-control">
                {#if editing === 'age'}
                  <span
                    class="tf-arrow"
                    onclick={(event) => {
                      event.stopPropagation()
                      onRangeStep('ageMin', -1)
                    }}>‹</span
                  >
                {/if}
                <strong>{filters.ageMin ?? 'Люб.'}</strong>
                {#if editing === 'age'}
                  <span
                    class="tf-arrow"
                    onclick={(event) => {
                      event.stopPropagation()
                      onRangeStep('ageMin', 1)
                    }}>›</span
                  >
                {/if}
              </span>
            </div>
            <div class="tf-range-row" class:is-active={editing === 'age' && ageRow === 'ageMax'}>
              <span>МАКС.</span>
              <span class="tf-range-control">
                {#if editing === 'age'}
                  <span
                    class="tf-arrow"
                    onclick={(event) => {
                      event.stopPropagation()
                      onRangeStep('ageMax', -1)
                    }}>‹</span
                  >
                {/if}
                <strong>{filters.ageMax ?? 'Люб.'}</strong>
                {#if editing === 'age'}
                  <span
                    class="tf-arrow"
                    onclick={(event) => {
                      event.stopPropagation()
                      onRangeStep('ageMax', 1)
                    }}>›</span
                  >
                {/if}
              </span>
            </div>
          </div>
        </button>
      {/if}

      <TransferFilterTile
        {field}
        {label}
        editing={editing === field}
        meta={transferValueMeta(field, context)}
        value={transferFieldLabel(field, context)}
        onToggle={() => onToggle(field)}
        onStep={(delta) => onStepActive(delta)}
      />
    {/each}
  </div>
</div>
