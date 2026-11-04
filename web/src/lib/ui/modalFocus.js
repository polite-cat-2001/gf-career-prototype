function isEnabled(element) {
  if (element.disabled) return false
  if (element.getAttribute('aria-disabled') === 'true') return false
  if (element.closest('[inert]')) return false
  return true
}

export function trapModalFocus(layer) {
  if (!layer) return () => {}

  const previouslyFocused = document.activeElement
  const restores = []

  let node = layer
  while (node && node !== document.body && node.parentElement) {
    const parent = node.parentElement
    for (const sibling of parent.children) {
      if (sibling === node) continue
      restores.push({ element: sibling, wasInert: sibling.hasAttribute('inert') })
      sibling.setAttribute('inert', '')
    }
    node = parent
  }

  let disposed = false

  function focusTarget() {
    if (disposed || !layer.isConnected) return
    const candidates = Array.from(layer.querySelectorAll('[data-autofocus], [data-nav]')).filter(
      isEnabled,
    )
    const target =
      candidates.find((element) => element.hasAttribute('data-autofocus')) ?? candidates[0]

    if (target) {
      target.focus({ preventScroll: true })
      target.scrollIntoView({ block: 'nearest', inline: 'nearest' })
      return
    }

    if (!layer.hasAttribute('tabindex')) layer.setAttribute('tabindex', '-1')
    layer.focus({ preventScroll: true })
  }

  focusTarget()
  const frame = window.requestAnimationFrame(focusTarget)

  return () => {
    disposed = true
    window.cancelAnimationFrame(frame)
    for (let index = restores.length - 1; index >= 0; index -= 1) {
      const { element, wasInert } = restores[index]
      if (!wasInert) element.removeAttribute('inert')
    }
    if (previouslyFocused instanceof HTMLElement && previouslyFocused.isConnected) {
      previouslyFocused.focus({ preventScroll: true })
    }
  }
}
