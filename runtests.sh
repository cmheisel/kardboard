clear
./run-pyflakes.py kardboard
if [ "$?" -eq "0" ]
then
    python kardboard/tests.py
fi