# -*- coding: utf-8 -*-

import colorsys
import io

import discord
from PIL import Image


def f(x, n, d, m, l):
    return round(((l[n]-d[n])/255) * (255**m[n] - (255-x)**m[n])**(1/m[n]) + d[n])


def light(x):
    return tuple(f(x, i, (78, 93, 148), (0.641, 0.716, 1.262), (255, 255, 255)) for i in range(3))


def dark(x):
    return tuple(f(x, i, (35,39,42), (1.064, 1.074, 1.162), (114, 137, 218)) for i in range(3))


# def dark2(x):
#     return tuple(f(x, i, (44,47,51), (0.976, 1.014, 1.124), (114, 137, 218)) for i in range(3))

MODIFIERS = {
    'light': light,
    'dark': dark,
    'orange': orange,
    'gay': gay,
}


def convert_image(image, modifier):
    try:
        converter = MODIFIERS[modifier]
    except KeyError:
        raise RuntimeError('Invalid image modifier.')

    with Image.open(io.BytesIO(image)) as img:
        img = img.convert('LA')

        pixels = img.getdata()
        img = img.convert('RGBA')

        minimum = img.getextrema()[0][0]

        results = [converter((x - minimum) * 255 / (255 - minimum)) if x >= minimum else 0 for x in range(256)]

        img.putdata((*map(lambda x : results[x[0]] + (x[1],), pixels),))

        out = io.BytesIO()
        img.save(out, format='png')

    out.seek(0)
    return discord.File(out, filename=f'{modifier}.png')
