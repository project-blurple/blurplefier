# -*- coding: utf-8 -*-

import base64
import json
import os
import traceback
from typing import Any, Dict

import discord_interactions
import requests

import magic


CLIENT_ID = os.environ['APPLICATION_CLIENT_ID']
PUBLIC_KEY = os.environ['APPLICATION_PUBLIC_KEY']

DEBUG = os.environ.get('DEBUG')

# Please don't delete any of the test channels
# Instead just add your own, your app won't be in the other guilds anyway
ALLOWED_CHANNELS = {
    # Blob Emoji
    '272885620769161216': [
        '411929226066001930',  # blob-development -> bot-spamz
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
        '799271219592560660',  # blurple-playground -> blurplfier-1
        '799271239557709864',  # blurple-playground -> blurplfier-2
        # '442725328130015244', # staff-lobby -> moderator-playground
    ],
}

SAD_EMOJI = '<a:ablobsadrain:620464068393828382>'


class Image:
    def __init__(self, name, data):
        self.name = name
        self.data = data


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


def send_response(interaction, *, data=None, image=None, followup=True):
    interaction_id = interaction['id']
    interaction_token = interaction['token']

    kwargs: Dict[str, Any] = {
        'headers': {
            'user-agent': 'Blurplefier/2021.0 (+https://github.com/project-blurple/blurplefier)',
        },
    }

    if image is None:
        kwargs['json'] = data
        kwargs['headers']['content-type'] = 'application/json'
    else:
        kwargs['files'] = {image.name: image.data}

        if data is not None:
            kwargs['data'] = {'payload_json': json.dumps(data)}

    if followup:
        kwargs['url'] = f'https://discord.com/api/webhooks/{CLIENT_ID}/{interaction_token}'
    else:
        kwargs['url'] = f'https://discord.com/api/v8/interactions/{interaction_id}/{interaction_token}/callback'

    r = requests.post(**kwargs)
    print(r.text)
    return r


def inner_handler(event, context):
    data = event.get('body', '')
    encoded = event.get('isBase64Encoded', False)

    if not encoded:
        data = data.encode('utf-8')
    else:
        data = base64.b64decode(data)

    event['headers'] = event.get('headers', {})

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
        channel_ids = ALLOWED_CHANNELS.get(guild_id, [])
        mentions = ' '.join(f'<#{x}>' for x in channel_ids) or 'other servers'

        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {
                'content': f'This command can only be used in {mentions}!',
                'flags': discord_interactions.InteractionResponseFlags.EPHEMERAL,
            },
        }

        return Response(200, data)

    data = {
        'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        'data': {'content': 'Request accepted. Blurplefying...'},
    }
    send_response(interaction, data=data, followup=False)

    # Dict[Snowflake, Attachment]
    attachments = interaction['data'].get('resolved', {}).get('attachments', {})

    try:
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
                if option['name'] == 'image':
                    attachment_id = option['value']
                    url = attachments[attachment_id]['url']
                    continue

                to_add = option['value'].split()
                for v in to_add:
                    variations.append(v)

        if url is None:
            if not avatar:
                data = {'content': f'<@!{user_id}> You need an avatar before you can blurplefy! {SAD_EMOJI}'}
                send_response(interaction, data=data, followup=True)
                return
            ext = 'gif' if avatar.startswith('a_') else 'png'
            url = f'https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size=512'

        try:
            resp = requests.get(url, stream=True)
        except requests.exceptions.MissingSchema:
            data = {'content': f'The supplied URL was invalid <@!{user_id}>! {SAD_EMOJI}'}
            send_response(interaction, data=data, followup=True)
            return

        if resp.status_code != 200:
            data = {'content': f'I couldn\'t download your image <@!{user_id}>! {SAD_EMOJI}'}
            send_response(interaction, data=data, followup=True)
            return

        if int(resp.headers.get('content-length', '0')) > 1024**2 * 8:
            data = {'content': f'Your image is too large (> 8MiB) <@!{user_id}>! {SAD_EMOJI}'}
            send_response(interaction, data=data, followup=True)
            return

        try:
            data = {'content': f'Your requested image is ready <@!{user_id}>!'}
            image = Image(*magic.convert_image(resp.content, 'light', method, variations))
        except magic.InvalidImageFormat as error:
            image = None

            if error.format is None:
                detail = 'Invalid image format given.'
            else:
                detail = f'{error.format.title()} is not a supported image format.'

            data = {'content': f'{detail} Please supply a PNG, JPG, GIF, or WEBP image instead.'}
        except Exception as error:
            image = None
            data = {
                'content': f'I was unable to blurplefy your image <@!{user_id}>! {SAD_EMOJI}\nPlease try a different image.'
            }

            if DEBUG:
                data['content'] += f'\n{error}'
        resp = send_response(interaction, data=data, image=image, followup=True)

        if 400 <= resp.status_code <= 599:
            data = {'content': f'I couldn\'t upload your finished image <@!{user_id}>! {SAD_EMOJI}'}
            send_response(interaction, data=data, followup=True)
    except Exception:
        data = {'content': traceback.format_exc()}
        send_response(interaction, data=data, followup=True)


def handler(event, context):
    response = inner_handler(event, context)

    if response is None:
        response = Response(200)

    return response.to_lambda_response()
