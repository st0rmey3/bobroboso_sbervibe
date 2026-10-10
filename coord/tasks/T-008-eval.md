---
id: T-008
title: Эталонные ответы для тестовых файлов (руками) — шаг 3 из 3
owner: gemini
status: todo
prio: P1
model: human
depends:
---
## Цель
Блок «качество разбора» — 30 баллов. Чтобы честно посчитать точность, нужны правильные ответы для каждого
тестового файла. Делается руками, ИИ не нужен: смотришь на картинку — переписываешь значения.

## Шаги
1. Создать папку `data/open/` в корне проекта (она в `.gitignore`, в git не попадёт — так и надо).
2. Скопировать туда все файлы из `case_docs`.
3. Для каждого файла создать рядом JSON с тем же именем, например
   `Паспорт РФ Киселев Максим Васильевич.json`:
   ```
   {"doc_type": "passport_ru",
    "fields": {"series": "3625", "number": "921601", "full_name": "КИСЕЛЕВ МАКСИМ ВАСИЛЬЕВИЧ",
               "birth_date": "1980-07-19"}}
   ```
   Правила: даты `ГГГГ-ММ-ДД`; цифры без пробелов; ФИО как на документе.
   Коды видов и названия полей — в `backend/app/extraction/doctypes.py` (passport_ru, snils, inn, work_patent,
   driver_license_ru, driver_license_kg, passport_by, passport_in).
   Для чека и размытого фото: `{"doc_type": "unknown", "fields": {}}`.
4. Заполнять хотя бы обязательные поля (минимум из ТЗ). Остальные — по желанию.
5. Отправить папку `data/open` капитану архивом в личку (не через git).

## Шаблоны (обязательные поля по ТЗ — заполнить обязательно, остальные — если видно)
```
passport_ru:        {"doc_type": "passport_ru", "fields": {"series": "", "number": "", "full_name": "", "birth_date": "", "birth_place": "", "issued_by": "", "issue_date": ""}}
snils:              {"doc_type": "snils", "fields": {"number": "", "full_name": ""}}
inn:                {"doc_type": "inn", "fields": {"number": ""}}
work_patent (лицо): {"doc_type": "work_patent", "fields": {"series": "", "number": "", "full_name": "", "birth_date": "", "citizenship": ""}}
work_patent (обор.):{"doc_type": "work_patent", "fields": {"issue_date": "", "valid_until": "", "region": "", "blank_number": ""}}
driver_license_ru:  {"doc_type": "driver_license_ru", "fields": {"number": "", "full_name": "", "birth_date": "", "issue_date": "", "expiry_date": ""}}
driver_license_kg:  {"doc_type": "driver_license_kg", "fields": {"number": "", "full_name": "", "birth_date": "", "issue_date": "", "expiry_date": ""}}
passport_by:        {"doc_type": "passport_by", "fields": {"number": "", "full_name": "", "birth_date": "", "expiry_date": ""}}
passport_in:        {"doc_type": "passport_in", "fields": {"number": "", "full_name": "", "birth_date": "", "expiry_date": ""}}
не документ / размыто: {"doc_type": "unknown", "fields": {}}
```
Номер ВУ РФ — 10 цифр без пробелов; номер патента — цифры после «№» на лицевой стороне.

## Как работать в Aider
Быстрее руками в любом редакторе. Если всё же через Aider — по одному файлу:
```
/read backend/app/extraction/doctypes.py
/add "data/open/Паспорт РФ Киселев Максим Васильевич.json"
```
Запрос: «Создай этот JSON по шаблону passport_ru с такими значениями: серия 3625, номер 921601, …».
Значения диктуешь ты, глядя на картинку — модель их не придумывает.

## Готово, когда
- [ ] у каждого тестового файла есть JSON с ответами
- [ ] капитан прогнал `python scripts/eval_extraction.py data/open` и получил цифры точности

## Thread

## Result
