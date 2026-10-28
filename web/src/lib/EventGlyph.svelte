<script>
  let { type = 'goal', size = 15 } = $props()

  const icons = {
    goal: '<circle cx="12" cy="12" r="8"></circle><path d="M12 7l3.4 2.5-1.3 4H9.9L8.6 9.5z M12 4v3 M19.3 9.5l-2.8 2 M16.4 18l-1-4 M7.6 18l1-4 M4.7 9.5l2.8 2"></path>',
    penalty: '<circle cx="12" cy="12" r="8"></circle><path d="M9.5 8h3a2 2 0 0 1 0 4h-3z M9.5 12v4"></path>',
    yellow: '<rect x="7" y="4" width="10" height="16" rx="1.5" fill="currentColor" stroke="none"></rect>',
    red: '<rect x="7" y="4" width="10" height="16" rx="1.5" fill="currentColor" stroke="none"></rect>',
    'sub-in': '<path d="M12 19V5"></path><path d="M7 10l5-5 5 5"></path>',
    'sub-out': '<path d="M12 5v14"></path><path d="M7 14l5 5 5-5"></path>',
    injury: '<path d="M9 4h6v5h5v6h-5v5H9v-5H4V9h5z"></path>',
  }
</script>

<svg
  class="event-glyph is-{type}"
  viewBox="0 0 24 24"
  width={size}
  height={size}
  fill="none"
  stroke="currentColor"
  stroke-width="1.5"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
>
  {@html icons[type] || icons.goal}
</svg>
