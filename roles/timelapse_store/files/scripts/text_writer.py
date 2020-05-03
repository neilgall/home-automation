from datetime import datetime
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
from typing import Tuple


class TextWriter:
  def __init__(self, base_image):
    self._base_image = base_image.convert('RGBA')
    self._text_image = Image.new('RGBA', base_image.size, (0,0,0,0))
    self._font = ImageFont.truetype('VeraBd.ttf', 40)
    self._context = ImageDraw.Draw(self._text_image)
    self._color = (255,255,255,255)

  def write(self, x, y, txt):
    px = int(x * self._text_image.size[0])
    py = int(y * self._text_image.size[1])
    self._context.text((px, py), txt, font=self._font, fill=self._color)

  def composite(self):
    shadow = self._text_image.filter(ImageFilter.GaussianBlur(5))
    shadowed = Image.alpha_composite(self._base_image, shadow)
    return Image.alpha_composite(shadowed, self._text_image)


class DateTimeOverlay:
  def __init__(self, x1: int, x2: int, y: int):
    self._x1 = x1
    self._x2 = x2
    self._y = y

  def draw(self, writer: TextWriter, data: dict):
    if 'unix_time' in data:
      dt = datetime.fromtimestamp(data['unix_time'])
      writer.write(self._x1, self._y, dt.strftime('%b %d'))
      writer.write(self._x2, self._y, dt.strftime('%H:%M'))


class LabelledDataOverlay:
  def __init__(self, x1: int, x2: int, y: int, key: str, label: str, fmt: str):
    self._x1 = x1
    self._x2 = x2
    self._y = y
    self._key = key
    self._label = label
    self._fmt = fmt

  def draw(self, writer: TextWriter, data: dict):
    if self._key in data:
      writer.write(self._x1, self._y, self._label)
      writer.write(self._x2, self._y, self._fmt % data[self._key])


class PlainDataOverlay:
  def __init__(self, x: int, y: int, key: str, fmt: str):
    self._x = x
    self._y = y
    self._key = key
    self._fmt = fmt

  def draw(self, writer: TextWriter, data: dict):
    if self._key in data:
      writer.write(self._x, self._y, self._fmt % data[self._key])
