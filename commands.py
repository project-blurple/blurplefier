# -*- coding: utf-8 -*-

import requests


GUILD_ID = input('guild id: ')

APPLICATION_ID = input('application id: ')
APPLICATION_TOKEN = 'bot ' + input('bot token: ')

URL = f'https://discord.com/api/v8/applications/{APPLICATION_ID}/guilds/{GUILD_ID}/commands'


def create_command(data):
    response = requests.post(URL, json=data, headers={'authorization': APPLICATION_TOKEN})

    if response.status_code in (200, 201, 204):
        print('Command created!')
    else:
        print('Creating command failed!')
        print(response.status_code)
        print(response.json())


blurplefy = {
    'name': 'blurplefy',
    'description': 'Blurplefy your avatar or an image from a URL.',
    'options': [
        {
            'name': 'url',
            'description': 'URL of an image you want to blurplefy.',
            'type': 3,
            'required': False,
        },
    ],
}


create_command(blurplefy)
