# -*- coding: utf-8 -*-

import colorsys
import io
import math

import discord
from PIL import Image, ImageSequence


# source: https://dev.to/enzoftware/how-to-build-amazing-image-filters-with-python-median-filter---sobel-filter---5h7
def edge_antialiasing(img):
    new_img = Image.new("RGB", img.size, "black")
    for x in range(1, img.width-1):  # ignore the edge pixels for simplicity (1 to width-1)
        for y in range(1, img.height-1):  # ignore edge pixels for simplicity (1 to height-1)

            # initialise Gx to 0 and Gy to 0 for every pixel
            Gx = 0
            Gy = 0

            # top left pixel
            p = img.getpixel((x - 1, y - 1))
            r = p[0]
            g = p[1]
            b = p[2]

            # intensity ranges from 0 to 765 (255 * 3)
            intensity = r + g + b

            # accumulate the value into Gx, and Gy
            Gx += -intensity
            Gy += -intensity

            # remaining left column
            p = img.getpixel((x - 1, y))
            r = p[0]
            g = p[1]
            b = p[2]

            Gx += -2 * (r + g + b)

            p = img.getpixel((x - 1, y + 1))
            r = p[0]
            g = p[1]
            b = p[2]

            Gx += -(r + g + b)
            Gy += (r + g + b)

            # middle pixels
            p = img.getpixel((x, y - 1))
            r = p[0]
            g = p[1]
            b = p[2]

            Gy += -2 * (r + g + b)

            p = img.getpixel((x, y + 1))
            r = p[0]
            g = p[1]
            b = p[2]

            Gy += 2 * (r + g + b)

            # right column
            p = img.getpixel((x + 1, y - 1))
            r = p[0]
            g = p[1]
            b = p[2]

            Gx += (r + g + b)
            Gy += -(r + g + b)

            p = img.getpixel((x + 1, y))
            r = p[0]
            g = p[1]
            b = p[2]

            Gx += 2 * (r + g + b)

            p = img.getpixel((x + 1, y + 1))
            r = p[0]
            g = p[1]
            b = p[2]

            Gx += (r + g + b)
            Gy += (r + g + b)

            # calculate the length of the gradient (Pythagorean theorem)
            length = math.sqrt((Gx * Gx) + (Gy * Gy))

            # normalise the length of gradient to the range 0 to 255
            length = length / 4328 * 255

            length = int(length)

            # draw the length in the edge image
            new_img.putpixel((x, y), (length, length, length))
    return new_img


def place_edges(img, edge_img, modifiers):
    edge_img_minimum = 10  # edge_img.getextrema()[0][0]
    edge_img_maximum = edge_img.crop().getextrema()[0][1]
    for x in range(1, img.width-1):
        for y in range(1, img.height-1):
            p = img.getpixel((x, y))
            ep = edge_img.getpixel((x, y))
            if(ep[0] > edge_img_minimum):
                img.putpixel((x, y), edge_colorify((ep[0] - edge_img_minimum) / (edge_img_maximum - edge_img_minimum), modifiers['colors'], p))
    return img


def f(x, n, d, m, l):
    return round(((l[n]-d[n])/255) * (255**m[n] - (255-x)**m[n])**(1/m[n]) + d[n])


def light(x):
    return tuple(f(x, i, (78, 93, 148), (0.641, 0.716, 1.262), (255, 255, 255)) for i in range(3))


def dark(x):
    return tuple(f(x, i, (35,39,42), (1.064, 1.074, 1.162), (114, 137, 218)) for i in range(3))


def edge_detect(img, modifier, variation, maximum, minimum):
    img = img.convert('RGBA')
    edge_img = edge_antialiasing(img)
    img = blurplefy(img, modifier, variation, maximum, minimum)
    new_img = place_edges(img, edge_img, modifier)
    return new_img


def interpolate(color1, color2, percent):
    return round((color2 - color1) * percent + color1)


def f2(x, n, colors, variation):
    if x < variation[0]:
        return colors[0][n]
    elif x < variation[1]:
        if variation[0] == variation[2]:
            return interpolate(colors[0][n], colors[2][n], (x - variation[0]) / (variation[1] - variation[0]))
        else:
            return interpolate(colors[0][n], colors[1][n], (x - variation[0])/(variation[1] - variation[0]))
    elif x < variation[2]:
        return colors[1][n]
    elif x < variation[3]:
            return interpolate(colors[1][n], colors[2][n], (x - variation[2])/(variation[3] - variation[2]))
    else:
        return colors[2][n]


def f3(x, n, colors, cur_color):
    def distance_to_color(color):
        total = 0
        for i in range(3):
            total += (255 - abs(color[i] - cur_color[i])) / 255
        return total / 3
    maximum = 0
    closest_color = None
    for color in colors:
        dis = distance_to_color(color)
        if dis > maximum:
            maximum = dis
            closest_color = color

    if closest_color == colors[0]:
        return interpolate(colors[0][n], colors[1][n], x)
    elif closest_color == colors[1]:
        return interpolate(colors[1][n], colors[2][n], x)
    else:
        return interpolate(colors[2][n], colors[1][n], x)


def colorify(x, colors, variation):
    return tuple(f2(x, i, colors, variation) for i in range(3))


def edge_colorify(x, colors, cur_color):
    return tuple(f3(x, i, colors, cur_color) for i in range(3))


