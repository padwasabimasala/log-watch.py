import re
import sys
import time

# https://gist.github.com/sumeetpareek/9644255
class Parser:
  parts = [
      r'(?P<host>\S+)',                   # host %h
      r'(?P<ident>\S+)',                  # ident %l
      r'(?P<user>\S+)',                   # user %u
      r'\[(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})\s+(?P<time>.+)\]',          # time %t
      r'"(?P<method>.*)\s+(?P<path>.*)\s+(?P<protocol>.*)"',               # request "%r"
      r'(?P<status>[0-9]+)',              # status %>s
      r'(?P<size>\S+)',                   # size %b (careful, can be '-')
      r'"(?P<referrer>.*)"',              # referrer "%{Referer}i"
      r'"(?P<agent>.*)"',                 # user agent "%{User-agent}i"
      ]
  pattern = re.compile(r'\s+'.join(parts))

  @staticmethod
  def parse(line):
    """
    >>> Parser.parse("xyz") is None
    True
    >>> Parser.parse(r'155.80.44.115 IT - [2015-09-02 11:58:49.801640] "GET /cms/2013/10/21/nftables-to-replace-iptables-firewall-facility-in-upcoming-linux-kernel/feed/ HTTP/1.1" 200 475 "-" "Mozilla/5.0 (compatible; MJ12bot/v1.4.5; http://www.majestic12.co.uk/bot.php?+)" www.example.com 124.165.3.7 443 redirect-handler - + "-" VebIWcCoAwcAADRbdGsAAAAD TLSv1 AES256-SHA 501 1007 -% 23735 833 0 0 0 0') == {'host': '155.80.44.115', 'ident': 'IT', 'user': '-', 'date': '2015-09-02', 'time': '11:58:49.801640', 'method': 'GET', 'path': '/cms/2013/10/21/nftables-to-replace-iptables-firewall-facility-in-upcoming-linux-kernel/feed/', 'protocol': 'HTTP/1.1', 'status': '200', 'size': '475', 'referrer': '-', 'agent': 'Mozilla/5.0 (compatible; MJ12bot/v1.4.5; http://www.majestic12.co.uk/bot.php?+)" www.example.com 124.165.3.7 443 redirect-handler - + "-'}
    True
    """  
    match = Parser.pattern.match(line)
    if match:
      return match.groupdict()
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
        time.sleep(0.001)

# 0. Consume an actively written-to w3c-formatted HTTP access log
# (https://en.wikipedia.org/wiki/Common_Log_Format). 
# Example: 127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "GET /api/user HTTP/1.0" 200 1234
# - It should default to reading /var/log/access.log 
# - and be overridable
#
# 1. Display stats every 10s about the traffic during those 10s: 
# - the sections of the web site with the most hits
# - interesting summary statistics on the traffic as a whole. 
# 
#   A section is defined as being what's before the second '/' in the path. 
#   For example, the section for "http://my.site.com/pages/create” is
#   "http://my.site.com/pages". 
#
# 2. Make sure a user can keep the app running and monitor the log file continuously 
#
# Whenever total traffic for the past 2 minutes exceeds a certain number on average, add
# a message saying that “High traffic generated an alert - hits = {value},
# triggered at {time}”. 
# - The default threshold should be 10 requests per second
# - it should be overridable.  
# 
# 3. Whenever the total traffic drops again below that value on average for the
# past 2 minutes, print or displays another message detailing when the alert
# recovered.  
#
# 4. Write a test for the alerting logic.

#
# file = arg || default
# stats_interval = arg || default
# traffic_interval = arg || default
# 
# stats_timer = traffic_timer = now
# for line in tail(file):
#   stats = parse(line)
#   collect(stats)
#   if now - stats_timer >= stats_interval:
#     print_stats
#     stats_timer = now
#   if now - traffic_timer >= traffic_interval:
#     print_alerts
#     traffic_time = now
#     clear_stats

if __name__ == '__main__':
    try:
        fname = sys.argv[1]
    except IndexError:
        print('File not specified')
        sys.exit(1)

    for line in tailf(fname):
        d = Parser.parse(line)
        print(d)
