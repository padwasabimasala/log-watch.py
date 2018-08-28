import re
import sys
import time
import argparse
from urllib.parse import urlparse

""" log-watch.py

  Tails a common log formatted file and reports useful statistics and alerts for high traffic.

  usage: log-watch.py [-h] [--stats-timer [STATS_TIMER]]
                    [--alerts-timer [ALERTS_TIMER]]
                    [--alerts-threshold [ALERTS_THRESHOLD]]
                    [--results [RESULTS]]
                    [file]

   positional arguments:
     file                  common log formated file to watch (default:
                           /var/log/access.log)
   
   optional arguments:
     -h, --help            show this help message and exit
     --stats-timer [STATS_TIMER], -s [STATS_TIMER] number seconds to wait before updating stats (default: 10)
     --alerts-timer [ALERTS_TIMER], -a [ALERTS_TIMER] number seconds to wait before updating alerts (default: 120)
     --alerts-threshold [ALERTS_THRESHOLD], -t [ALERTS_THRESHOLD] number of requests/per second to trigger an alert (default: 10)
     --results [RESULTS], -r [RESULTS] number of top sections to display stats for (default: 10)
"""

DEFAULT_LOG_FILE = '/var/log/access.log'
DEFAULT_STATS_TIMER_SECS = 10
DEFAULT_ALERT_TIMER_SECS = 120 
DEFAULT_ALERT_THRESHOLD = 10
DEFAULT_NUMBER_OF_RESULTS = 10

class Parser:
  """ Parse common log formatted string into dict """

  # https://gist.github.com/sumeetpareek/9644255
  parts = [
      r'(?P<host>\S+)',                   # host %h
      r'(?P<ident>\S+)',                  # ident %l
      r'(?P<user>\S+)',                   # user %u
      r'\[(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})\s+(?P<time>.+)\]',          # time %t
      r'"(?P<method>.*)\s+(?P<path>.*)\s+(?P<protocol>.*)"',               # request "%r"
      r'(?P<status>[0-9]+)',              # status %>s
      r'(?P<size>\S+)',                   # size %b (careful, can be '-')
      ]
  pattern = re.compile(r'\s+'.join(parts))

  @staticmethod
  def parse(line):
    """
    >>> Parser.parse("xyz") is None
    True
    >>> Parser.parse(r'155.80.44.115 - bobbyt [2015-09-02 11:58:49.801640] "GET /cms/2013/10/21/nftables HTTP/1.1" 200 475')
    {'host': '155.80.44.115', 'ident': '-', 'user': 'bobbyt', 'date': '2015-09-02', 'time': '11:58:49.801640', 'method': 'GET', 'path': '/cms/2013/10/21/nftables', 'protocol': 'HTTP/1.1', 'status': '200', 'size': '475', 'section': '/cms'}
    """  
    match = Parser.pattern.match(line)
    if match:
      d = match.groupdict()
      d['section'] = '/'.join(urlparse(d['path']).path.split('/')[0:2])
      return d
    return None

def tailf(fname):
  """ Tail file and yield each line """

  # https://agrrh.com/2018/tail-follow-in-python
  try:
      fp = open(fname, 'r')
  except IOError:
      print('Could not open file')
      sys.exit(1)

  fp.seek(0, 2)
  while True:
      line = fp.readline()
      if line:
          yield line.strip()

class SampleCollector:
  """
  Collect samples of parsed log data

  Calculate totals for requests, bytesout, and errors

  Rollup samples and store rollups until clear is called

  >>> scol = SampleCollector()
  >>> scol.collect(None)
  >>> scol.collect(dict(host='155.80.44.115', user='bobbyt', method='GET', status='200', size='75', section='/xyz'))
  >>> scol.collect(dict(host='155.80.44.115', user='bobbyt', method='GET', status='200', size='100', section='/cms'))
  >>> scol.collect(dict(host='155.80.44.115', user='bobbyt', method='GET', status='500', size='20', section='/cms'))
  >>> scol.rollup()
  [{'section': '/cms', 'requests': 2, 'bytesout': 120, 'errors': 1}, {'section': '/xyz', 'requests': 1, 'bytesout': 75, 'errors': 0}]
  >>> scol.collect(dict(host='155.80.44.115', user='bobbyt', method='GET', status='200', size='75', section='/xyz'))
  >>> scol.collect(dict(host='155.80.44.115', user='bobbyt', method='GET', status='200', size='100', section='/xyz'))
  >>> scol.collect(dict(host='155.80.44.115', user='bobbyt', method='GET', status='500', size='20', section='/cms'))
  >>> scol.rollup()
  [{'section': '/xyz', 'requests': 2, 'bytesout': 175, 'errors': 0}, {'section': '/cms', 'requests': 1, 'bytesout': 20, 'errors': 1}]
  >>> scol.rollups
  [[{'section': '/cms', 'requests': 2, 'bytesout': 120, 'errors': 1}, {'section': '/xyz', 'requests': 1, 'bytesout': 75, 'errors': 0}], [{'section': '/xyz', 'requests': 2, 'bytesout': 175, 'errors': 0}, {'section': '/cms', 'requests': 1, 'bytesout': 20, 'errors': 1}]]
  >>> scol.subtotal()
  {'requests': 6, 'bytesout': 390, 'errors': 2}
  >>> scol.totals
  {'requests': 6, 'bytesout': 390, 'errors': 2}
  >>> scol.clear()
  >>> scol.rollups
  []
  >>> scol.totals
  {'requests': 6, 'bytesout': 390, 'errors': 2}
  """
  def __init__(self):
    self.samples = []
    self.rollups = []
    self.totals = dict(requests=0, bytesout=0, errors=0)

  def collect(self, sample):
    if sample:
      self.samples.append(sample)

  def rollup(self):
    samples = self.samples.copy()
    self.samples = []
    rollup = self.__calc_rollup_and_totals(samples)
    self.rollups.append(rollup)
    return rollup

  def subtotal(self):
    subt = dict(requests=0, bytesout=0, errors=0)
    for rollup in self.rollups:
      for ru in rollup:
        for key in subt:
          subt[key] += ru[key]
    return subt

  def clear(self):
    self.rollups = []

  def __calc_rollup_and_totals(self, samples):
    all = {}
    for sample in samples:
      section = sample['section']
      if section in all.keys():
        ru = all[section]
      else:
        ru = dict(section=section, requests=0, bytesout=0, errors=0)
        all[section] = ru
      ru['requests'] += 1
      self.totals['requests'] += 1
      try:
        ru['bytesout'] += int(sample['size'])
        self.totals['bytesout'] += int(sample['size'])
      except ValueError:
        pass
      if sample['status'][0] == '5':
        ru['errors'] += 1
        self.totals['errors'] += 1
    res = sorted(all.values(), key=lambda rollup: rollup['requests'])
    res.reverse()
    return res

