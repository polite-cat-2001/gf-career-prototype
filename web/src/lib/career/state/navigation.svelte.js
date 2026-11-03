import { tick } from 'svelte'

import { detailPages, tabs } from '../constants/hub.js'

export function createNavigationState(ctx) {
  const {
    getCareer,
    getNextMatch,
    getSeason,
    getOwnRow,
    getPlaying,
    getSaving,
    getCentreAction,
    match,
    squad,
    transfers,
    onexit,
    onsave,
    focusFirst,
  } = ctx

    const enabledTabs = tabs.filter((tab) => !tab.disabled).map((tab) => tab.id)
  
    let tab = $state('centre')
    let view = $state('overview')
    let detailsPage = $state(0)
    let hints = $derived.by(() => {
      const start = { gamepad: ['Start'], keyboard: ['S'], label: 'Сохранить' }
      const sections = { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Разделы' }
      if (match.matchdayOpen) {
        return match.matchdayStep === 'results'
          ? [
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Таблица' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'В хаб' },
            ]
          : [
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Продолжить' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'К результатам' },
            ]
      }
      if (match.matchSimOpen) {
        if (match.matchSimPhase === 'live') {
          return [
            {
              gamepad: ['Y'],
              keyboard: ['R'],
              label: match.matchSimLoading ? 'Симуляция…' : 'Пропустить',
            },
          ]
        }
        if (match.matchSimPhase === 'done') {
          return [{ gamepad: ['A'], keyboard: ['Enter'], label: 'Далее' }]
        }
        return [
          {
            gamepad: ['A'],
            keyboard: ['Enter'],
            label: match.matchSimLoading ? 'Загрузка…' : 'Начать симуляцию',
          },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (match.seasonReview) {
        return [
          {
            gamepad: ['A'],
            keyboard: ['Enter'],
            label: match.reviewStep === 0 ? 'Далее' : 'Начать новый сезон',
          },
          {
            gamepad: ['B'],
            keyboard: ['Esc'],
            label: match.reviewStep === 1 ? 'К таблице' : 'Закрыть',
          },
        ]
      }
      if (match.simulating || match.advancing) {
        return [{ gamepad: ['A'], keyboard: ['Enter'], label: getCentreAction() }]
      }
      if (tab === 'transfers') {
        if (transfers.transfersView === 'incomingCounter') {
          return [
            { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
            { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Отправить' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'contractAmount') {
          return [
            { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
            { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'contract') {
          if (transfers.transferContractState?.status === 'pending') {
            return [
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Вернуться' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            ]
          }
          if (transfers.transferContractState?.status === 'accepted') {
            return [
              {
                gamepad: ['A'],
                keyboard: ['Enter'],
                label:
                  transfers.transferContractState.affordable === false
                    ? 'Недостаточно средств'
                    : 'Подписать',
              },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            ]
          }
          return [
            { gamepad: ['D-pad'], keyboard: ['↑', '↓'], label: 'Условие' },
            { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Изменить' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'offerAmount') {
          return [
            { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
            { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'offer') {
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Условие' },
            { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Изменить' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'network') {
          return transfers.networkHints
        }
        if (transfers.transfersView === 'history') {
          return transfers.historyHints
        }
        if (transfers.scoutPickerOpen) {
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Скаут' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Поручить' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.oskOpen) {
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Буква' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Ввод' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'hub') {
          return [
            sections,
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Открыть' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'В меню' },
          ]
        }
        if (transfers.transfersView === 'filters') {
          if (transfers.transferEditing) {
            return [
              { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Значение' },
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Готово' },
            ]
          }
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Фильтр' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Изменить' },
            { gamepad: ['X'], keyboard: ['X'], label: 'Сброс' },
            { gamepad: ['Y'], keyboard: ['Y'], label: 'Начать поиск' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        if (transfers.transfersView === 'centre') {
          if (transfers.incomingOfferModalId) {
            const offer = transfers.incomingOfferModal
            const hasAction =
              offer && ['pending'].includes(offer.status)
            if (!hasAction) {
              return [{ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' }]
            }
            return [
              { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            ]
          }
          if (transfers.transferOfferModalId) {
            const offer = transfers.transferOfferModal
            const hasAction =
              offer &&
              offer.status !== 'pending' &&
              !offer.signed &&
              !(offer.status === 'refused' && !offer.can_offer_again)
            if (!hasAction) {
              return [{ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' }]
            }
            return [
              { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            ]
          }
          if (transfers.transferCentreActionsOpen) {
            return [
              { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            ]
          }
          const list = [
            { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Вкладки' },
          ]
          if (transfers.transferCentreIsSent || transfers.transferCentreTab === 'received') {
            list.push({ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' })
            list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' })
          } else if (transfers.transferCentreIsList) {
            list.push({ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' })
            list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' })
            list.push({ gamepad: ['Y'], keyboard: ['Y'], label: 'Вид' })
          }
          list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
          return list
        }
        if (transfers.transfersView === 'results') {
          if (transfers.transferSearchActionsOpen) {
            return [
              { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Действие' },
              { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбор' },
              { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            ]
          }
          return [
            { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
            { gamepad: ['Y'], keyboard: ['Y'], label: 'Вид' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          ]
        }
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (tab === 'squad' && view === 'amount') {
        return [
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Разряд' },
          { gamepad: ['↑', '↓'], keyboard: ['↑', '↓'], label: 'Цифра' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Готово' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (tab === 'squad' && view === 'negotiation') {
        if (squad.negotiationState?.status === 'pending') {
          return [
            { gamepad: ['A'], keyboard: ['Enter'], label: 'Вернуться' },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            start,
          ]
        }
        if (squad.negotiationState?.status === 'accepted') {
          return [
            {
              gamepad: ['A'],
              keyboard: ['Enter'],
              label:
                squad.negotiationState.affordable === false
                  ? 'Недостаточно средств'
                  : 'Подписать',
            },
            { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
            start,
          ]
        }
        return [
          { gamepad: ['D-pad'], keyboard: ['↑', '↓'], label: 'Условие' },
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Значение' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Выбрать' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
          start,
        ]
      }
      if (tab === 'squad' && view === 'number') {
        return [
          { gamepad: ['←', '→'], keyboard: ['←', '→'], label: 'Номер' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Сохранить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' },
        ]
      }
      if (tab === 'squad' && view === 'release') {
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Выбор' },
          { gamepad: ['A'], keyboard: ['Enter'], label: 'Подтвердить' },
          { gamepad: ['B'], keyboard: ['Esc'], label: 'Отмена' },
        ]
      }
      if (tab === 'squad' && view === 'centre') {
        const list = [{ gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' }]
        if (squad.centreOpenId) {
          list[0].label = 'Пункт'
          list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'Действие' })
          list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Закрыть' })
          list.push(start)
          return list
        }
        if (squad.centreTab === 'attributes') {
          list.push({
            gamepad: ['R-stick'],
            keyboard: ['←', '→'],
            label: 'Страницы',
          })
        }
        list.push({ gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Вкладки' })
        list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
        list.push(start)
        return list
      }
      if (tab === 'squad' && view === 'details') {
        return [
          { gamepad: ['B'], keyboard: ['Esc'], label: 'К полю' },
          { gamepad: ['Y'], keyboard: ['R'], label: 'План игры' },
          { gamepad: ['L1', 'R1'], keyboard: ['Q', 'E'], label: 'Страницы' },
          start,
        ]
      }
      if (tab === 'squad' && view === 'plan') {
        return [
          { gamepad: ['D-pad'], keyboard: ['Стрелки'], label: 'Игрок' },
          squad.comparing
            ? { gamepad: ['A'], keyboard: ['Enter'], label: squad.canSwap ? 'Обменять' : 'Просмотр' }
            : { gamepad: ['A'], keyboard: ['Enter'], label: 'Сравнить' },
          { gamepad: ['Y'], keyboard: ['R'], label: 'Подробности' },
          { gamepad: ['B'], keyboard: ['Esc'], label: squad.comparing ? 'Отменить' : 'Назад' },
          start,
        ]
      }
      const list = [sections]
      if (tab === 'centre') {
        list.push({
          gamepad: ['A'],
          keyboard: ['Enter'],
          label: match.isMatchDay ? 'Выбрать' : getCentreAction(),
        })
        list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'В меню' })
      } else {
        list.push({ gamepad: ['A'], keyboard: ['Enter'], label: 'План игры' })
        list.push({ gamepad: ['B'], keyboard: ['Esc'], label: 'Назад' })
      }
      list.push(start)
      return list
    })
  
    function handleSave() {
      if (
        !getSaving() &&
        !match.seasonReview &&
        !match.simulating &&
        !match.advancing &&
        !match.matchSimOpen &&
        !match.matchdayOpen
      ) {
        onsave()
      }
    }
  
    function handleStep(direction) {
      if (tab !== 'transfers' || transfers.transfersView !== 'filters') return false
      if (transfers.oskOpen || !transfers.transferEditing) return false
      if (transfers.transferEditing === 'age') {
        if (direction === 'up' || direction === 'down') {
          transfers.transferAgeRow = transfers.transferAgeRow === 'ageMin' ? 'ageMax' : 'ageMin'
        } else {
          transfers.stepActive(direction === 'right' ? 1 : -1)
        }
        return true
      }
      if (transfers.transferEditing === 'positionRole') {
        if (direction === 'up' || direction === 'down') {
          transfers.transferRoleRow = transfers.transferRoleRow === 'group' ? 'position' : 'group'
            } else {
          transfers.stepActive(direction === 'right' ? 1 : -1)
        }
        return true
      }
      if (direction === 'left' || direction === 'right') transfers.stepActive(direction === 'right' ? 1 : -1)
      return true
    }
  
    function handleViewToggle() {
      if (tab !== 'transfers' || transfers.oskOpen) return false
      if (transfers.transfersView === 'filters') {
        transfers.startTransferSearch()
        return true
      }
      if (transfers.transfersView === 'results') {
        if (transfers.transferSearchActionsOpen) return true
        transfers.transferResultView = transfers.transferResultView === 'grid' ? 'list' : 'grid'
        return true
      }
      if (transfers.transfersView === 'centre') {
        if (
          transfers.transferCentreActionsOpen ||
          transfers.transferCentreIsOffer ||
          transfers.transferCentreIsSent
        ) {
          return true
        }
        transfers.transferCentreView = transfers.transferCentreView === 'grid' ? 'list' : 'grid'
        return true
      }
      return false
    }
  
    function handleReset() {
      if (tab !== 'transfers' || transfers.transfersView !== 'filters' || transfers.oskOpen) return false
      transfers.transferEditing = null
      transfers.resetTransferFilters()
      return true
    }
  
    function handleBack() {
      if (tab === 'transfers' && transfers.transfersView === 'incomingCounter') {
        transfers.closeIncomingCounter()
        return
      }
      if (tab === 'transfers' && transfers.incomingOfferModalId) {
        transfers.closeIncomingOfferModal()
        return
      }
      if (tab === 'transfers' && transfers.transfersView === 'contractAmount') {
        transfers.closeTransferContractAmount()
        return
      }
      if (tab === 'transfers' && transfers.transfersView === 'contract') {
        transfers.closeTransferContract()
        return
      }
      if (tab === 'transfers' && transfers.transfersView === 'offerAmount') {
        transfers.closeOfferAmount()
        return
      }
      if (tab === 'transfers' && transfers.transfersView === 'offer') {
        transfers.closeTransferOffer()
        return
      }
      if (tab === 'transfers' && transfers.transferOfferModalId) {
        transfers.closeSentOfferModal()
        return
      }
      if (tab === 'squad' && view === 'amount') {
        squad.closeAmountScreen()
        return
      }
      if (tab === 'squad' && view === 'negotiation') {
        squad.closeNegotiationScreen()
        return
      }
      if (tab === 'squad' && view === 'number') {
        squad.closeNumberScreen()
        return
      }
      if (tab === 'squad' && view === 'release') {
        squad.closeReleaseScreen()
        return
      }
      if (match.matchdayOpen) {
        if (match.matchdayStep === 'table') {
          match.matchdayStep = 'results'
        } else {
          match.closeMatchday()
        }
        return
      }
      if (match.matchSimOpen) {
        if (match.matchSimLoading || match.matchSimPhase !== 'setup') return
        match.closeMatchSimulation()
        return
      }
      if (match.simulating) {
        match.stopSimulation()
        return
      }
      if (match.advancing) return
      if (match.seasonReview) {
        if (match.reviewStep === 1) {
          match.reviewStep = 0
          tick().then(focusFirst)
        } else {
          match.closeSeasonReview()
        }
        return
      }
      if (tab === 'transfers') {
        if (transfers.scoutPickerOpen) {
          transfers.closeScoutPicker()
          return
        }
        if (transfers.transfersView === 'network') {
          transfers.closeTransferNetwork()
          return
        }
        if (transfers.transfersView === 'centre' && transfers.transferCentreActionsOpen) {
          transfers.transferCentreActionsOpen = false
          return
        }
        if (transfers.transfersView === 'results' && transfers.transferSearchActionsOpen) {
          transfers.transferSearchActionsOpen = false
          return
        }
        transfers.openTransferHub()
        return
      }
      if (tab === 'squad') {
        if (view === 'centre') {
          if (squad.centreOpenId) {
            squad.closeCentreActions()
            return
          }
          backToOverview()
          return
        }
        if (view === 'details') {
          closeDetails()
          return
        }
        if (view === 'plan') {
          if (squad.anchorId) {
            const anchor = squad.anchorId
            squad.anchorId = null
            tick().then(() => squad.focusPlayer(anchor))
            return
          }
          backToOverview()
          return
        }
        setTab('centre')
        return
      }
      if (tab !== 'centre') {
        setTab('centre')
        return
      }
      onexit()
    }
  
    function closeDetails() {
      view = 'plan'
      tick().then(() => squad.focusPlayer(squad.focusPlayerId))
    }
  
    function handlePrimaryAction() {
      if (tab === 'squad' && view === 'number') {
        squad.confirmNumber()
        return true
      }
      if (match.matchdayOpen) {
        match.advanceMatchday()
        return true
      }
      if (!match.matchSimOpen) return false
      match.activateMatchSimulation()
      return true
    }
  
    function handleDetails() {
      if (match.matchdayOpen) return
      if (match.matchSimOpen) {
        if (match.matchSimPhase === 'live') match.finishMatchSimulation()
        return
      }
      if (tab === 'squad' && view === 'centre') return
      toggleDetails()
    }
  
    function toggleDetails() {
      if (match.matchdayOpen || match.seasonReview) return
      if (tab !== 'squad' || !squad.focusedPlayer) return
      if (view === 'centre') return
      if (view === 'details') {
        closeDetails()
        return
      }
      if (view === 'plan') {
        squad.anchorId = null
        squad.benchFocused = false
        detailsPage = 0
        view = 'details'
        tick().then(() => {
          document.querySelector('.details-panel')?.focus({ preventScroll: true })
        })
      }
    }
  
    async function backToOverview() {
      view = 'overview'
      squad.anchorId = null
      squad.benchFocused = false
      squad.focusPlayerId = null
      squad.centreOpenId = null
      await tick()
      focusFirst()
    }
  
    async function setTab(next) {
      if (match.simulating || match.advancing || match.matchSimOpen || match.matchdayOpen) return
      if (!enabledTabs.includes(next)) return
      tab = next
      view = 'overview'
      squad.anchorId = null
      squad.benchFocused = false
      squad.focusPlayerId = null
      squad.centrePlayerId = null
      squad.centreOpenId = null
      squad.centreTab = 'status'
      transfers.transfersView = 'hub'
      transfers.networkMode = 'scouts'
      transfers.networkEntryId = null
      transfers.networkBackToHub = false
      transfers.networkHints = []
      transfers.scoutPickerOpen = false
      transfers.scoutPickerPlayer = null
      transfers.transferEditing = null
      transfers.transferOffer = null
      transfers.transferOfferPlayer = null
      transfers.oskOpen = false
      transfers.transferResults = []
      transfers.transferTotal = 0
      transfers.transferSearchSelectedId = null
      transfers.transferSearchActionsOpen = false
      transfers.transferCentreTab = 'shortlist'
      transfers.transferCentreSelectedId = null
      transfers.transferCentreActionsOpen = false
      transfers.transferOfferModalId = null
      transfers.incomingOfferModalId = null
      transfers.incomingCounterOffer = null
      transfers.incomingCounterPlayer = null
      transfers.transferError = ''
      await tick()
      focusFirst()
    }
  
    function switchTab(direction) {
      if (tab === 'transfers' && transfers.transfersView !== 'hub') {
        if (
          transfers.transfersView === 'centre' &&
          !transfers.transferCentreActionsOpen &&
          !transfers.scoutPickerOpen &&
          !transfers.transferOfferModalId &&
          !transfers.incomingOfferModalId
        ) {
          transfers.switchTransferCentreTab(direction)
        }
        return
      }
      if (tab === 'squad' && ['negotiation', 'amount', 'number', 'release'].includes(view)) return
      if (transfers.transferEditing || transfers.oskOpen) return
      if (match.simulating || match.advancing || match.seasonReview || match.matchSimOpen || match.matchdayOpen) return
      if (tab === 'squad' && view === 'centre') {
        squad.switchCentreTab(direction)
        return
      }
      if (tab === 'squad' && view === 'details') {
        switchDetailsPage(direction)
        return
      }
      const index = enabledTabs.indexOf(tab)
      const offset = direction === 'right' ? 1 : -1
      const next = enabledTabs[(index + offset + enabledTabs.length) % enabledTabs.length]
      setTab(next)
    }
  
    function switchDetailsPage(direction) {
      const offset = direction === 'right' ? 1 : -1
      detailsPage = (detailsPage + offset + detailPages.length) % detailPages.length
    }
  
    function handleCycle(direction) {
      if (tab === 'transfers') {
        if (transfers.transfersView === 'incomingCounter') {
          squad.adjustAmount(direction)
          return
        }
        if (transfers.transfersView === 'contractAmount') {
          squad.adjustAmount(direction)
          return
        }
        if (transfers.transfersView === 'contract') {
          const field = document.activeElement?.dataset?.field
          if (field) transfers.adjustTransferContractField(field, direction === 'right' ? 1 : -1)
          return
        }
        if (transfers.transfersView === 'offerAmount') {
          squad.adjustAmount(direction)
          return
        }
        if (transfers.transfersView === 'offer') {
          const field = document.activeElement?.dataset?.field
          if (field === 'buyout') {
            if (direction === 'left' || direction === 'right') transfers.toggleOfferBuyout()
            return
          }
          if (field) transfers.adjustOfferField(field, direction === 'right' ? 1 : -1)
          return
        }
        if (transfers.transfersView === 'hub' && transfers.reportFeed.length) {
          transfers.shiftReport(direction)
          return
        }
        if (transfers.transfersView === 'filters' && !transfers.oskOpen) {
          handleStep(direction === 'right' ? 'right' : 'left')
        }
        return
      }
      if (tab === 'squad' && view === 'number') {
        squad.cycleNumber(direction)
        return
      }
      if (tab === 'squad' && view === 'amount') {
        squad.adjustAmount(direction)
        return
      }
      const field = document.activeElement?.dataset?.field
      if (tab === 'squad' && view === 'negotiation' && field) {
        squad.adjustNegotiationField(field, direction === 'right' ? 1 : -1)
        return
      }
      if (tab !== 'squad' || view !== 'centre' || squad.centreTab !== 'attributes') return
      squad.shiftAttributePage(direction === 'right' ? 1 : -1)
    }
  



  return {
    get tab() {
      return tab
    },
    set tab(value) {
      tab = value
    },
    get view() {
      return view
    },
    set view(value) {
      view = value
    },
    get detailsPage() {
      return detailsPage
    },
    set detailsPage(value) {
      detailsPage = value
    },
    get hints() {
      return hints
    },
    handleSave,
    handleStep,
    handleViewToggle,
    handleReset,
    handleBack,
    closeDetails,
    handlePrimaryAction,
    handleDetails,
    toggleDetails,
    backToOverview,
    setTab,
    switchTab,
    switchDetailsPage,
    handleCycle,
  }
}
