<script>
  let { name = 'pitch', size = 44 } = $props()

  const paths = {
    pitch: 'M3 5h18v14H3z M3 12h18 M12 8.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7',
    shirt: 'M8 4l4 2 4-2 4 3-2 3-1-1v10H7V9L6 10 4 7z',
    layers: 'M12 3l9 5-9 5-9-5 9-5z M3 13l9 5 9-5',
    grid: 'M4 4h7v7H4z M13 4h7v7h-7z M4 13h7v7H4z M13 13h7v7h-7z',
    users:
      'M9 11a3.5 3.5 0 1 0 0-7a3.5 3.5 0 0 0 0 7z M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6 M16 5.5a3.5 3.5 0 0 1 0 7 M18 14c2.1.7 3.5 2.7 3.5 6',
    chart: 'M5 20V11h3v9 M10.5 20V5h3v15 M16 20v-6h3v6',
    calendar: 'M4 6h16v14H4z M4 10h16 M8 3v4 M16 3v4',
    news: 'M4 5h12v14H4z M16 9h4v8a2 2 0 0 1-2 2 M7 9h6 M7 12h6 M7 15h4',
    table: 'M3 5h18v14H3z M3 10h18 M9 10v9 M15 10v9',
    clock: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 7v5l3 2',
    globe: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M3 12h18 M12 3c3 3.2 3 14.8 0 18 M12 3c-3 3.2-3 14.8 0 18',
    lock:
      'M6 11h12v9H6z M8.5 11V8a3.5 3.5 0 0 1 7 0v3 M12 15v2',
    check: 'M5 12.5l4.5 4.5L19 7'
  }
</script>

<svg
  class="icon"
  viewBox="0 0 24 24"
  width={size}
  height={size}
  fill="none"
  stroke="currentColor"
  stroke-width="1.3"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
>
  <path d={paths[name] || paths.pitch} />
</svg>
