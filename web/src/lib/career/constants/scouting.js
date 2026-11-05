export const REPORT_PAGE_SIZE = 6

export const OSK_ROWS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']
export const OSK_LIMIT = 24

export const REPORT_TABS = [
  { id: 'all', label: 'Все' },
  { id: 'requests', label: 'Отчёты по запросу' },
  { id: 'GK', label: 'Врт' },
  { id: 'DEF', label: 'Защ' },
  { id: 'MID', label: 'ПЗЩ' },
  { id: 'FWD', label: 'Нап' },
]
export const TASK_ROLES = [
  { id: '', label: 'Любая позиция' },
  { id: 'GK', label: 'Вратарь' },
  { id: 'DEF', label: 'Защитник' },
  { id: 'MID', label: 'Полузащитник' },
  { id: 'FWD', label: 'Нападающий' },
]
export const ROLE_GROUP = {
  GK: 'GK',
  CB: 'DEF',
  LB: 'DEF',
  RB: 'DEF',
  LWB: 'DEF',
  RWB: 'DEF',
  SW: 'DEF',
  DM: 'MID',
  CM: 'MID',
  LM: 'MID',
  RM: 'MID',
  AM: 'MID',
  CF: 'FWD',
  ST: 'FWD',
  LW: 'FWD',
  RW: 'FWD',
}
