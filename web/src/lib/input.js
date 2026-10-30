import { writable } from 'svelte/store'

import { triggerBack, triggerCycle, triggerDetails, triggerPrimary, triggerSave, triggerTab } from './actions.js'

export const inputDevice = writable('keyboard')

const NAV_SELECTOR = '[data-nav]:not([disabled])'
const DIRECTIONS = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']
const DEFENDER_ROLES = new Set(['CB', 'LB', 'RB', 'LWB', 'RWB', 'SW'])

let initialized = false
let pollTimer = null
let lastDirection = ''
let lastMoveAt = 0
let lastRightStick = ''
let lastRightStickAt = 0
let previousButtons = []

function visible(element) {
  if (!element || element.offsetParent === null) return false
  return element.getBoundingClientRect().width > 0
}

function navItems() {
  return Array.from(document.querySelectorAll(NAV_SELECTOR)).filter(
    (element) => visible(element) && !element.closest('[inert]'),
  )
}

export function focusFirst() {
  const items = navItems()
  const preferred = items.find((element) => element.hasAttribute('data-autofocus'))
  const target = preferred || items[0]
  if (target) {
    target.focus({ preventScroll: true })
    target.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }
}

export function focusElement(element) {
  if (!element) return
  element.focus({ preventScroll: true })
  element.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

function isTyping() {
  const element = document.activeElement
  if (!element) return false
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)
}

function cycle(direction) {
  triggerCycle(direction)
}

function moveWithinPitch(current, direction) {
  if (direction !== 'down') return false
  const pitch = current.closest('.pitch-plan-large')
  if (!pitch) return false
  const cards = Array.from(pitch.querySelectorAll(NAV_SELECTOR)).filter(visible)
  const rect = current.getBoundingClientRect()
  const centreX = rect.left + rect.width / 2
  const centreY = rect.top + rect.height / 2

  if (DEFENDER_ROLES.has(current.dataset.role)) {
    const keeper = cards.find((element) => {
      if (element.dataset.role !== 'GK') return false
      const other = element.getBoundingClientRect()
      return other.top + other.height / 2 > centreY + 10
    })
    if (keeper) {
      keeper.focus({ preventScroll: true })
      keeper.scrollIntoView({ block: 'nearest', inline: 'nearest' })
      return true
    }
  }

  let best = null
  let bestScore = Infinity
  for (const element of cards) {
    if (element === current) continue
    const other = element.getBoundingClientRect()
    const dx = other.left + other.width / 2 - centreX
    const dy = other.top + other.height / 2 - centreY
    if (dy <= 10) continue
    const score = dy + Math.abs(dx) * 1.8
    if (score < bestScore) {
      bestScore = score
      best = element
    }
  }

  if (!best) return false
  best.focus({ preventScroll: true })
  best.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  return true
}

function moveWithinActions(current, direction) {
  const panel = current.closest('.squad-actions')
  if (!panel) return false
  const items = Array.from(panel.querySelectorAll(NAV_SELECTOR)).filter(visible)
  if (!items.length) return true
  const rect = current.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  let best = null
  let bestScore = Infinity
  for (const item of items) {
    if (item === current) continue
    const other = item.getBoundingClientRect()
    const dx = other.left + other.width / 2 - cx
    const dy = other.top + other.height / 2 - cy
    let forward = 0
    let sideways = 0
    if (direction === 'right') {
      forward = dx
      sideways = Math.abs(dy)
    } else if (direction === 'left') {
      forward = -dx
      sideways = Math.abs(dy)
    } else if (direction === 'down') {
      forward = dy
      sideways = Math.abs(dx)
    } else {
      forward = -dy
      sideways = Math.abs(dx)
    }
    if (forward <= 8) continue
    const weight = direction === 'left' || direction === 'right' ? 4 : 1.8
    const score = forward + sideways * weight
    if (score < bestScore) {
      bestScore = score
      best = item
    }
  }
  if (best) {
    best.focus({ preventScroll: true })
    best.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }
  return true
}

