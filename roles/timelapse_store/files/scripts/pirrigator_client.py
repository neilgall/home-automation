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
    self._records = [munchify({**r, 'timestamp': int(r.timestamp.secs_since_epoch)}) for r in records]

  def at(self, dt: datetime) -> Munch:
    """
    Get the record closest in time to 'dt'
    """
    if self._records:
      timestamp = _int_ts(dt)
      return min(self._records, key=lambda r: abs(timestamp - r['timestamp']))
    else:
      return {}


class PirrigatorClient:
  """
  A client for the Pirrigator API
  """
  def __init__(self, base_url: str):
    self._base = base_url

  def weather(self, start: datetime, end: datetime) -> TimeSeries:
    """
    Get all weather records between 'start' and 'end' as a 'TimeSeries'
    """
    data = munchify(requests.get(f"{self._base}/weather/{_int_ts(start)}/{_int_ts(end)}").json())
    return TimeSeries(data)


if __name__ == "__main__":
  import sys
  t = "12:00" if len(sys.argv) < 2 else sys.argv[1]
  h,m = (int(x) for x in t.split(':', maxsplit=1))
  time = datetime.combine(date.today(), time(hour=h, minute=m), timezone.utc)

  p = PirrigatorClient('pirrigator', 5000)
  hour = timedelta(seconds=3600)
  print(p.weather(time - hour, time + hour).at(time))