class Timer:
  """
  Simple timer

  >>> t = Timer(0.1)
  >>> t.is_done()
  False
  >>> time.sleep(0.1)
  >>> elapsed_time = t.is_done()
  >>> elapsed_time > 0.1 
  True
  >>> elapsed_time < 0.11
  True
  """

  def __init__(self, seconds):
    self.start = time.time()
    self.seconds = seconds

  def is_done(self):
    elapsed_time = time.time() - self.start
    if elapsed_time >= self.seconds:
      self.start = time.time()
      return elapsed_time
    return False

class Display:
  """ Write stats and alerts to the screen """

  def __init__(self, num_results):
    self.start_time = time.time()
    self.num_results = num_results

  def show_summary(self, rollup, totals):
    ave = self._reqs_ave(totals['requests'])
    print("Traffic Summary requests: {requests} ({ave} rps) bytes out: {bytesout} 500s: {errors}".format(**totals, **dict(ave=ave)))
    for ru in rollup[0:self.num_results]:
      print("{section} requests: {requests} bytes out: {bytesout} 500s: {errors}".format(**ru))

  def show_alert(self, value):
    print("High traffic generated an alert - hits = {0}, triggered at {1}".format(int(value), self._curtime()))

  def show_alert_resolution(self, value):
    print("High traffic recovered at {0}".format(self._curtime()))

  def _reqs_ave(self, reqs):
    return int(reqs / (time.time() - self.start_time))

  def _curtime(self):
    return time.strftime("%H:%M:%S",time.localtime(time.time()))

class HighTrafficMonitor():
  """
  Trigger alert and resolve callbacks when threshold reached or resolved

  >>> htm = HighTrafficMonitor(threshold=10, alert=lambda x: print("Alert %s" % x), resolve=lambda x: print("Resolved"))
  >>> htm.check(1)
  >>> htm.check(11)
  Alert 11
  >>> htm.check(12)
  Alert 12
  >>> htm.check(1)
  Resolved
  """

  def __init__(self, threshold, alert, resolve):
    self._active = False
    self.threshold = threshold
    self.alert = alert
    self.resolve = resolve

  def check(self, value):
    if value > self.threshold:
      self._active = True
      self.alert(value)
    else:
      if self._active:
        self._active = False
        self.resolve(value)

def main(args):
  """ main loop """

  col = SampleCollector()
  display = Display(args.results)
  alerts_timer = Timer(args.stats_timer)
  alert_timer = Timer(args.alerts_timer)
  htm = HighTrafficMonitor(threshold=args.alerts_threshold, alert=display.show_alert, resolve=display.show_alert_resolution)

  for line in tailf(args.file):
      samples = Parser.parse(line)
      col.collect(samples)
      if alerts_timer.is_done():
        rollup = col.rollup()
        display.show_summary(rollup, col.totals)
        elapsed_time = alert_timer.is_done()
        if elapsed_time: 
          htm.check(col.subtotal()['requests']/elapsed_time)
          col.clear()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('file', nargs='?', help="common log formated file to watch", default=DEFAULT_LOG_FILE)
  parser.add_argument('--stats-timer', '-s', nargs='?', help="number seconds to wait before updating stats", default=DEFAULT_STATS_TIMER_SECS, type=int)
  parser.add_argument('--alerts-timer', '-a', nargs='?', help="number seconds to wait before updating alerts", default=DEFAULT_ALERT_TIMER_SECS, type=int)
  parser.add_argument('--alerts-threshold', '-t', nargs='?', help="number of requests/per second to trigger an alert", default=DEFAULT_ALERT_THRESHOLD, type=int)
  parser.add_argument('--results', '-r', nargs='?', help="number of top sections to display stats for", default=DEFAULT_NUMBER_OF_RESULTS, type=int)
  args = parser.parse_args()
  main(args)
