#!/bin/sh
code_path=~/Code/kardboard
cd $code_path
gitx $code_path

tmux start-server
tmux new-session -d -s kardboard -n git
tmux new-window -tkardboard:1 -n tests
tmux new-window -tkardboard:2 -n shell
tmux new-window -tkardboard:3 -n runserver
tmux new-window -tkardboard:4 -n mongo

tmux send-keys -tkardboard:4 'workon kardboard; cd $code_path; rm var/*; bash runmongo.sh' C-m
tmux send-keys -tkardboard:3 'workon kardboard; cd $code_path; python kardboard/runserver.py' C-m
tmux send-keys -tkardboard:2 'workon kardboard; cd $code_path;' C-m
tmux send-keys -tkardboard:1 'workon kardboard; cd $code_path; bash ci.sh' C-m
tmux send-keys -tkardboard:0 'workon kardboard; cd $code_path; clear' C-m

tmux select-window -tkardboard:0
tmux attach-session -d -tkardboard