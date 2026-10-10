// The only place with UI labels for backend statuses (enums in backend/app/models.py).
export const documentStatusLabel: Record<string, string> = {
  queued: "В очереди",
  preprocessing: "Подготовка файла",
  recognizing: "Распознавание текста",
  extracting: "Извлечение данных",
  validating: "Проверка",
  done: "Готово",
  needs_review: "Требует проверки",
  unreadable: "Не читается",
  failed: "Ошибка разбора",
};

export const applicationStatusLabel: Record<string, string> = {
  draft: "Черновик",
  processing: "Обрабатывается",
  ready: "Готова к рассмотрению",
  needs_review: "Требует внимания",
  accepted: "Принята",
  rejected: "Отклонена",
};
