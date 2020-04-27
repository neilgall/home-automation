import argparse
import os
import re
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from pirrigator_client import PirrigatorClient
from typing import Iterable


_PATH_FORMAT = re.compile(r'img(\d\d)(\d\d)(\d\d)(\d\d)(\d\d).jpg')

_TEXT_FORMATS = [
  ('timestamp',   lambda x: datetime.fromtimestamp(x).strftime('%b %d'), lambda x: datetime.fromtimestamp(x).strftime('%H:%M')),
  ('temperature', 'Temperature', lambda x: '%.1f°C' % x),
  ('humidity',    'Humidity',    lambda x: '%.0f%%' % x),
  ('pressure',    'Pressure',    lambda x: '%.0f mBar' % x)
]

class ImageFile:
  def __init__(self, path: str):
    assert os.path.isfile(path), f"{path} is not a file"

    m = _PATH_FORMAT.match(os.path.basename(path))
    assert m, f"{path} is not in the expected filename format"
    month, day, hour, minute, second = (int(s) for s in m.groups())

    self._datetime = datetime(datetime.today().year, month, day, hour, minute, second)
    self._path = path   
    self._out_path = path.replace('jpg', 'png')

  def datetime(self) -> datetime:
    """
    The `datetime` for this image
    """
    return self._datetime

  def out_path(self) -> str:
    """
    The output file path for this image
    """
    return self._out_path

  def overlay(self, data: dict):
    """
    Overlay the data in 'data' on the image
    """
    image = Image.open(self._path).convert('RGBA')
    text = Image.new('RGBA', image.size, (255,255,255,0))
    width = image.size[0]

    font = ImageFont.truetype('VeraBd.ttf', 40)
    draw = ImageDraw.Draw(text)

    x = width * 0.7
    y = 50
    for key, *cols in _TEXT_FORMATS:
      if key in data:
        cx = x
        for col in cols:
          txt = col(data[key]) if callable(col) else col
          draw.text((cx,y), txt, font=font, fill=(255,255,255,255))
          cx += width * 0.18

      y += 50

    out = Image.alpha_composite(image, text)
    out.save(self._out_path)    


def write_index_file(path: str, images: Iterable[ImageFile]):
  """
  Write an ffmpeg concat index file to 'path' for 'images'
  """
  with open(path, 'wt') as f:
    for image in images:
      f.write(f"file '{image.out_path()}'\nduration 0.25\n")


def parse_command_line_args():
  """
  Parse the command line arguments. Returns the args object
  """
  parser = argparse.ArgumentParser()
  
  parser.add_argument(
    'images',
    metavar='PATH',
    type=str,
    nargs='+',
    help='Images to process'
  )
  
  parser.add_argument(
    '--pirrigator',
    action='store',
    default='http://pirrigator:5000/api',
    help='Base URL for Pirrigator API'
  )

  parser.add_argument(
    '--index',
    action='store',
    help='Path to ffmpeg concat index file for image sequence'
  )

  return parser.parse_args()


if __name__ == "__main__":
  args = parse_command_line_args()
  images = [ImageFile(i) for i in args.images]
  start_time = min(i.datetime() for i in images)
  end_time = max(i.datetime() for i in images) + timedelta(minutes=10)

  client = PirrigatorClient(args.pirrigator)
  weather = client.weather(start_time, end_time)

  for i in images:
    if not os.path.isfile(i.out_path()):
      i.overlay(weather.at(i.datetime()))

  if args.index:
    images_in_date_order = sorted(images, key=ImageFile.datetime)
    write_index_file(args.index, images_in_date_order)
