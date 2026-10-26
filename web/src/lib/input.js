import { writable } from 'svelte/store'

import { triggerBack, triggerCycle, triggerDetails, triggerSave, triggerTab } from './actions.js'

export const inputDevice = writable('keyboard')

const NAV_SELECTOR = '[data-nav]:not([disabled])'
const DIRECTIONS = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']

let initialized = false
let pollTimer = null
let lastDirection = ''
let lastMoveAt = 0
let previousButtons = []

function visible(element) {
  if (!element || element.offsetParent === null) return false
  return element.getBoundingClientRect().width > 0
}

function navItems() {
  return Array.from(document.querySelectorAll(NAV_SELECTOR)).filter(visible)
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

export function moveFocus(direction) {
  const items = navItems()
  if (!items.length) return
  const current = document.activeElement
  if (!items.includes(current)) {
    focusFirst()
    return
  }

  if (current.dataset.cycle && (direction === 'left' || direction === 'right')) {
    cycle(direction)
    return
  }

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
    const score = forward + sideways * 1.8
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
    activateFocused()
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
    moveFocus(map[event.key])
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

    const was = previousButtons[pad.index] || []
    const down = (index) => pressed[index] && !was[index]
    if (pressed.some(Boolean) || direction) inputDevice.set('gamepad')
    if (down(0)) activateFocused()
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
