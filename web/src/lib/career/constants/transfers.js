export const TRANSFER_PAGE = 40

export const transferHubCards = [
  {
    id: 'search',
    label: 'Искать игроков',
    note: 'Поиск особого игрока, которого вы хотите купить, взять в аренду или изучить.',
    icon: 'grid',
    enabled: true,
  },
  {
    id: 'centre',
    label: 'Центр трансферов',
    note: 'Шортлист, предложения и переговоры',
    icon: 'shirt',
    enabled: true,
  },
  {
    id: 'network',
    label: 'Всемирная сеть',
    note: 'Скауты, задачи и отчёты по всему миру',
    icon: 'globe',
    enabled: true,
  },
  {
    id: 'history',
    label: 'История',
    note: 'Все сделки, офферы и переходы',
    icon: 'news',
    enabled: true,
  },
]

export const TRANSFER_POSITIONS = [
  'Goalkeeper',
  'Sweeper',
  'Defender',
  'Centre-Back',
  'Left-Back',
  'Right-Back',
  'Defensive Midfield',
  'Central Midfield',
  'Attacking Midfield',
  'Left Midfield',
  'Right Midfield',
  'Midfielder',
  'Left Winger',
  'Right Winger',
  'Striker',
  'Centre-Forward',
  'Second Striker',
]

export const TRANSFER_GROUP_TABS = [
  { id: '', label: 'ВСЕ' },
  { id: 'FWD', label: 'НАП' },
  { id: 'MID', label: 'ПЗЩ' },
  { id: 'DEF', label: 'ЗАЩ' },
  { id: 'GK', label: 'ВРТ' },
]

export const TRANSFER_GROUP_OPTIONS = TRANSFER_GROUP_TABS.map((group) => ({
  value: group.id,
  label: group.id ? group.label : 'Любая',
}))

export const TRANSFER_STATUS_OPTIONS = [
  { value: '', label: 'Любой' },
  { value: 'free', label: 'Свободный агент' },
  { value: 'transfer', label: 'На трансфере' },
  { value: 'loan', label: 'В аренде' },
  { value: 'blocked', label: 'Заблокирован' },
]

export const TRANSFER_CENTRE_TABS = [
  { id: 'shortlist', label: 'Список' },
  { id: 'sent', label: 'Отправленные предложения' },
  { id: 'received', label: 'Полученные предложения' },
  { id: 'listed', label: 'На трансфере' },
  { id: 'loaned', label: 'На аренде' },
]

export const OFFER_STATUS_LABELS = {
  pending: 'Ожидает ответа',
  counter: 'Контрпредложение',
  accepted: 'Принято',
  refused: 'Отказ',
  withdrawn: 'Отозвано',
  expired: 'Истекло',
}

export const OFFER_KIND_LABELS = {
  transfer: 'Трансфер',
  loan: 'Аренда',
}

export const POSITION_BADGES = {
  Goalkeeper: 'ВРТ',
  Sweeper: 'СВ',
  Defender: 'ЗАЩ',
  'Centre-Back': 'ЦЗ',
  'Left-Back': 'ЛЗ',
  'Right-Back': 'ПЗ',
  'Defensive Midfield': 'ОП',
  'Central Midfield': 'ЦП',
  'Attacking Midfield': 'АП',
  'Left Midfield': 'ЛП',
  'Right Midfield': 'ПП',
  Midfielder: 'ПЗЩ',
  'Left Winger': 'ЛФА',
  'Right Winger': 'ПФА',
  Striker: 'НАП',
  'Centre-Forward': 'ФРВ',
  'Second Striker': 'ОТН',
}

export const TRANSFER_AGE = { min: 15, max: 50 }
