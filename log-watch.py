import re
import sys
import time
from urllib.parse import urlparse

# https://gist.github.com/sumeetpareek/9644255
class Parser:
  # host ident authuser date request status bytes
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
    >>> Parser.parse(r'155.80.44.115 - bobbyt [2015-09-02 11:58:49.801640] "GET /cms/2013/10/21/nftables HTTP/1.1" 200 475') == {'host': '155.80.44.115', 'ident': '-', 'user': 'bobbyt', 'date': '2015-09-02', 'time': '11:58:49.801640', 'method': 'GET', 'path': '/cms/2013/10/21/nftables', 'protocol': 'HTTP/1.1', 'status': '200', 'size': '475', 'section': '/cms'}
    True
    """  
    match = Parser.pattern.match(line)
    if match:
      d = match.groupdict()
      d['section'] = '/'.join(urlparse(d['path']).path.split('/')[0:2])
      return d
    return None

# https://agrrh.com/2018/tail-follow-in-python
def tailf(fname):
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
        #time.sleep(0.001)

# [x] 0. Consume an actively written-to w3c-formatted HTTP access log
# (https://en.wikipedia.org/wiki/Common_Log_Format). 
# Example: 127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "GET /api/user HTTP/1.0" 200 1234
# [x] - It should default to reading /var/log/access.log 
# [x] - and be overridable
#
# [ ] 1. Display stats every 10s about the traffic during those 10s: 
# [x] - the sections of the web site with the most hits
# [ ] - interesting summary statistics on the traffic as a whole. 
# 
#   A section is defined as being what's before the second '/' in the path. 
#   For example, the section for "http://my.site.com/pages/create” is
#   "http://my.site.com/pages". 
#
# [x] 2. Make sure a user can keep the app running and monitor the log file continuously 
#
# [ ] 3. Whenever total traffic for the past 2 minutes exceeds a certain number on average, add
# a message saying that “High traffic generated an alert - hits = {value},
# triggered at {time}”. 
# [ ] - The default threshold should be 10 requests per second
# [ ] - it should be overridable.  
# 
# [ ] 4. Whenever the total traffic drops again below that value on average for the
# past 2 minutes, print or displays another message detailing when the alert
# recovered.  
#
# [ ] 5. Write a test for the alerting logic.

# Notes/
# Section size could be configured
# sleep could be configured or null
# timer in another thread?
# run profiler

class StatsCollector:
  """
  >>> scol = StatsCollector()
  >>> scol.collect(dict(section= '/abc'))
  >>> scol.collect(dict(section= '/abc'))
  >>> scol.collect(dict(section= '/xyz'))
  >>> scol.stats
  {'/abc': 2, '/xyz': 1}
  """
  def __init__(self):
    self.stats = {}

  def collect(self, stats):
    try:
      self.stats[stats['section']] += 1
    except KeyError:
      self.stats[stats['section']] = 1


DEFAULT_LOG_FILE = '/var/log/access.log'
DEFAULT_STATS_INTERVAL = 10
DEFAULT_TRAFFIC_INTERVAL = 120 
DEFAULT_HIGH_TRAFFIC_THRESHOLD = 10

class Timer:
  """
  >>> t = Timer(1, lambda t: print("Times up"))
  >>> t.check(time.time())
  >>> t.check(time.time()+5)
  Times up
  """

  def __init__(self, seconds, callback):
    self.start = time.time()
    self.seconds = seconds
    self.callback = callback

  def check(self, curtime):
    elapsed_time = curtime - self.start
    if elapsed_time >= self.seconds:
      self.start = time.time()
      self.callback(elapsed_time)

class HighTrafficAlert:
  # req/secs
  """
  >>> cur_time = 1535088782.4119601
  >>> hta = HighTrafficAlert(10)
  >>> hta.check(10, 100, cur_time)
  >>> hta.check(600, 60, cur_time)
  High traffic generated an alert - hits = 10.0, triggered at 23:33:02
  >>> hta.check(1400, 70, cur_time)
  High traffic generated an alert - hits = 20.0, triggered at 23:33:02
  >>> hta.check(140, 70, cur_time)
  High traffic recovered at 23:33:02
  >>> hta.check(140, 70, cur_time)
  >>> hta.check(140, 70, cur_time)
  >>> hta.check(1400, 70, cur_time)
  High traffic generated an alert - hits = 20.0, triggered at 23:33:02
  """

  warning = "High traffic generated an alert - hits = {value}, triggered at {time}"
  recovery = "High traffic recovered at {time}"

  def fmt_time(self, t):
    return time.strftime("%H:%M:%S",time.localtime(t))

  def __init__(self, threshold):
    self.threshold = threshold
    self.switch = False

  def check(self, reqs, elapsed_time, cur_time):
    reqs_per_sec = (reqs / elapsed_time)
    if reqs_per_sec >= self.threshold:
      self.switch = True
      print(self.warning.format(**dict(value=reqs_per_sec, time=self.fmt_time(cur_time))))
    else:
      if self.switch:
        print(self.recovery.format(**dict(time=self.fmt_time(cur_time))))
      self.switch = False
  

def main(fname):
  col = StatsCollector()
  stats_timer = Timer(1, lambda t: print(col.stats))
  traffic_timer = Timer(5, lambda t: print(col.stats))

  for line in tailf(fname):
      d = Parser.parse(line)
      if d:
        col.collect(d)
      now = time.time()
      stats_timer.check(now)
      traffic_timer.check(now)

if __name__ == '__main__':
  try:
      fname = sys.argv[1]
  except IndexError:
      fname = DEFAULT_LOG_FILE

  #import profile
  #profile.run("main()")
  main(fname)
