# -*- coding: utf-8 -*-

import io
import logging
import math
from pympler import asizeof
from PIL import Image, ImageSequence, GifImagePlugin


log = logging.getLogger(__name__)

import sys
from types import ModuleType, FunctionType
from gc import get_referents

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: ' + str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size


# source: https://dev.to/enzoftware/how-to-build-amazing-image-filters-with-python-median-filter---sobel-filter---5h7
def edge_antialiasing(img):
    new_img = Image.new("RGB", img.size, "black")
    for x in range(1, img.width - 1):  # ignore the edge pixels for simplicity (1 to width-1)
        for y in range(1, img.height - 1):  # ignore edge pixels for simplicity (1 to height-1)

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
            Gy += r + g + b

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

            Gx += r + g + b
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

            Gx += r + g + b
            Gy += r + g + b

            # calculate the length of the gradient (Pythagorean theorem)
            length = math.sqrt((Gx * Gx) + (Gy * Gy))

            # normalise the length of gradient to the range 0 to 255
            length = length / 4328 * 255

            length = int(length)

            # draw the length in the edge image
            new_img.putpixel((x, y), (length, length, length))
    return new_img


def place_edges(img, edge_img, modifiers):
    edge_img_minimum = 10
    edge_img_maximum = edge_img.crop().getextrema()[0][1]
    for x in range(1, img.width - 1):
        for y in range(1, img.height - 1):
            p = img.getpixel((x, y))
            ep = edge_img.getpixel((x, y))
            if ep[0] > edge_img_minimum:
                img.putpixel(
                    (x, y),
                    edge_colorify(
                        (ep[0] - edge_img_minimum) / (edge_img_maximum - edge_img_minimum), modifiers['colors'], p
                    ),
                )
    return img


def f(x, n, d, m, l):
    return round(((l[n] - d[n]) / 255) * (255 ** m[n] - (255 - x) ** m[n]) ** (1 / m[n]) + d[n])


def light(x):
    return tuple(f(x, i, (78, 93, 148), (0.641, 0.716, 1.262), (255, 255, 255)) for i in range(3))


def dark(x):
    return tuple(f(x, i, (35, 39, 42), (1.064, 1.074, 1.162), (114, 137, 218)) for i in range(3))


def edge_detect(img, modifier, variation, maximum, minimum):
    img = img.convert('RGBA')
    edge_img = edge_antialiasing(img)
    img = blurplefy(img, modifier, variation, maximum, minimum)
    new_img = place_edges(img, edge_img, modifier)
    return new_img


def interpolate(color1, color2, percent):
    return round((color2 - color1) * percent + color1)


def f2(x, n, colors, variation):
    if x <= variation[0]:
        return colors[0][n]
    elif x <= variation[1]:
        if variation[0] == variation[2]:
            return interpolate(colors[0][n], colors[2][n], (x - variation[0]) / (variation[1] - variation[0]))
        else:
            return interpolate(colors[0][n], colors[1][n], (x - variation[0]) / (variation[1] - variation[0]))
    elif x <= variation[2]:
        return colors[1][n]
    elif x <= variation[3]:
        return interpolate(colors[1][n], colors[2][n], (x - variation[2]) / (variation[3] - variation[2]))
    else:
        return colors[2][n]


def f3(x, n, colors, cur_color):
    array = []

    for i in range(len(colors)):
        array.append(distance_to_color(colors[i], cur_color))

    closest_color = find_max_index(array)
    if closest_color == 0:
        return interpolate(colors[0][n], colors[1][n], x)
    elif closest_color == 1:
        return interpolate(colors[1][n], colors[2][n], x)
    else:
        return interpolate(colors[2][n], colors[1][n], x)


def colorify(x, colors, variation):
    return tuple(f2(x, i, colors, variation) for i in range(3))


def edge_colorify(x, colors, cur_color):
    return tuple(f3(x, i, colors, cur_color) for i in range(3))


def remove_alpha(img, bg):
    alpha = img.convert('RGBA').getchannel('A')
    background = Image.new("RGBA", img.size, bg)
    background.paste(img, mask=alpha)
    return background


def clean_alpha(img):
    img = img.convert('RGBA')
    for x in range(img.width):
        for y in range(img.height):
            pixel = img.getpixel((x, y))
            if pixel[3] == 0:
                img.putpixel((x, y), (0, 0, 0, 0))
    return img


def blurple_filter(img, modifier, variation, maximum, minimum):
    img = img.convert('LA')
    pixels = img.getdata()
    img = img.convert('RGBA')
    results = [modifier['func']((x - minimum) * 255 / (255 - minimum)) if x >= minimum else 0 for x in range(256)]

    img.putdata((*map(lambda x: results[x[0]] + (x[1],), pixels),))
    return clean_alpha(img)


