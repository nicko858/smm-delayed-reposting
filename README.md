# smm-delayed-reposting
## Описание функционала
Утилита предназначена для автоматического, отложенного постинга в социальные сети: `vk.com`, `facebook`, `telegram`.
В качестве расписания публикаций, используется сервис [google-spreadsheets](https://docs.google.com/spreadsheets/).

## Установка
Python3 должен быть установлен

```
$ git clone https://github.com/nicko858/smm-delayed-reposting.git
$ cd smm-delayed-reposting
$ pip install -r requirements.txt
```

## Необходимые настройки

- Создайте файл `.env` в корневой директории скрипта 
- Выполните инструкции `VK instructions`, `Telegram instructions` и `Facebook instructions` из [этого](https://github.com/nicko858/smm-reposting) репозитория
- Создайте аккаунт в `google.com` или используйте существующий
- Настройте подключение к `google-sheets` следуя [этой](https://developers.google.com/sheets/api/quickstart/python) инструкции
- Настройте подключение к `google-drive` следуя [этой](https://gsuitedevs.github.io/PyDrive/docs/build/html/quickstart.html#authentication) инструкции
- Создайте расписание в виде excel-листа [следующего вида](https://docs.google.com/spreadsheets/d/1HbSI6IFkc2GK3MBwZCRxMHrhCOxzMxVG11203KK9Sx4)
- Запомните `sheet_id` из ссылки
- Добавьте следующую запись в ваш файл `.env`:
  
  ```
  # google_env
  POST_SHEDULLER_SHEET_ID=<your post_sheduller_sheet_id>
  ```
## Как запускать

```python delayed_reposting.py```


## Цели проекта
Код написан в учебных целях в рамках онлайн-курса для веб-разработчиков [dvmn.org](https://dvmn.org).