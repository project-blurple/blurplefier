# -*- coding: utf-8 -*-

import base64
import json
from logging import exception
import os
import traceback

import backblaze
import backblaze.settings
import discord_interactions
import requests
import time
import magic


CLIENT_ID = os.environ['APPLICATION_CLIENT_ID']
PUBLIC_KEY = os.environ['APPLICATION_PUBLIC_KEY']

B2_BUCKET_ID = os.environ['B2_BUCKET_ID']
B2_APPLICATION_KEY = os.environ['B2_APPLICATION_KEY']
B2_APPLICATION_KEY_ID = os.environ['B2_APPLICATION_KEY_ID']

IMAGES_BASE_URL = os.environ['IMAGES_BASE_URL']

# Please don't delete any of the test channels
# Instead just add your own, your app won't be in the other guilds anyway
ALLOWED_CHANNELS = {
    # Blob Emoji
    '272885620769161216': [
        '411929226066001930',  # blob-development -> bot-spam
    ],
    # Comet Observatory
    '380295555039100932': [
        '771892440374050837',  # luma -> bot-spam
    ],
    # B.A.D. (Blurple Application Development)
    '559341262302347314': [
        '559342069932359681',  # blurplefier -> bot-spam
    ],
    # Project Blurple
    '412754940885467146': [
        '442725328130015244',  # staff-lobby -> moderator-playground
    ],
}

SAD_EMOJI = '<a:ablobsadrain:620464068393828382>'


class Response:
    def __init__(self, status, data=None):
        self.status = status
        self.data = data or {}

    def to_lambda_response(self):
        data = {
            'statusCode': self.status,
            'body': json.dumps(self.data),
            'headers': {
                'Content-Type': 'application/json',
            },
        }

        return data


def inner_handler(event, context):
    data = event.get('body', '')
    encoded = event.get('isBase64Encoded', False)

    if not encoded:
        data = data.encode('utf-8')
    else:
        data = base64.b64decode(data)

    signature = event['headers'].get('x-signature-ed25519')
    timestamp = event['headers'].get('x-signature-timestamp')

    if not (signature and timestamp and discord_interactions.verify_key(data, signature, timestamp, PUBLIC_KEY)):
        return Response(401, {'error': 'Request signature invalid.'})

    interaction = json.loads(data)

    if interaction['type'] == discord_interactions.InteractionType.PING:
        return Response(200, {'type': discord_interactions.InteractionResponseType.PONG})

    guild_id = interaction['guild_id']
    channel_id = interaction['channel_id']

    if channel_id not in ALLOWED_CHANNELS.get(guild_id, []):
        channel_ids = ALLOWED_CHANNELS.get(guild_id)
        mentions = ' '.join(f'<#{x}>' for x in channel_ids) or 'other servers'

        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {
                'content': f'This command can only be used in {mentions}!',
                'flags': discord_interactions.InteractionResponseFlags.EPHEMERAL,
            },
        }

        return Response(200, data)

    user = interaction['member']['user']
    avatar = user['avatar']
    user_id = user['id']
    url = None

    if interaction['data']['options'][0]['name'] == 'classic':
        method = '--blurplefy'
    else:
        method = '--filter'

    variations = []
    if 'options' in interaction['data']['options'][0]:
        for option in interaction['data']['options'][0]['options']:
            if option['name'] == 'url':
                url = option['value']
                continue

            to_add = option['value'].split()
            for v in to_add:
                variations.append(v)

    if url is None:
        ext = 'gif' if avatar.startswith('a_') else 'png'
        url = f'https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size=512'

    try:
        resp = requests.get(url, stream=True)
    except requests.exceptions.MissingSchema:
        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': f'The supplied URL was invalid <@!{user_id}>! {SAD_EMOJI}'},
        }
        return Response(200, data)
    except requests.exceptions.RequestException:
        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': f'I was unable to download your image <@!{user_id}>! {SAD_EMOJI}'},
        }
        return Response(200, data)

    if resp.status_code != 200:
        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': f'I couldn\'t download your image <@!{user_id}>! {SAD_EMOJI}'},
        }
        return Response(200, data)

    # if int(resp.headers.get('content-length', '0')) > 1024 ** 2 * 8:
    #     data = {'content': f'Your image is too large (> 8MiB) <@!{user_id}>! {SAD_EMOJI}'}
    #     send_response(interaction, data=data, followup=True)
    #     return

    try:
        name, data = magic.convert_image(resp.content, 'light', method, variations)
    except Exception:
        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': f'I was unable to blurplefy your image <@!{user_id}>! {SAD_EMOJI}'},
        }
        return Response(200, data)

    client = backblaze.Blocking(key=B2_APPLICATION_KEY, key_id=B2_APPLICATION_KEY_ID)

    try:
        client.authorize()
    except backblaze.exceptions.UnAuthorized:
        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': 'Unable to upload image, invalid credentials provided.'},
        }
        return Response(200, data)

    bucket = client.bucket(bucket_id=B2_BUCKET_ID)

    name = f'{user_id}/{int(time.time())}/{name}'
    settings = backblaze.settings.UploadSettings(name=name)

    try:
        bucket.upload(settings, data)
    except backblaze.exceptions.BackblazeException:
        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {
                'content': f'I was unable to upload your image, please try again later <@!{user_id}>! {SAD_EMOJI}'
            },
        }
        return Response(200, data)

    try:
        client.close()
    except Exception:
        pass

    data = {
        'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        'data': {
            'content': (
                f'Your image has been converted <@!{user_id}>!\n'
                f'**The image URL will expire, download it to keep it!**\n\n{IMAGES_BASE_URL}/{name}'
            )
        },
    }

    return Response(200, data)


def handler(event, context):
    return inner_handler(event, context).to_lambda_response()


def test_handler(event, context):
    try:
        return inner_handler(event, context).to_lambda_response()
    except Exception as e:
        import traceback

        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {
                'content': traceback.format_exc(),
            },
        }

        return Response(200, data).to_lambda_response()