def blurplefy(img, modifier, variation, maximum, minimum):
    img = img.convert('LA')
    pixels = img.getdata()
    img = img.convert('RGBA')
    results = [
        colorify((x - minimum) / (maximum - minimum), modifier['colors'], variation) if x >= minimum else 0
        for x in range(256)
    ]
    img.putdata((*map(lambda x: results[x[0]] + (x[1],), pixels),))
    return clean_alpha(img)


def variation_maker(base, var):
    if var[0] <= -100:
        base1 = base2 = 0
        base3 = (base[2] + base[0]) / 2 * 0.75
        base4 = (base[3] + base[1]) / 2 * 1.5
    elif var[1] >= 100:
        base2 = base4 = (base[1] + base[3]) / 2 * 1.5
        base1 = base3 = (base[0] + base[2]) / 2 * 0.75
    elif var[3] >= 100:
        base3 = base4 = 1
        base1 = (base[0] + base[2]) / 2 * 0.75
        base2 = (base[1] + base[3]) / 2 * 1.5
    else:
        base1 = max(min(base[0] + var[0], 1), 0)
        base2 = max(min(base[1] + var[1], 1), 0)
        base3 = max(min(base[2] + var[2], 1), 0)
        base4 = max(min(base[3] + var[3], 1), 0)
    return base1, base2, base3, base4


def variation_converter(variations, modifier):
    variations.sort()
    base_color_var = (0.15, 0.3, 0.7, 0.85)
    background_color = None
    for var in variations:
        try:
            variation = VARIATIONS[var]
        except KeyError:
            try:
                variation = VARIATIONS['bg' + var]
                background_color = variation
                continue
            except KeyError:
                try:
                    variation = VARIATIONS['method' + var]
                    modifier = variation(modifier)
                    continue
                except KeyError:
                    raise RuntimeError(f'Invalid image variation: \"{var}\"')
        base_color_var = variation_maker(base_color_var, variation)
    return base_color_var, background_color, modifier


def invert_colors(modifier):
    modifier['colors'] = list(reversed(modifier['colors']))
    return modifier


def shift_colors(modifier):
    colors = modifier['colors']
    modifier['colors'] = [colors[2], colors[0], colors[1]]
    return modifier


def interpolate_colors(color1, color2, x):
    new_color = [0, 0, 0]
    for i in range(3):
        new_color[i] = round((color2[i] - color1[i]) * x + color1[i])
    return tuple(new_color)


def distance_to_color(color1, color2):
    total = 0
    for i in range(3):
        total += (255 - abs(color1[i] - color2[i])) / 255
    return total / 3


def find_max_index(array):
    maximum = 0
    closest = None
    for i in range(len(array)):
        if array[i] > maximum:
            maximum = array[i]
            closest = i
    return closest


def color_ratios(img, colors):
    img = img.convert('RGBA')
    total_pixels = img.width * img.height
    color_pixels = [0, 0, 0, 0]
    close_colors = []
    for i in range(3):
        close_colors.append(interpolate_colors(colors[i], colors[min(i + 1, 2)], 0.33))
        close_colors.append(interpolate_colors(colors[i], colors[max(i - 1, 0)], 0.33))

    for x in range(0, img.width):
        for y in range(0, img.height):
            p = img.getpixel((x, y))
            if p[3] == 0:
                total_pixels -= 1
                continue
            values = [0, 0, 0]
            for i in range(3):
                values[i] = max(
                    distance_to_color(p, colors[i]),
                    distance_to_color(p, close_colors[2 * i]),
                    distance_to_color(p, close_colors[2 * i + 1]),
                )
            index = find_max_index(values)
            if values[index] > 0.93:
                color_pixels[index] += 1
            else:
                color_pixels[3] += 1

    percent = [0, 0, 0, 0]
    for i in range(4):
        percent[i] = color_pixels[i] / total_pixels
    return percent


MODIFIERS = {
    'light': {
        'func': light,
        'colors': [(78, 93, 148), (114, 137, 218), (255, 255, 255)],
        'color_names': ['Dark Blurple', 'Blurple', 'White'],
    }
}

METHODS = {'--blurplefy': blurplefy, '--edge-detect': edge_detect, '--filter': blurple_filter}

VARIATIONS = {
    None: (0, 0, 0, 0),
    '++more-white': (0, 0, -0.05, -0.05),
    '++more-blurple': (-0.1, -0.1, 0.1, 0.1),
    '++more-dark-blurple': (0.05, 0.05, 0, 0),
    '++less-white': (0, 0, 0.05, 0.05),
    '++less-blurple': (0.1, 0.1, -0.1, -0.1),
    '++less-dark-blurple': (-0.05, -0.05, 0, 0),
    '++no-white': (0, 0, 500, 500),
    '++no-blurple': (0, 500, -500, 0),
    '++no-dark-blurple': (-500, -500, 0, 0),
    '++classic': (0.15, -0.15, 0.15, -0.15),
    '++less-gradient': (0.05, -0.05, 0.05, -0.05),
    '++more-gradient': (-0.05, 0.05, -0.05, 0.05),
    'method++invert': invert_colors,
    'method++shift': shift_colors,
    'bg++white-bg': (255, 255, 255, 255),
    'bg++blurple-bg': (114, 137, 218, 255),
    'bg++dark-blurple-bg': (78, 93, 148, 255),
}