def blurple_filter(img, modifier, variation, maximum, minimum):
    img = img.convert('LA')
    img = img.convert('RGBA')
    pixels = img.getdata()
    results = [modifier['func']((x - minimum) * 255 / (255 - minimum)) if x >= minimum else 0 for x in range(256)]

    img.putdata((*map(lambda x: results[x[0]] + (x[1],), pixels),))
    return img


def blurplefy(img, modifier, variation, maximum, minimum):
    img = img.convert('LA')
    pixels = img.getdata()
    img = img.convert('RGBA')
    results = [colorify((x - minimum) / (maximum - minimum), modifier['colors'], variation) if x >= minimum else 0 for x in range(256)]
    img.putdata((*map(lambda x: results[x[0]] + (x[1],), pixels),))
    return img


def variation_maker(base, var):
    if var[0] <= -100 :
        base1 = base2 = 0
        base3 = (base[2] + base[0]) / 2 * .75
        base4 = (base[3] + base[1]) / 2 * 1.5
    elif var[1] >= 100:
        base2 = base4 = (base[1] + base[3]) / 2 * 1.5
        base1 = base3 = (base[0] + base[2])/2 * .75
    elif var[3] >= 100:
        base3 = base4 = 1
        base1 = (base[0] + base[2]) / 2 * .75
        base2 = (base[1] + base[3]) / 2 * 1.5
    else:
        base1 = max(min(base[0] + var[0], 1), 0)
        base2 = max(min(base[1] + var[1], 1), 0)
        base3 = max(min(base[2] + var[2], 1), 0)
        base4 = max(min(base[3] + var[3], 1), 0)
    return base1, base2, base3, base4


MODIFIERS = {
    'light': {
        'func': light,
        'colors': [(78, 93, 148, 255), (114, 137, 218, 255), (255, 255, 255, 255)]
    },
    'dark': {
        'func': dark,
        'colors': [(35, 39, 42, 255), (78, 93, 148, 255), (114, 137, 218, 255)]
    }

}
METHODS = {
    None: blurplefy,
    '--edge-detect': edge_detect,
    '--filter': blurple_filter,
}
VARIATIONS = {
    None: (0, 0, 0, 0),
    'light++more-white': (0, 0, -.1, -.1),
    'light++more-blurple': (-.1, -.1, .1, .1),
    'light++more-dark-blurple': (.1, .1, 0, 0),
    'dark++more-blurple': (0, 0, -.1, -.1),
    'dark++more-dark-blurple': (-.1, -.1, .1, .1),
    'dark++more-not-quite-black': (.1, .1, 0, 0),
    'light++less-white': (0, 0, -.1, -.1),
    'light++less-blurple': (-.1, -.1, .1, .1),
    'light++less-dark-blurple': (.1, .1, 0, 0),
    'dark++less-blurple': (0, 0, -.1, -.1),
    'dark++less-dark-blurple': (-.1, -.1, .1, .1),
    'dark++less-not-quite-black': (.1, .1, 0, 0),
    'light++no-white': (0, 0, 500, 500),
    'light++no-blurple': (0, 500, -500, 0),
    'light++no-dark-blurple': (-500, -500, 0, 0),
    'dark++no-blurple': (0, 0, 500, 500),
    'dark++no-dark-blurple': (0, 500, -500, 0),
    'dark++no-not-quite-black': (-500, -500, 0, 0),
    '++classic': (.15,-.15,.15,-.15),
    '++less-gradient': (.05,-.05,.05,-.05),
    '++more-gradient': (.05,-.05,.05,-.05),
}


def convert_image(image, modifier, method, variations):
    try:
        modifier_converter = MODIFIERS[modifier]
    except KeyError:
        raise RuntimeError('Invalid image modifier.')

    try:
        method_converter = METHODS[method]
    except KeyError:
        raise RuntimeError('Invalid image method.')

    variations.sort()

    base_color_var = (.15, .3, .7, .85)
    for var in variations:
        try:
            variation_converter = VARIATIONS[var]
        except KeyError:
            try:
                variation_converter = VARIATIONS[modifier + var]
            except KeyError:
                raise RuntimeError('Invalid image variation.')
        if method is not "--filter":
            base_color_var = variation_maker(base_color_var, variation_converter)
    if method is not "--filter":
        variation_converter = base_color_var

    with Image.open(io.BytesIO(image)) as img:
        if img.format == "GIF":
            frames = []
            minimum = 256
            maximum = 0
            transparency = img.info['transparency']
            loop = img.info['loop']
            for imgframe in ImageSequence.Iterator(img):
                frame = imgframe.convert('LA')
                frame.info['duration'] = imgframe.info['duration']
                if frame.getextrema()[0][0] < minimum:
                    minimum = frame.getextrema()[0][0]
                if frame.getextrema()[0][1] > maximum:
                    maximum = frame.getextrema()[0][1]
            for frame in ImageSequence.Iterator(img):
                new_frame = method_converter(frame, modifier_converter, variation_converter, maximum, minimum)
                frames.append(new_frame)
            out = io.BytesIO()
            frames[0].save(out, format='GIF', append_images=frames, save_all=True, transparency=transparency, loop=loop)
            filename = f'{modifier}.gif'
        else:
            img = img.convert('LA')
            minimum = img.getextrema()[0][0]
            maximum = img.getextrema()[0][1]

            img = method_converter(img, modifier_converter, variation_converter, maximum, minimum)

            out = io.BytesIO()
            img.save(out, format='png')
            filename = f'{modifier}.png'
    out.seek(0)
    return discord.File(out, filename=filename)
