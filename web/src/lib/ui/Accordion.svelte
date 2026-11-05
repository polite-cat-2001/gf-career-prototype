<script>
  let { open = false, onclose = null, children } = $props()

  function closeDuration(node) {
    const style = window.getComputedStyle(node)
    return Math.max(
      0,
      ...style.transitionDuration.split(',').map((value) => {
        const parsed = Number.parseFloat(value)
        if (Number.isNaN(parsed)) return 0
        return parsed * (value.trim().endsWith('ms') ? 1 : 1000)
      }),
    )
  }

  function closeOnAction(node) {
    let replaying = false

    function waitForClose() {
      return new Promise((resolve) => {
        const duration = closeDuration(node)
        if (!duration) {
          requestAnimationFrame(resolve)
          return
        }
        let settled = false
        let timer
        const finish = () => {
          if (settled) return
          settled = true
          node.removeEventListener('transitionend', onEnd)
          window.clearTimeout(timer)
          resolve()
        }
        const onEnd = (event) => {
          if (event.target === node && event.propertyName === 'grid-template-rows') finish()
        }
        timer = window.setTimeout(finish, duration + 80)
        node.addEventListener('transitionend', onEnd)
      })
    }

    async function handleClick(event) {
      if (replaying || !open) return
      const action = event.target.closest?.('button, [data-nav]')
      if (!action || action.disabled) return
      event.preventDefault()
      event.stopPropagation()
      onclose?.()
      await waitForClose()
      if (!action.isConnected) return
      replaying = true
      action.click()
      replaying = false
    }

    node.addEventListener('click', handleClick, true)
    return {
      destroy() {
        node.removeEventListener('click', handleClick, true)
      },
    }
  }
</script>

<div
  class="gf-accordion"
  class:is-open={open}
  inert={!open}
  data-nav-trap
  use:closeOnAction
>
  <div class="gf-accordion__inner">
    {@render children?.()}
  </div>
</div>
