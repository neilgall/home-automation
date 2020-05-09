import logging
import requests
from datetime import date, datetime, time, timedelta, timezone
from munch import munchify, Munch


def _int_ts(dt: datetime) -> int:
  """
  Get an integer timestamp from `dt`
  """
  return int(dt.timestamp())


class TimeSeries:
  """
  A time series group of records
  """
  def __init__(self, records):
    self._records = munchify(list(dict(d) for d in records))

  def at(self, dt: datetime) -> Munch:
    """
    Get the record closest in time to 'dt'
    """
    if len(self._records) > 0:
      timestamp = _int_ts(dt)
      return min(self._records, key=lambda r: abs(timestamp - r['unix_time']))
    else:
      return {}

  def __str__(self):
    return str(sorted(self._records, key=lambda r: r['unix_time']))


class PirrigatorClient:
  """
  A client for the Pirrigator API
  """
  def __init__(self, base_url: str):
    self._base = base_url

  def _apicall(self, url: str):
    logging.debug(f'GET {url}')
    rsp = requests.get(f'{self._base}{url}')
    json = rsp.json()
    logging.debug(f'{rsp.status_code} {json}')
    return json

  def zones(self):
    """
    Get the list of configured zone names
    """
    return munchify(self._apicall('/zone/list'))

  def moisture_sensors(self):
    """
    Get the list of moisture sensor names, suitable as values
    for the 'sensor' parameter of 'moisture()'
    """
    return munchify(self._apicall('/moisture/sensors'))

  def weather_history(self, start: datetime, end: datetime) -> TimeSeries:
    """
    Get all weather records between 'start' and 'end' as a 'TimeSeries'
    """
    return TimeSeries(self._apicall(f'/weather/{_int_ts(start)}/{_int_ts(end)}'))

  def moisture_history(self, sensor: str, start: datetime, end: datetime) -> TimeSeries:
    """
    Get all moisture records between 'start' and 'end' as a 'TimeSeries'
    """
    data = self._apicall(f'/moisture/{sensor}/{_int_ts(start)}/{_int_ts(end)}')
    return TimeSeries({ 'unix_time': r[0], 'value': r[1] } for r in data)

  def irrigation_history(self, zone: str, start: datetime, end: datetime) -> TimeSeries:
    """
    Get all the irrigation records between 'start' and 'end' as a 'TimeSeries'
    """
    data = self._apicall(f'/zone/{zone}/irrigation/{_int_ts(start)}/{_int_ts(end)}')
    return TimeSeries({ 'unix_time': r[0], 'duration': r[1]['secs'] } for r in data)


if __name__ == "__main__":
  import sys
  t = "12:00" if len(sys.argv) < 2 else sys.argv[1]
  h,m = (int(x) for x in t.split(':', maxsplit=1))
  time = datetime.combine(date.today(), time(hour=h, minute=m), timezone.utc)

  logging.basicConfig(level=logging.DEBUG)

  p = PirrigatorClient('http://pirrigator:5000/api')
  hour = timedelta(seconds=3600)
  print(p.weather_history(time - hour, time + hour).at(time))

  for s in p.moisture_sensors():
    print(s, p.moisture_history(s, time - hour, time + hour).at(time))

  for z in p.zones():
    print(z, p.irrigation_history(s, time - hour, time + hour))
