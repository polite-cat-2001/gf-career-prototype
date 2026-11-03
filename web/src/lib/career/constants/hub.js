export const tabs = [
  { id: 'centre', label: 'Центр' },
  { id: 'squad', label: 'Состав' },
  { id: 'transfers', label: 'Трансферы' },
  { id: 'office', label: 'Офис', disabled: true },
  { id: 'season', label: 'Сезон', disabled: true },
]

export const planTabs = [
  { label: 'Состав', active: true },
  { label: 'Схемы' },
  { label: 'Амплуа' },
  { label: 'Задачи' },
  { label: 'Тактика' },
]

export const detailPages = [
  { id: 'general', label: 'Общая информация' },
  { id: 'stats-one', label: 'Статы 1' },
  { id: 'stats-two', label: 'Статы 2' },
  { id: 'season', label: 'Сезон' },
]

export const centreTabs = [
  { id: 'status', label: 'Статус' },
  { id: 'stats', label: 'Статистика' },
  { id: 'attributes', label: 'Характеристики' },
  { id: 'finance', label: 'Финансы' },
]

export const attributePages = [
  { id: 'overview', label: 'Общая информация' },
  { id: 'mental', label: 'Ментальные' },
  { id: 'physical', label: 'Физические' },
  { id: 'technical', label: 'Технические' },
]

export const AMOUNT_PLACES = [
  'сотни миллионов',
  'десятки миллионов',
  'миллионы',
  'сотни тысяч',
  'десятки тысяч',
  'тысячи',
  'сотни',
  'десятки',
  'единицы',
]

export const INFO_LABELS = [
  { key: 'position', label: 'Амплуа' },
  { key: 'age', label: 'Возраст' },
  { key: 'height', label: 'Рост' },
  { key: 'weight', label: 'Вес' },
  { key: 'foot', label: 'Рабочая нога' },
  { key: 'weakFoot', label: 'Слабая нога' },
  { key: 'skillMoves', label: 'Финты' },
  { key: 'shirtNumber', label: 'Номер' },
  { key: 'potential', label: 'Потенциал' },
  { key: 'marketValue', label: 'Стоимость' },
  { key: 'citizenship', label: 'Гражданство' },
]

export const squadTiles = [
  { id: 'club', label: 'Состав клуба', note: 'Текущий состав на матч', selected: true },
  {
    id: 'national',
    label: 'Сборная',
    note: 'Сейчас вы не являетесь тренером сборной',
    icon: 'globe',
    disabled: true,
  },
  { id: 'centre', label: 'Центр составов', note: 'Статус, статистика и финансы', icon: 'users' },
  {
    id: 'national-squad',
    label: 'Выбор состава сборной',
    note: 'Доступно только для сборных',
    icon: 'globe',
    disabled: true,
  },
  {
    id: 'main-squads',
    label: 'Основные составы',
    note: 'Несколько составов — #4',
    icon: 'layers',
    disabled: true,
  },
  { id: 'change', label: 'Изменить игрока', note: 'Заблокировано', icon: 'lock', disabled: true },
]
