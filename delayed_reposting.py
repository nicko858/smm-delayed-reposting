from __future__ import print_function
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError as google_http_error
from google.auth.exceptions import TransportError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import FileNotDownloadableError
import urllib.parse as urlparse
from reposting import run_reposting
import os
import os.path
from os import getenv
import glob
from datetime import datetime
import locale
import calendar
from dotenv import load_dotenv
import time


def read_article_file(article_path):
    with open(article_path, 'r') as file_handler:
        content = file_handler.read()
        return content


def get_file_id(formula_string):
    parsed_url = urlparse.urlparse(formula_string)
    file_id = ''.join(urlparse.parse_qs(parsed_url.query)['id']).replace(
        '"',
        ''
    )
    return file_id


def download_data_for_posting(
        file_id=None,
        file_type=None,
        download_dir=None
):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    downloaded_file = drive.CreateFile({'id': file_id})
    downloaded_file.FetchMetadata()

    file_metadata = {
        'img': 'originalFilename',
        'article': 'title'
    }

    file_name = downloaded_file.metadata[file_metadata[file_type]]
    file_download_path = os.path.join(download_dir, file_name)
    mimetype = ''
    if file_type == 'article':
        mimetype = 'text/plain'

    downloaded_file.GetContentFile(
        file_download_path,
        mimetype=mimetype
    )
    return file_download_path


def connect_to_google(scopes):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', scopes)
                time.sleep(1)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('sheets', 'v4', credentials=creds)
        return service
    except TransportError:
        print('Проблема с авторизацией в google!\nЗадание не будет выполнено!')
        return


def get_scheduler_data(
        service,
        post_scheduler_sheet_id,
        post_scheduler_cell_range
):
    value_render_option = 'FORMULA'
    sheet = service.spreadsheets()
    try:
        result = sheet.values().get(
            spreadsheetId=post_scheduler_sheet_id,
            range=post_scheduler_cell_range,
            valueRenderOption=value_render_option
        ).execute()
    except google_http_error:
        return
    scheduler_data = result.get('values', [])
    return scheduler_data


def unpack_sheet_range_data(scheduler_data):
    scheduler_data_names = [
        'vk',
        'telegram',
        'facebook',
        'post_day',
        'post_time',
        'article_url',
        'image_url',
        'is_posted'
    ]
    handled_scheduler_data = []
    for record in scheduler_data:
        scheduler_record = dict(zip(
            scheduler_data_names,
            record)
        )
        handled_scheduler_data.append(scheduler_record)
    return handled_scheduler_data


def is_publish_date(day_str):
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    today_datetime = datetime.now()
    today_int = today_datetime.weekday()
    today_str = calendar.day_name[today_int]
    return today_str == day_str.capitalize()


def execute_posting(scheduler_record, download_dir=None):
    image_url = scheduler_record['image_url']
    article_url = scheduler_record['article_url']
    image_id = get_file_id(image_url)
    article_id = get_file_id(article_url)
    if not (is_publish_date(scheduler_record['post_day'])
            and scheduler_record['is_posted'] == 'нет'):
        return

    post_to = []
    social_medias = ['vk', 'telegram', 'facebook']
    [post_to.append(record_key)
     for record_key in social_medias
     if scheduler_record[record_key] == 'да']

    try:
        img_file_path = download_data_for_posting(
            file_id=image_id,
            file_type='img',
            download_dir=download_dir
        )
        article_path = download_data_for_posting(
            file_id=article_id,
            file_type='article',
            download_dir=download_dir
        )
    except FileNotDownloadableError:
        print("Проблема при загрузке файлов для постинга!")
        return

    article_content = read_article_file(article_path)
    was_posted = run_reposting(
        post_to,
        img_file_path=img_file_path,
        message=article_content
    )
    return was_posted


def update_scheduler(
        service,
        post_scheduler_sheet_id,
        post_scheduler_cell_range,
        values
):
    value_input_option = 'USER_ENTERED'
    body = {
        'values': values
    }
    try:
        result = service.spreadsheets().values().update(
           spreadsheetId=post_scheduler_sheet_id,
           range=post_scheduler_cell_range,
           valueInputOption=value_input_option,
           body=body
        ).execute()
    except google_http_error:
        return
    return bool(result)


def truncate_folder(path_to_folder):
    files_to_remove = glob.glob('{}/*'.format(path_to_folder))
    for file in files_to_remove:
        os.remove(file)


def main():
    while True:
        load_dotenv()
        download_dir = 'tmp'
        os.makedirs(download_dir, exist_ok=True)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        post_scheduler_sheet_id = getenv('POST_SHEDULLER_SHEET_ID')
        post_scheduler_cell_range = 'Лист1!A3:H'
        google_service = connect_to_google(scopes)
        if not google_service:
            time.sleep(300)
            continue
        scheduler_data = get_scheduler_data(
            google_service,
            post_scheduler_sheet_id,
            post_scheduler_cell_range
        )
        if scheduler_data:
            handled_scheduler_data = unpack_sheet_range_data(scheduler_data)
            updated_scheduler_data = []
            for scheduler_record in handled_scheduler_data:
                was_posted = execute_posting(scheduler_record, download_dir)
                if was_posted:
                    scheduler_record['is_posted'] = "да"
                updated_scheduler_data.append(list(scheduler_record.values()))
            scheduler_updated = update_scheduler(
                google_service,
                post_scheduler_sheet_id,
                post_scheduler_cell_range,
                updated_scheduler_data
            )
            if not scheduler_updated:
                print("Возникла ошибка в процессе обновления расписания!")
            truncate_folder(download_dir)
        time.sleep(300)


if __name__ == '__main__':
    main()
