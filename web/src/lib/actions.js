const backHandlers = []
const tabHandlers = []
const saveHandlers = []
const cycleHandlers = []
const detailsHandlers = []
const primaryHandlers = []
const viewHandlers = []
const stepHandlers = []
const resetHandlers = []

function register(list, handler) {
  list.push(handler)
  return () => {
    const index = list.lastIndexOf(handler)
    if (index >= 0) list.splice(index, 1)
  }
}

function latest(list) {
  return list.length ? list[list.length - 1] : null
}

export function registerBack(handler) {
  return register(backHandlers, handler)
}

export function registerTabs(handler) {
  return register(tabHandlers, handler)
}

export function registerSave(handler) {
  return register(saveHandlers, handler)
}

export function registerDetails(handler) {
  return register(detailsHandlers, handler)
}

export function registerCycle(handler) {
  return register(cycleHandlers, handler)
}

export function registerPrimary(handler) {
  return register(primaryHandlers, handler)
}

export function registerView(handler) {
  return register(viewHandlers, handler)
}

export function registerStep(handler) {
  return register(stepHandlers, handler)
}

export function registerReset(handler) {
  return register(resetHandlers, handler)
}

export function triggerBack() {
  latest(backHandlers)?.()
}

export function triggerTab(direction) {
  latest(tabHandlers)?.(direction)
}

export function triggerSave() {
  latest(saveHandlers)?.()
}

export function triggerDetails() {
  latest(detailsHandlers)?.()
}

export function triggerCycle(direction) {
  latest(cycleHandlers)?.(direction)
}

export function triggerPrimary() {
  return latest(primaryHandlers)?.() ?? false
}

export function triggerView() {
  return latest(viewHandlers)?.() ?? false
}

export function triggerStep(direction) {
  return latest(stepHandlers)?.(direction) ?? false
}

export function triggerReset() {
  return latest(resetHandlers)?.() ?? false
}
