# At Datadog, we value working on real solutions to real problems, and as such we
# think the best way to understand your capabilities is to give you the
# opportunity to solve a problem similar to the ones we solve on a daily basis.
# As the next step in our process, we ask that you write a simple console program
# that monitors HTTP traffic on your machine. Treat this as an opportunity to
# show us how you would write something you would be proud to put your name on.
# Feel free to impress us.
# 
# Consume an actively written-to w3c-formatted HTTP access log
# (https://en.wikipedia.org/wiki/Common_Log_Format). It should default to reading
# /var/log/access.log and be overridable.  Example log lines:
# 
# ```
# 
# 127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 1234
# 
# 127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 1234
# 
# 127.0.0.1 - frank [09/May/2018:16:00:42 +0000] "GET /api/user HTTP/1.0" 200 1234
# 
# 127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "GET /api/user HTTP/1.0" 200 1234
# 
# ```
# 
# Display stats every 10s about the traffic during those 10s: the sections of
# the web site with the most hits, as well as interesting summary statistics on
# the traffic as a whole. A section is defined as being what's before the
# second '/' in the path. For example, the section for
# "http://my.site.com/pages/create” is "http://my.site.com/pages".  Make sure a
# user can keep the app running and monitor the log file continuously Whenever
# total traffic for the past 2 minutes exceeds a certain number on average, add
# a message saying that “High traffic generated an alert - hits = {value},
# triggered at {time}”. The default threshold should be 10 requests per second
# and should be overridable.  Whenever the total traffic drops again below that
# value on average for the past 2 minutes, print or displays another message
# detailing when the alert recovered.  Write a test for the alerting logic.

# 127.0.0.1 user-identifier frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
# https://raw.githubusercontent.com/Apache-Labor/labor/master/labor-04/labor-04-example-access.log

file = open('labor-04-example-access.log', 'r')
file = open('short.log', 'r')

# https://gist.github.com/sumeetpareek/9644255
# pattern.match(line).groupdict()
# Regex for the common Apache log format.
import re

# 9.184.11.34 - - [12/Dec/2015:18:32:56 +0100] "GET /administrator/ HTTP/1.1" 200 4263 "-" "Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0" "-"
# 109.184.11.34 - - [12/Dec/2015:18:32:56 +0100] "POST /administrator/index.php HTTP/1.1" 200 4494 "http://almhuette-raith.at/administrator/" "Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0" "-"
parts = [
    r'(?P<host>\S+)',                   # host %h
    r'(?P<ident>\S+)',                  # ident %l
    r'(?P<user>\S+)',                   # user %u
    r'\[(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})\s+(?P<time>.+)\]',                # time %t
    r'"(?P<method>.*)\s+(?P<path>.*)\s+(?P<protocol>.*)"',               # request "%r"
    r'(?P<status>[0-9]+)',              # status %>s
    r'(?P<size>\S+)',                   # size %b (careful, can be '-')
    r'"(?P<referrer>.*)"',              # referrer "%{Referer}i"
    r'"(?P<agent>.*)"',                 # user agent "%{User-agent}i"
    ]
pattern = re.compile(r'\s+'.join(parts))

for line in file:
  print()
  print (line)
  match = pattern.match(line)
  if match:
    d = match.groupdict()
    print(d)
