# -*- coding: utf-8 -*-

import base64
import json
import os
import random

import discord_interactions
import requests


CLIENT_ID = os.environ['APPLICATION_CLIENT_ID']
PUBLIC_KEY = os.environ['APPLICATION_PUBLIC_KEY']

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
}


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


def send_response(interaction, *, data=None, image=None, followup=False):
    interaction_id = interaction['id']
    interaction_token = interaction['token']

    kwargs = {
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

    return requests.post(**kwargs)


def handler(event, context):
    data = event.get('body', '')
    encoded = event.get('isBase64Encoded', False)

    if not encoded:
        data = data.encode('utf-8')
    else:
        data = base64.b64decode(data)

    signature = event['headers'].get('x-signature-ed25519')
    timestamp = event['headers'].get('x-signature-timestamp')

    if not (signature and timestamp and discord_interactions.verify_key(data, signature, timestamp, PUBLIC_KEY)):
        return Response(401, {'error': 'Request signature invalid.'}).to_lambda_response()

    interaction = json.loads(data)

    if interaction['type'] == discord_interactions.InteractionType.PING:
        return Response(200, {'type': discord_interactions.InteractionResponseType.PONG}).to_lambda_response()

    guild_id = interaction['guild_id']
    channel_id = interaction['channel_id']

    if channel_id not in ALLOWED_CHANNELS.get(guild_id, []):
        channel_ids = ALLOWED_CHANNELS.get(guild_id)
        mentions = ' '.join(f'<#{x}>' for x in channel_ids) or 'other servers'

        data = {
            'type': discord_interactions.InteractionResponseType.CHANNEL_MESSAGE,
            'data': {
                'content': f'This command can only be used in {mentions}!',
                'flags': discord_interactions.InteractionResponseFlags.EPHEMERAL,
            },
        }

        return Response(200, data).to_lambda_response()

    send_response(interaction, data={'type': discord_interactions.InteractionResponseType.ACKNOWLEDGE_WITH_SOURCE})

    # TODO: Download user avatar or supplies image URL here, convert it and change it out from sample images
    # These are just here to ensure sending the initial ACK and then the followup message + image works as intended
    choices = (
        'https://files.snowyluma.dev/Fv7Lxi.gif',
        'https://files.snowyluma.dev/mkaDDE.jpg',
        'https://files.snowyluma.dev/nzyJl5.jpg',
        'https://files.snowyluma.dev/50ck33.png',
    )

    url = random.choice(choices)
    resp = requests.get(url=url)

    data = {'content': 'Zeboat has to code the actual image conversion, so have a random image from me,,'}
    send_response(interaction, data=data, image=Image(url[-10:], resp.content), followup=True)

    return Response(200).to_lambda_response()  # I'm not sure what we're supposed to return here,, but this works :)
