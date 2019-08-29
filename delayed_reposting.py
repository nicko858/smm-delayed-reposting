from __future__ import print_function
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import urllib.parse as urlparse
from reposting import run_reposting
import os
import os.path
import glob


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
        image_id=None,
        article_id=None,
        download_dir=None
):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    img_file = drive.CreateFile({'id': image_id})
    img_file.FetchMetadata()

    article_file = drive.CreateFile({'id': article_id})
    article_file.FetchMetadata()

    img_file_name = img_file.metadata['originalFilename']
    article_name = article_file.metadata['title']

    img_file_download_path = os.path.join(download_dir, img_file_name)
    article_download_path = os.path.join(
            download_dir,
            article_name
        )

    try:
        img_file.GetContentFile(img_file_download_path)
        article_file.GetContentFile(
            article_download_path,
            mimetype='text/plain'
        )
        return img_file_download_path, article_download_path
    except:
        pass


def connect_to_google(scopes):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)
    return service


def get_sheduller_data(
        service,
        post_sheduller_sheet_id,
        post_sheduller_cell_range
):
    value_render_option = 'FORMULA'
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=post_sheduller_sheet_id,
        range=post_sheduller_cell_range,
        valueRenderOption=value_render_option
    ).execute()
    print(result)
    sheduller_data = result.get('values', [])
    return sheduller_data


def handle_sheduller_data(sheduller_data):
    print(sheduller_data)
    if not sheduller_data:
        print('Не удалось найти расписание публикациЙ!')
    else:
        sheduller_data_names = [
            'vk',
            'telegram',
            'facebook',
            'post_day',
            'post_time',
            'article_url',
            'image_url',
            'is_posted'
        ]
        handled_sheduller_data = []
        for record in sheduller_data:
            sheduller_record = dict(zip(
                sheduller_data_names,
                record)
            )
            handled_sheduller_data.append(sheduller_record)
        return handled_sheduller_data


def execute_sheduller(handled_sheduller_data, download_dir=None):
    for sheduller_record in handled_sheduller_data:
        image_url = sheduller_record['image_url']
        article_url = sheduller_record['article_url']
        if image_url and article_url:
            image_id = get_file_id(image_url)
            article_id = get_file_id(article_url)
            if (sheduller_record['post_day'] == 'суббота'
                    and sheduller_record['is_posted'] == 'нет'):
                post_to = []
                for record_key in ['vk', 'telegram', 'facebook']:
                    if sheduller_record[record_key]:
                        post_to.append(record_key)
                img_file_path, article_path = download_data_for_posting(
                    image_id=image_id,
                    article_id=article_id,
                    download_dir=download_dir
                )
                article_content = read_article_file(article_path)
                run_reposting(
                    post_to,
                    img_file_path=img_file_path,
                    message=article_content
                )
                sheduller_record['is_posted'] = "Да"
    print(handled_sheduller_data.values())
    

def update_sheduller(
        service,
        post_sheduller_sheet_id,
        post_sheduller_cell_range
):
    value_render_option = 'FORMULA'
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=post_sheduller_sheet_id,
        range=post_sheduller_cell_range,
        valueRenderOption=value_render_option
    ).execute()
    sheduller_data = result.get('values', [])


def truncate_folder(path_to_folder):
    files_to_remove = glob.glob('{}/*'.format(path_to_folder))
    for file in files_to_remove:
        os.remove(file)


if __name__ == '__main__':
    download_dir = 'tmp'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    post_sheduller_sheet_id = '1HbSI6IFkc2GK3MBwZCRxMHrhCOxzMxVG11203KK9Sx4'
    post_sheduller_cell_range = 'Лист1!A3:H'
    google_service = connect_to_google(scopes)
    sheduller_data = get_sheduller_data(
        google_service,
        post_sheduller_sheet_id,
        post_sheduller_cell_range
    )
    handled_sheduller_data = handle_sheduller_data(sheduller_data)
    execute_sheduller(handled_sheduller_data, download_dir)
    truncate_folder(download_dir)




