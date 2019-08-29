from telegram.error import NetworkError

from dotenv import load_dotenv
from os import getenv
from external_api import (
    upload_photo_to_vk,
    save_img_to_vk,
    get_vk_upload_address,
    post_photo_to_vk_wall
)
from external_api import post_to_facebook, post_to_telegram
from external_api import FaceBookAPIUnavailable, VkAPIUnavailable


def invoke_vk_posting(
        img_file_path,
        message,
        vk_access_token,
        vk_group_id
):
    try:
        upload_url = get_vk_upload_address(
            vk_group_id,
            vk_access_token
        )
        with open(img_file_path, 'rb') as img_file:
            img_obj_for_vk = {'photo': img_file}
            uploaded_photo, server, img_hash = upload_photo_to_vk(
                upload_url,
                img_obj_for_vk
            )
        media_id, owner_id = save_img_to_vk(
            vk_access_token,
            uploaded_photo,
            vk_group_id,
            server,
            img_hash
        )
        post_photo_to_vk_wall(
            vk_group_id,
            owner_id,
            media_id,
            message,
            vk_access_token
        )
    except VkAPIUnavailable as error:
        print("Error during VK posting:\n{}".format(error))


def invoke_facebook_posting(
        img_file_path,
        message,
        facebook_access_token,
        facebook_group_id
):
    try:
        with open(img_file_path, 'rb') as img_file:
            post_to_facebook(
                facebook_access_token,
                facebook_group_id,
                img_file,
                message
            )
    except FaceBookAPIUnavailable as error:
        print("Error during Facebook posting:\n{}".format(error))


def invoke_telegram_posting(
        img_file_path,
        message,
        chat_id,
        bot_token,
        proxy_url=None):
    try:
        with open(img_file_path, 'rb') as img_file:
            post_to_telegram(
                img_file,
                message,
                chat_id,
                bot_token,
                proxy_url=proxy_url
            )
    except NetworkError as error:
        print("Error during Telegram posting:\n{}".format(error))


def run_reposting(post_to, img_file_path=None, message=None):
    load_dotenv()
    vk_access_token = getenv("VK_ACCESS_TOKEN")
    vk_group_id = getenv("VK_GROUP_ID")
    bot_token = getenv("TELEGRAM_BOT_TOKEN")
    chat_id = getenv("TELEGRAM_CHANNEL_NAME")
    proxy_url = getenv("HTTPS_PROXY")
    facebook_access_token = getenv("FACEBOOK_TOKEN")
    facebook_group_id = getenv("FACEBOOK_GROUP")

    for parameter in post_to:
        if parameter == 'vk':
            invoke_vk_posting(
                img_file_path,
                message,
                vk_access_token,
                vk_group_id
            )
        elif parameter == 'facebook':
            invoke_facebook_posting(
                img_file_path,
                message,
                facebook_access_token,
                facebook_group_id
            )
        elif parameter == 'telegram':
            invoke_telegram_posting(
                img_file_path,
                message,
                chat_id,
                bot_token,
                proxy_url=proxy_url
            )