function moveToBenchFromPitch(current, direction) {
  if (direction !== 'down') return false
  const pitch = current.closest('.pitch-plan-large')
  if (!pitch) return false
  const cards = Array.from(pitch.querySelectorAll(NAV_SELECTOR)).filter(visible)
  const rect = current.getBoundingClientRect()
  const centreY = rect.top + rect.height / 2
  const hasCardBelow = cards.some((element) => {
    if (element === current) return false
    const other = element.getBoundingClientRect()
    return other.top + other.height / 2 > centreY + 10
  })
  if (hasCardBelow) return false
  const bench = document.querySelector('[data-nav-grid]')
  const first = bench?.querySelector(NAV_SELECTOR)
  if (!first) return false
  first.focus({ preventScroll: true })
  first.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  return true
}

function focusGridItem(item) {
  item.focus({ preventScroll: true })
  item.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

function cycleSquadCentrePages(current, direction) {
  if (direction !== 'left' && direction !== 'right') return false
  if (current.closest('.squad-actions')) return false
  const centre = current.closest('.centre')
  if (!centre || !centre.querySelector('.centre-pager')) return false
  if (!current.closest('.centre-list')) return false
  cycle(direction)
  return true
}

function moveGridFocus(current, direction) {
  const region = current.closest('[data-nav-grid]')
  const grid = current.closest('.bench-grid')
  if (!region || !grid) return false
  const grids = Array.from(region.querySelectorAll('.bench-grid'))
  const gridIndex = grids.indexOf(grid)
  const items = Array.from(grid.querySelectorAll(NAV_SELECTOR)).filter(visible)
  const index = items.indexOf(current)
  if (index === -1) return false
  const columns = getComputedStyle(grid)
    .gridTemplateColumns.split(' ')
    .filter(Boolean).length

  if (direction === 'left' || direction === 'right') {
    const target = items[index + (direction === 'right' ? 1 : -1)]
    if (!target) return true
    focusGridItem(target)
    return true
  }

  const targetIndex = index + (direction === 'down' ? columns : -columns)
  if (targetIndex >= 0 && targetIndex < items.length) {
    focusGridItem(items[targetIndex])
    return true
  }

  if (direction === 'down' && targetIndex >= items.length) {
    const nextGrid = grids[gridIndex + 1]
    const first = nextGrid?.querySelector(NAV_SELECTOR)
    if (first) {
      focusGridItem(first)
      return true
    }
    return true
  }

  if (direction === 'up' && targetIndex < 0) {
    const previousGrid = grids[gridIndex - 1]
    if (!previousGrid) return false
    const previousItems = Array.from(previousGrid.querySelectorAll(NAV_SELECTOR)).filter(visible)
    const column = index % columns
    const lastRowStart = Math.max(
      0,
      previousItems.length - (previousItems.length % columns || columns),
    )
    const target = previousItems[lastRowStart + column] || previousItems[previousItems.length - 1]
    if (!target) return false
    focusGridItem(target)
    return true
  }

  return true
}

export function moveFocus(direction) {
  const items = navItems()
  if (!items.length) return
  const current = document.activeElement
  if (!items.includes(current)) {
    focusFirst()
    return
  }

  if (
    current.hasAttribute('data-amount') &&
    (direction === 'up' || direction === 'down')
  ) {
    cycle(direction)
    return
  }

  if (current.dataset.cycle && (direction === 'left' || direction === 'right')) {
    cycle(direction)
    return
  }

  if (moveWithinPitch(current, direction)) return
  if (moveToBenchFromPitch(current, direction)) return
  if (moveWithinActions(current, direction)) return
  if (moveGridFocus(current, direction)) return

  const currentRect = current.getBoundingClientRect()
  const cx = currentRect.left + currentRect.width / 2
  const cy = currentRect.top + currentRect.height / 2

  let best = null
  let bestScore = Infinity
  for (const item of items) {
    if (item === current) continue
    const rect = item.getBoundingClientRect()
    const x = rect.left + rect.width / 2
    const y = rect.top + rect.height / 2
    const dx = x - cx
    const dy = y - cy

    let forward = 0
    let sideways = 0
    if (direction === 'right') {
      forward = dx
      sideways = Math.abs(dy)
    } else if (direction === 'left') {
      forward = -dx
      sideways = Math.abs(dy)
    } else if (direction === 'down') {
      forward = dy
      sideways = Math.abs(dx)
    } else {
      forward = -dy
      sideways = Math.abs(dx)
    }

    if (forward <= 8) continue
    const sidewaysWeight = direction === 'left' || direction === 'right' ? 4 : 1.8
    const score = forward + sideways * sidewaysWeight
    if (score < bestScore) {
      bestScore = score
      best = item
    }
  }

  if (best) {
    best.focus({ preventScroll: true })
    best.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }
}

export function activateFocused() {
  const element = document.activeElement
  if (!element || !element.matches(NAV_SELECTOR)) return
  if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
    return
  }
  element.click()
}

