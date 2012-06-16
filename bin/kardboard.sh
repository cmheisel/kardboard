#!/bin/sh
export code_path=~/Code/kardboard
export conf_path=~/Code/kardconfig
cd $code_path
tmux_cmd='tmux -vvv'
export KARDBOARD_SETTINGS=$conf_path/sources/kardboard-prod.cfg
export NR_INI=$conf_path/sources/newrelic.ini
mkdir -p $code_path/var

tmux start-server
tmux new-session -d -skardboard -n conf
tmux new-window -tkardboard:1 -n git
tmux new-window -tkardboard:2 -n tests
tmux new-window -tkardboard:3 -n runserver
tmux new-window -tkardboard:4 -n celery
tmux new-window -tkardboard:5 -n mongo
tmux new-window -tkardboard:6 -n cache
tmux new-window -tkardboard:7 -n queue

tmux send-keys -t kardboard:0 "workon kardboard; cd $conf_path; git checkout local;"
tmux send-keys -t kardboard:0 "Enter"

tmux send-keys -t kardboard:1 "cd $code_path; workon kardboard; "
tmux send-keys -t kardboard:1 "Enter"

tmux send-keys -t kardboard:2 'cd $code_path; workon kardboard; tdaemon --ignore-dirs=var'
tmux send-keys -t kardboard:2 "Enter"


# Have to start services before we start the server/daemons
tmux send-keys -t kardboard:6 'memcached -v'
tmux send-keys -t kardboard:6 "Enter"

# Have to start services before we start the server/daemons
tmux send-keys -t kardboard:7 'redis-server /usr/local/etc/redis.conf'
tmux send-keys -t kardboard:7 "Enter"

tmux send-keys -t kardboard:5 "cd $code_path; bash bin/runmongo.sh"
tmux send-keys -t kardboard:5 "Enter"

tmux send-keys -t kardboard:4 'cd $code_path; workon kardboard;'
tmux send-keys -t kardboard:4 "Enter"
tmux send-keys -t kardboard:4 'python kardboard/manage.py celeryd --purge -B --schedule=./var/celerybeat-schedule.db'

tmux send-keys -t kardboard:3 'cd $code_path; workon kardboard;'
tmux send-keys -t kardboard:3 "Enter"
tmux send-keys -t kardboard:3 'python kardboard/runserver.py'
tmux send-keys -t kardboard:3 "Enter"


tmux select-window -t kardboard:2
tmux attach-session -t kardboard