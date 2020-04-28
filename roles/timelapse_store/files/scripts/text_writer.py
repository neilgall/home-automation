from datetime import datetime
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
from typing import Tuple


class TextWriter:
  def __init__(self, base_image, origin: Tuple[int,int], cell_size: Tuple[int,int]):
    self._base_image = base_image.convert('RGBA')
    self._text_image = Image.new('RGBA', base_image.size, (0,0,0,0))
    self._font = ImageFont.truetype('VeraBd.ttf', 40)
    self._context = ImageDraw.Draw(self._text_image)
    self._color = (255,255,255,255)
    self._origin = origin
    self._cell_size = cell_size

  def write(self, x, y, txt):
    px = (self._origin[0] + x * self._cell_size[0]) * self._text_image.size[0]
    py = (self._origin[1] + y * self._cell_size[1]) * self._text_image.size[1]
    self._context.text((px, py), txt, font=self._font, fill=self._color)

  def composite(self):
    shadow = self._text_image.filter(ImageFilter.GaussianBlur(5))
    shadowed = Image.alpha_composite(self._base_image, shadow)
    return Image.alpha_composite(shadowed, self._text_image)


class DateTimeOverlay:
  def draw(self, writer: TextWriter, x: int, y: int, data: dict):
    if 'timestamp' in data:
      dt = datetime.fromtimestamp(data['timestamp'])
      writer.write(x, y, dt.strftime('%b %d'))
      writer.write(x+1, y, dt.strftime('%H:%M'))


class DataOverlay:
  def __init__(self, key: str, label: str, fmt: str):
    self._key = key
    self._label = label
    self._fmt = fmt

  def draw(self, writer: TextWriter, x: int, y: int, data: dict):
    if self._key in data:
      writer.write(x, y, self._label)
      writer.write(x+1, y, self._fmt % data[self._key])

