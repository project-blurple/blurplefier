# -*- coding: utf-8 -*-

import requests


GUILD_ID = input('guild id: ')

APPLICATION_ID = input('application id: ')
APPLICATION_TOKEN = 'Bot ' + input('bot token: ')

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
            'name': 'classic',
            'description': 'Use the classic blurplefy method.',
            'type': 1,
            'options': [
                {
                    'name': 'variation',
                    'description': 'Changes in color ratios.',
                    'type': 3,
                    'required': False,
                    'choices': [
                        {'name': 'Extra White', 'value': '++more-white'},
                        {'name': 'Extra Blurple', 'value': '++more-blurple'},
                        {'name': 'Extra Dark Blurple', 'value': '++more-dark-blurple'},
                        {'name': 'Less White', 'value': '++less-white'},
                        {'name': 'Less Blurple', 'value': '++less-blurple'},
                        {'name': 'Less Dark Blurple', 'value': '++less-dark-blurple'},
                        {'name': 'No White', 'value': '++no-white'},
                        {'name': 'No Blurple', 'value': '++no-blurple'},
                        {'name': 'No Dark Blurple', 'value': '++no-dark-blurple'},
                    ],
                },
                {
                    'name': 'gradient',
                    'description': 'Changes the color gradient. (More = more colors inbetween White, Blurple, and Dark Blurple)',
                    'type': 3,
                    'required': False,
                    'choices': [
                        {'name': 'Extra Less Gradient', 'value': '++less-gradient ++less-gradient'},
                        {'name': 'Less Gradient', 'value': '++less-gradient'},
                        {'name': 'More Gradient', 'value': '++more-gradient'},
                        {'name': 'Extra More Gradient', 'value': '++more-gradient ++more-gradient'},
                    ],
                },
                {
                    'name': 'order',
                    'description': 'The order of colors used to transform your image. Default: White, Blurple, Dark Blurple',
                    'type': 3,
                    'required': False,
                    'choices': [
                        {'name': 'Dark Blurple, White, Blurple', 'value': '++shift'},
                        {'name': 'Blurple, Dark Blurple, White', 'value': '++shift ++shift'},
                        {'name': 'Dark Blurple, Blurple, White', 'value': '++invert'},
                        {'name': 'White, Dark Blurple, Blurple', 'value': '++invert ++shift'},
                        {'name': 'Blurple, White, Dark Blurple', 'value': '++invert ++shift ++shift'},
                    ],
                },
                {
                    'name': 'background',
                    'description': 'Background color for transparent images',
                    'type': 3,
                    'required': False,
                    'choices': [
                        {'name': 'White', 'value': '++white-bg'},
                        {'name': 'Blurple', 'value': '++blurple-bg'},
                        {'name': 'Dark Blurple', 'value': '++dark-blurple-bg'},
                    ],
                },
                {
                    'name': 'image',
                    'description': 'The image you want to blurplefy, defaults to your avatar.',
                    'type': 11,
                    'required': False,
                },
            ],
        },
        {
            'name': 'filter',
            'description': 'Use the BlurpleFilter method.',
            'type': 1,
            'options': [
                {
                    'name': 'background',
                    'description': 'Background color for transparent images',
                    'type': 3,
                    'required': False,
                    'choices': [
                        {'name': 'White', 'value': '++white-bg'},
                        {'name': 'Blurple', 'value': '++blurple-bg'},
                        {'name': 'Dark Blurple', 'value': '++dark-blurple-bg'},
                    ],
                },
                {
                    'name': 'image',
                    'description': 'The image you want to blurplefy, defaults to your avatar.',
                    'type': 11,
                    'required': False,
                },
            ],
        },
    ],
}


create_command(blurplefy)
