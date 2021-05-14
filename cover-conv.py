import argparse
import logging
from collections.abc import Iterable
from itertools import zip_longest
from pathlib import Path

from PIL import Image
from PIL.ImageFilter import GaussianBlur

logger = logging.getLogger("cover-conv")

DPI = 300
STICKER_W = 83.8
STICKER_H = 50.8

# from https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def mm_to_px(x: float, dpi=DPI) -> int:
    return int(0.03937008 * x * dpi)


def resize_rotate_image(image: Image) -> Image:
    w, h = image.size
    if h >= w:
        image = image.transpose(Image.ROTATE_90)
        w, h = image.size

    fact_h = h / mm_to_px(STICKER_H)
    fact_w = w / mm_to_px(STICKER_W)
    fact = max(fact_w, fact_h)
    new_w = w / fact
    new_h = h / fact

    image = image.resize(size=(int(new_w), int(new_h)))

    return image


def fill(image: Image) -> Image:
    ori_image = image.copy()

    image = image.resize(size=(mm_to_px(STICKER_W + 5), mm_to_px(STICKER_H + 5)))
    image = image.filter(GaussianBlur(radius=16))
    offset_x = int((mm_to_px(STICKER_W + 5) - ori_image.size[0]) / 2)
    offset_y = int((mm_to_px(STICKER_H + 5) - ori_image.size[1]) / 2)
    image.paste(
        ori_image,
        (
            offset_x,
            offset_y,
            offset_x + ori_image.size[0],
            offset_y + ori_image.size[1],
        ),
    )

    return image


def stitch_images(images: Iterable[Image]) -> Image:
    page_im = Image.new(mode="RGB", size=(mm_to_px(210), mm_to_px(297)), color="white")
    for ii, im in enumerate(images):
        if im is None:
            break

        x_offset = mm_to_px(18.64 - 2.5)
        y_offset = mm_to_px(21.5 + 2 * STICKER_H * ii - 2.5)
        page_im.paste(
            im, (x_offset, y_offset, x_offset + im.size[0], y_offset + im.size[1])
        )
        x_offset = mm_to_px(18.64 + STICKER_W + 5.26 - 2.5)
        page_im.paste(
            im, (x_offset, y_offset, x_offset + im.size[0], y_offset + im.size[1])
        )

        if ii > 3:
            raise NotImplementedError()

    return page_im


def main():
    parser = argparse.ArgumentParser(
        description="convert cover images to HERMA 5028 stickers"
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "input_file",
        type=lambda x: Path(x).expanduser().resolve(),
        nargs="+",
    )
    parser.add_argument(
        "output_file",
        type=lambda x: Path(x).expanduser().resolve(),
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    output_file = args.output_file

    images = (Image.open(p) for p in args.input_file)
    images = (resize_rotate_image(i) for i in images)
    images = (fill(i) for i in images)
    images = (stitch_images(ims) for ims in grouper(images, 3, None))
    for ii, im in enumerate(images):
        out_path = output_file.with_suffix(f".{ii}{output_file.suffix}")
        im.save(out_path)


if __name__ == "__main__":
    main()
