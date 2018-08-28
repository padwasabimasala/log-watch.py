# log-watch.py

Tails a common log formatted file and reports useful statistics and alerts for high traffic.

## Usage

`log-watch.py [file]`

## Options

```
log-watch.py --help

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
```

## Docker build

`docker build -t log-watch .`

## License

Other authors works copy right the original author.

MIT
