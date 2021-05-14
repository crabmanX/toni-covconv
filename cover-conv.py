import argparse
import logging
from collections.abc import Iterable
from pathlib import Path

from PIL import Image
from PIL.ImageFilter import GaussianBlur

logger = logging.getLogger("cover-conv")

DPI = 300
STICKER_W = 83.8
STICKER_H = 50.8


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
    x_locs = [18.64, 18.64 + STICKER_W + 5.26]
    y_locs = [21.5, 21.5 + 2 * STICKER_H, 21.5 + 4 * STICKER_H]
    for ii, im in enumerate(images):
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
    output_image = stitch_images(images)

    output_image.save(output_file)


if __name__ == "__main__":
    main()
