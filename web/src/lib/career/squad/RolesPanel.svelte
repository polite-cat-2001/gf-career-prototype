<script>
  import RoleGlyph from './RoleGlyph.svelte'

  let { roles, focusedId, pickingId, onFocus, onSelect } = $props()

  function playerLabel(role) {
    return role.player?.last_name || role.player?.name || '—'
  }
</script>

<section class="role-panel" aria-label="Амплуа игроков" inert={Boolean(pickingId)}>
  <div class="role-grid">
    {#each roles as role (role.id)}
      <button
        class="role-tile"
        class:is-captain={role.id === 'captain'}
        class:is-picking={pickingId === role.id}
        data-nav={pickingId ? undefined : ''}
        data-role-tile={role.id}
        aria-pressed={focusedId === role.id}
        onfocus={() => onFocus?.(role.id)}
        onclick={() => !pickingId && onSelect?.(role.id)}
      >
        <span class="role-name">{role.label}</span>
        <span class="role-icon">
          <RoleGlyph role={role.id} />
        </span>
        <span class="role-player">{playerLabel(role)}</span>
      </button>
    {/each}
  </div>
</section>