function goBack() {
  triggerBack()
}

function switchTab(direction) {
  triggerTab(direction)
}

function saveShortcut() {
  triggerSave()
}

function detailsShortcut() {
  triggerDetails()
}

function onKeyDown(event) {
  inputDevice.set('keyboard')
  if (event.key === 'Escape') {
    event.preventDefault()
    goBack()
    return
  }
  if (isTyping()) return
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (!triggerPrimary()) activateFocused()
    return
  }
  if (DIRECTIONS.includes(event.key)) {
    event.preventDefault()
    const map = {
      ArrowUp: 'up',
      ArrowDown: 'down',
      ArrowLeft: 'left',
      ArrowRight: 'right',
    }
    const direction = map[event.key]
    if (
      (direction === 'left' || direction === 'right') &&
      cycleSquadCentrePages(document.activeElement, direction)
    ) {
      return
    }
    moveFocus(direction)
    return
  }
  if (event.code === 'KeyQ') {
    event.preventDefault()
    switchTab('left')
    return
  }
  if (event.code === 'KeyE') {
    event.preventDefault()
    switchTab('right')
    return
  }
  if (event.code === 'KeyS') {
    event.preventDefault()
    saveShortcut()
    return
  }
  if (event.code === 'KeyR') {
    event.preventDefault()
    detailsShortcut()
  }
}

function onPointerDown() {
  inputDevice.set('keyboard')
}

function onPointerMove() {
  inputDevice.set('keyboard')
}

function onPointerOver(event) {
  inputDevice.set('keyboard')
  const element = event.target.closest?.(NAV_SELECTOR)
  if (element && element !== document.activeElement) {
    element.focus({ preventScroll: true })
  }
}

function pollGamepad() {
  if (!navigator.getGamepads) return
  const pads = Array.from(navigator.getGamepads()).filter(Boolean)
  if (!pads.length) return

  const now = performance.now()
  for (const pad of pads) {
    const axisX = pad.axes[0] ?? 0
    const axisY = pad.axes[1] ?? 0
    const rightX = pad.axes[2] ?? 0
    const pressed = pad.buttons.map((button) => button.pressed)

    let direction = ''
    if (pressed[12] || axisY < -0.55) direction = 'up'
    else if (pressed[13] || axisY > 0.55) direction = 'down'
    else if (pressed[14] || axisX < -0.55) direction = 'left'
    else if (pressed[15] || axisX > 0.55) direction = 'right'

    if (direction) {
      inputDevice.set('gamepad')
      if (direction !== lastDirection || now - lastMoveAt > 190) {
        lastDirection = direction
        lastMoveAt = now
        moveFocus(direction)
      }
    } else {
      lastDirection = ''
    }

    if (Math.abs(rightX) > 0.55) {
      inputDevice.set('gamepad')
      const pageDirection = rightX > 0 ? 'right' : 'left'
      if (pageDirection !== lastRightStick || now - lastRightStickAt > 190) {
        lastRightStick = pageDirection
        lastRightStickAt = now
        cycleSquadCentrePages(document.activeElement, pageDirection)
      }
    } else {
      lastRightStick = ''
    }

    const was = previousButtons[pad.index] || []
    const down = (index) => pressed[index] && !was[index]
    if (pressed.some(Boolean) || direction) inputDevice.set('gamepad')
    if (down(0)) {
      if (!triggerPrimary()) activateFocused()
    }
    if (down(1)) goBack()
    if (down(4)) switchTab('left')
    if (down(5)) switchTab('right')
    if (down(9)) saveShortcut()
    if (down(3)) detailsShortcut()
    previousButtons[pad.index] = pressed
  }
}

export function initInput() {
  if (initialized) return () => {}
  initialized = true
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('pointerdown', onPointerDown)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerover', onPointerOver)
  window.addEventListener('gamepadconnected', () => inputDevice.set('gamepad'))
  pollTimer = window.setInterval(pollGamepad, 45)
  return () => {
    initialized = false
    window.removeEventListener('keydown', onKeyDown)
    window.removeEventListener('pointerdown', onPointerDown)
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerover', onPointerOver)
    window.clearInterval(pollTimer)
  }
}
