let backHandler = null
let tabHandler = null
let saveHandler = null
let cycleHandler = null
let detailsHandler = null

export function registerBack(handler) {
  backHandler = handler
  return () => {
    if (backHandler === handler) backHandler = null
  }
}

export function registerTabs(handler) {
  tabHandler = handler
  return () => {
    if (tabHandler === handler) tabHandler = null
  }
}

export function registerSave(handler) {
  saveHandler = handler
  return () => {
    if (saveHandler === handler) saveHandler = null
  }
}

export function registerDetails(handler) {
  detailsHandler = handler
  return () => {
    if (detailsHandler === handler) detailsHandler = null
  }
}

export function registerCycle(handler) {
  cycleHandler = handler
  return () => {
    if (cycleHandler === handler) cycleHandler = null
  }
}

export function triggerBack() {
  backHandler?.()
}

export function triggerTab(direction) {
  tabHandler?.(direction)
}

export function triggerSave() {
  saveHandler?.()
}

export function triggerDetails() {
  detailsHandler?.()
}

export function triggerCycle(direction) {
  cycleHandler?.(direction)
}
