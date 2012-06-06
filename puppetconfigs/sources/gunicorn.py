import multiprocessing

bind = "127.0.0.1:4000"
logfile = "/home/kardboard/logs/kardboard-gunicorn.log"
loglevel = "info"
workers = 3
debug = False
daemon = False
pidfile = '/tmp/gunicorn.pid'
worker_class = "sync"

backlog = 2048
timeout = 30
keepalive = 2

user = "kardboard"