def writeImage(out, frames, filename="blurple.gif"):
    # Instead of saving a series of complete images, this saves the deltas
    for s in GifImagePlugin._get_global_header(frames[0], frames[0].info):
        out.write(s)
    for frame in frames:
        dispose_extent = frame.dispose_extent
        disposal_method = frame.disposal_method
        include_color_table = frame.palette.palette != frame.global_palette.palette
        frame = frame.crop(dispose_extent)
        GifImagePlugin._write_frame_data(
            out,
            frame,
            dispose_extent[:2],
            {
                'disposal': disposal_method,
                'duration': frame.info["duration"],
                'include_color_table': include_color_table,
                'transparency': 255,
                'loop': frame.info["loop"],
            },
        )


def convert_image(image, modifier, method, variations):
    try:
        modifier_converter = dict(MODIFIERS[modifier])
    except KeyError:
        raise RuntimeError(f'Invalid image modifier: \"{modifier}\"')

    try:
        method_converter = METHODS[method]
    except KeyError:
        raise RuntimeError(f'Invalid image method: \"{method}\"')

    base_color_var, background_color, modifier_converter = variation_converter(variations, modifier_converter)

    with Image.open(io.BytesIO(image)) as img:
        filename = None
        if img.format == "GIF":
            frames = []
            durations = []
            disposals = []
            colors = []
            try:
                loop = img.info['loop']
            except KeyError:
                loop = 1

            minimum = 256
            maximum = 0
            count = 0
            new_size = img.size
            for img_frame in ImageSequence.Iterator(img):
                frame = img_frame.convert('LA')

                if frame.getextrema()[0][0] < minimum:
                    minimum = frame.getextrema()[0][0]

                if frame.getextrema()[0][1] > maximum:
                    maximum = frame.getextrema()[0][1]

                if img_frame.size[0] > new_size[0]:
                    new_size[0] = img_frame.size[0]

                if img_frame.size[1] > new_size[1]:
                    new_size[1] = img_frame.size[1]
                count += 1
            optimize = True

            if asizeof.asizeof(img) / 1024 > 9:
                width, height = new_size
                ratio = 9 / (asizeof.asizeof(img) / 1024)
                new_size = (int(width * ratio), int(height * ratio))

            if count > 50:
                width, height = new_size
                ratio = 50 / float(count)
                new_size = (int(width * ratio), int(height * ratio))

            index = 0
            palette = None

            for frame in ImageSequence.Iterator(img):
                print(index)
                index += 1
                disposals.append(frame.disposal_method if img.format == 'GIF' else frame.dispose_op)
                durations.append(frame.info['duration'])
                dispose_extent = frame.dispose_extent
                new_frame = Image.new("RGBA", new_size)
                new_frame.paste(frame.resize(new_size, Image.ANTIALIAS))
                new_img = Image.new("RGBA", new_size)
                new_img.paste(method_converter(new_frame, modifier_converter, base_color_var, maximum, minimum), (0, 0))
                if background_color is not None:
                    new_img = remove_alpha(new_img, background_color)
                alpha = new_img.getchannel('A')
                if alpha.getextrema()[0] < 255 and optimize:
                    optimize = False
                new_img = new_img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
                mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
                new_img.paste(255, mask=mask)
                new_img.dispose_extent = (
                    int(new_size[0] / frame.size[0] * frame.dispose_extent[0]),
                    int(new_size[1] / frame.size[1] * frame.dispose_extent[1]),
                    int(new_size[0] / frame.size[0] * frame.dispose_extent[2]),
                    int(new_size[1] / frame.size[1] * frame.dispose_extent[3]),
                )
                new_img.disposal_method = frame.disposal_method
                new_img.global_palette = frame.global_palette = frame.palette
                new_img.info['duration'] = frame.info['duration']
                new_img.info['loop'] = loop
                frames.append(new_img)

            out = io.BytesIO()

            try:
                frames[0].save(
                    out,
                    format='GIF',
                    append_images=frames[1:],
                    save_all=True,
                    loop=loop,
                    duration=durations,
                    disposal=disposals,
                    optimize=optimize,
                    transparency=255,
                )
            except TypeError as e:
                log.exception()
                raise RuntimeError('Invalid GIF.')

            filename = f'blurple.gif'

        elif img.format == "PNG" and img.is_animated:
            frames = []
            durations = []
            # disposals = []
            blends = []
            minimum = 256
            maximum = 0
            try:
                loop = img.info['loop']
            except KeyError:
                loop = 1

            count = 0
            new_size = img.size
            for img_frame in ImageSequence.Iterator(img):
                frame = img_frame.convert('RGBA')

                if frame.getextrema()[0][0] < minimum:
                    minimum = frame.getextrema()[0][0]

                if frame.getextrema()[0][1] > maximum:
                    maximum = frame.getextrema()[0][1]

                if img_frame.size[0] > new_size[0]:
                    new_size[0] = img_frame.size[0]

                if img_frame.size[1] > new_size[1]:
                    new_size[1] = img_frame.size[1]
                count += 1

            if asizeof.asizeof(img) / 1024 > 9:
                width, height = new_size
                ratio = 9 / (asizeof.asizeof(img) / 1024)
                new_size = (int(width * ratio), int(height * ratio))

            if count > 50:
                width, height = new_size
                ratio = 50 / float(count)
                new_size = (int(width * ratio), int(height * ratio))

            index = 0

            for frame in ImageSequence.Iterator(img):
                print(index)
                index += 1
                # disposals.append(frame.dispose_op)
                durations.append(frame.info['duration'])
                blends.append(frame.info['blend'])
                new_frame = Image.new("RGBA", new_size)
                new_frame.paste(frame.resize(new_size, Image.NEAREST))
                new_img = Image.new("RGBA", new_size)
                new_img.paste(method_converter(new_frame, modifier_converter, base_color_var, maximum, minimum), (0, 0))
                if background_color is not None:
                    new_img = remove_alpha(new_img, background_color)
                new_img.global_palette = frame.global_palette = frame.palette
                # new_img.dispose_op = frame.dispose_op
                new_img.info['duration'] = frame.info['duration']
                new_img.info['loop'] = loop
                new_img.info['blend'] = frame.info['blend']

                frames.append(new_img)

            out = io.BytesIO()

            try:
                frames[0].save(
                    out,
                    format='PNG',
                    append_images=frames[1:],
                    save_all=True,
                    loop=loop,
                    duration=durations,
                    # disposal=disposals,
                    blend=blends,
                )
            except TypeError as e:
                log.exception()
                raise RuntimeError('Invalid APNG.')

            filename = f'blurple.png'

        else:

            if asizeof.asizeof(img) / 1024 > 9:
                width, height = img.size
                ratio = 9 / (asizeof.asizeof(img) / 1024)
                img.thumbnail((int(width * ratio), int(height * ratio)), Image.ANTIALIAS)
            print(f"Final:{asizeof.asizeof(img)/1024}")
            print(asizeof.asizeof(img) / 1024)
            img = img.convert('LA')
            print(asizeof.asizeof(img) / 1024)

            minimum = img.getextrema()[0][0]
            maximum = img.getextrema()[0][1]
            print(asizeof.asizeof(img) / 1024)
            img = method_converter(img, modifier_converter, base_color_var, maximum, minimum)
            if background_color is not None:
                img = remove_alpha(img, background_color)
            print(asizeof.asizeof(img) / 1024)
            if img.tell() > 1024 ** 2 * 8:
                raise RuntimeError(f'Final image too big!')
            out = io.BytesIO()
            img.save(out, format='png')
            filename = f'blurple.png'

    out.seek(0)
    return filename, out.getvalue()


