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


def run_reposting(post_to, img_file_path=None, message=None):
    load_dotenv()
    vk_access_token = getenv("VK_ACCESS_TOKEN")
    vk_group_id = getenv("VK_GROUP_ID")
    bot_token = getenv("TELEGRAM_BOT_TOKEN")
    chat_id = getenv("TELEGRAM_CHANNEL_NAME")
    proxy_url = getenv("HTTPS_PROXY")
    facebook_access_token = getenv("FACEBOOK_TOKEN")
    facebook_group_id = getenv("FACEBOOK_GROUP")
    was_posted = False
    for parameter in post_to:
        try:
            if parameter == 'vk':
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
            elif parameter == 'facebook':
                with open(img_file_path, 'rb') as img_file:
                    post_to_facebook(
                        facebook_access_token,
                        facebook_group_id,
                        img_file,
                        message
                    )
            elif parameter == 'telegram':
                with open(img_file_path, 'rb') as img_file:
                    post_to_telegram(
                        img_file,
                        message,
                        chat_id,
                        bot_token,
                        proxy_url=proxy_url
                    )
                was_posted =True
                return was_posted
        except VkAPIUnavailable as error:
            print("Error during VK posting:\n{}".format(error))
            return was_posted
        except FaceBookAPIUnavailable as error:
            print("Error during Facebook posting:\n{}".format(error))
            return was_posted
        except NetworkError as error:
            print("Error during Telegram posting:\n{}".format(error))
            return was_posted











