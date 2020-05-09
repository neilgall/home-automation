import argparse
import os
import logging
import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from PIL import Image
from pirrigator_client import PirrigatorClient
from text_writer import *
from typing import Iterable

logging.basicConfig(level=logging.INFO)


_PATH_FORMAT = re.compile(r'img(\d\d)(\d\d)(\d\d)(\d\d)(\d\d).jpg')
_MIN_BRIGHTNESS = 0.075

_WEATHER_X1 = 0.65
_WEATHER_X2 = 0.83

_WEATHER_OVERLAYS = [
  DateTimeOverlay(_WEATHER_X1, _WEATHER_X2, 0.05),
  LabelledDataOverlay(_WEATHER_X1, _WEATHER_X2, 0.10, "temperature", "Temperature", '%.1f°C'),
  LabelledDataOverlay(_WEATHER_X1, _WEATHER_X2, 0.15, 'humidity',    'Humidity',    '%.0f%%'),
  LabelledDataOverlay(_WEATHER_X1, _WEATHER_X2, 0.20, 'pressure',    'Pressure',    '%.0f mBar'),
]

_MOISTURE_OVERLAYS = {
  'Cucumbers': PlainDataOverlay(0.50, 0.60, 'value', '%d'),
  'Yellow Pigmy': PlainDataOverlay(0.37, 0.65, 'value', '%d'),
  'Vintage Wine': PlainDataOverlay(0.33, 0.90, 'value', '%d')
}


class ImageFile:
  def __init__(self, path: str):
    assert os.path.isfile(path), f"{path} is not a file"

    m = _PATH_FORMAT.match(os.path.basename(path))
    assert m, f"{path} is not in the expected filename format"
    month, day, hour, minute, second = (int(s) for s in m.groups())

    self._datetime = datetime(datetime.today().year, month, day, hour, minute, second)
    self._image = Image.open(path)
    self._out_path = path.replace('jpg', 'png')

  def datetime(self) -> datetime:
    """
    The `datetime` for this image
    """
    return self._datetime

  def brightness(self) -> float:
    """
    Get an overall measure of brightness for this image, where
    0.0 = completely dark and 1.0 = completely white
    """
    histogram = self._image.convert('L').histogram()
    total = sum(histogram)
    weighted = sum(i * j for i,j in enumerate(histogram)) / 255.0
    return weighted / total

  @contextmanager
  def overlay(self):
    """
    Overlay the data in 'data' on the image
    """
    writer = TextWriter(self._image)
    yield writer
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


class OverlayData:
  """
  Holds all the time series data and uses this to draw over each
  image supplied
  """
  def __init__(self, client: PirrigatorClient, start_time: datetime, end_time: datetime):
    self._weather = client.weather_history(start_time, end_time)
    self._moisture = { 
      sensor: client.moisture_history(sensor, start_time, end_time) 
      for sensor in _MOISTURE_OVERLAYS.keys()
    }

  def draw(self, image: Image):
    """
    Overlay the data for 'image'
    """
    t = image.datetime()
    logging.info(f'Processing {t}...')

    with image.overlay() as writer:
      for overlay in _WEATHER_OVERLAYS:
        overlay.draw(writer, self._weather.at(t))

      for sensor, overlay in _MOISTURE_OVERLAYS.items():
        overlay.draw(writer, self._moisture[sensor].at(t))

    return image


if __name__ == "__main__":
  args = parse_command_line_args()
  images = [ImageFile(i) for i in args.images]
  start_time = min(i.datetime() for i in images)
  end_time = max(i.datetime() for i in images) + timedelta(minutes=10)

  client = PirrigatorClient(args.pirrigator)
  data = OverlayData(client, start_time, end_time)

  if args.show:
    data.draw(images[0]).show()

  else:
    images_in_date_order = sorted(images, key=ImageFile.datetime)
    composite_images = (data.draw(i).save() for i in images if i.brightness() > _MIN_BRIGHTNESS)
    write_index_file(args.index, composite_images)