def check_image(image, modifier, method):
    try:
        modifier_converter = MODIFIERS[modifier]
    except KeyError:
        raise RuntimeError('Invalid image modifier.')

    with Image.open(io.BytesIO(image)) as img:
        if img.format == "GIF":
            total = [0, 0, 0, 0]
            count = 0

            for frame in ImageSequence.Iterator(img):
                f = frame.resize((round(img.width / 3), round(img.height / 3)))
                values = color_ratios(f, modifier_converter['colors'])
                for i in range(4):
                    total[i] += values[i]
                count += 1

            ratios = [0, 0, 0, 0]
            for i in range(4):
                ratios[i] = round(10000 * total[i] / count) / 100

            passed = ratios[3] <= 10

        else:
            img = img.resize((round(img.width / 3), round(img.height / 3)))
            values = color_ratios(img, modifier_converter['colors'])

            ratios = [0, 0, 0, 0]
            for i in range(4):
                ratios[i] = round(10000 * values[i]) / 100

            passed = ratios[3] <= 10

    colors = []
    for i in range(3):
        colors.append({'name': modifier_converter['color_names'][i], 'ratio': ratios[i]})
    colors.append({'name': 'Non-Blurple', 'ratio': ratios[3]})
    data = {'passed': passed, 'colors': colors}
    return data
