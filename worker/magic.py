# -*- coding: utf-8 -*-

import colorsys
import io

import discord
from PIL import Image


# Filter
def f(x, n, d, m, l):
    return round(((l[n]-d[n])/255) * (255**m[n] - (255-x)**m[n])**(1/m[n]) + d[n])


def light(x):
    return tuple(f(x, i, (78, 93, 148), (0.641, 0.716, 1.262), (255, 255, 255)) for i in range(3))


def dark(x):
    return tuple(f(x, i, (35,39,42), (1.064, 1.074, 1.162), (114, 137, 218)) for i in range(3))




def blurple_filter(img, modifier, variation):
    img = img.convert('LA')

    pixels = img.getdata()
    img = img.convert('RGBA')

    minimum = img.getextrema()[0][0]

    results = [modifier['func']((x - minimum) * 255 / (255 - minimum)) if x >= minimum else 0 for x in range(256)]

    img.putdata((*map(lambda x: results[x[0]] + (x[1],), pixels),))
    return img



MODIFIERS = {
    'light': {
        'func': light,
        'colors': [(78, 93, 148), (114, 137, 218), (255, 255, 255)]
    },
    'dark': {
        'func': dark,
        'colors': [(35, 39, 42), (78, 93, 148), (114, 137, 218)]
    }
}
METHODS = {
    '--filter': blurple_filter,
}
VARIATIONS = {
}
def convert_image(image, modifier, method, variation):
    try:
        modifier_converter = MODIFIERS[modifier]
    except KeyError:
        raise RuntimeError('Invalid image modifier.')

    try:
        method_converter = METHODS[method]
    except KeyError:
        raise RuntimeError('Invalid image method.')

    try:
        variation_converter = VARIATIONS[variation]
    except KeyError:
        raise RuntimeError('Invalid image variation.')

    with Image.open(io.BytesIO(image)) as img:
        img = method_converter(img, modifier_converter, variation_converter)

        out = io.BytesIO()
        img.save(out, format='png')

    out.seek(0)
    return discord.File(out, filename=f'{modifier}.png')
