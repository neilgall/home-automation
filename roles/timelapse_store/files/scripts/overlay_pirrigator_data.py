import argparse
import os
import re
from datetime import datetime, timedelta
from PIL import Image
from pirrigator_client import PirrigatorClient
from text_writer import *
from typing import Iterable


_PATH_FORMAT = re.compile(r'img(\d\d)(\d\d)(\d\d)(\d\d)(\d\d).jpg')
_ORIGIN = (0.7, 0.05)
_CELL_SIZE = (0.18, 0.05)

_TEXT_OVERLAYS = [
  DateTimeOverlay(),
  DataOverlay("temperature", "Temperature", '%.1f°C'),
  DataOverlay('humidity',    'Humidity',    '%.0f%%'),
  DataOverlay('pressure',    'Pressure',    '%.0f mBar')
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

  def overlay(self, data: dict):
    """
    Overlay the data in 'data' on the image
    """
    writer = TextWriter(Image.open(self._path), _ORIGIN, _CELL_SIZE)

    for y, overlay in enumerate(_TEXT_OVERLAYS):
      overlay.draw(writer, 0, y, data)

    self._composite = writer.composite()
    return self

  def show(self):
    """
    Show the composite image
    """
    self._composite.show()

  def save(self) -> str:
    """
    Write the composite image, returning the output file path
    """
    self._composite.save(self._out_path)
    return self._out_path


def write_index_file(path: str, paths: Iterable[str]):
  """
  Write an ffmpeg concat index file to 'path' for 'images'
  """
  with open(path, 'wt') as f:
    for path in paths:
      f.write(f"file '{path}'\nduration 0.25\n")


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
    '--show',
    action='store_true',
    help='Show the first processed image instead of writing to disk'
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
    default='/tmp/index.txt',
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

  if args.show:
    images[0].overlay(weather.at(images[0].datetime())).show()
  else:
    images_in_date_order = sorted(images, key=ImageFile.datetime)
    composite_images = (i.overlay(weather.at(i.datetime())).save() for i in images)
    write_index_file(args.index, composite_images)
