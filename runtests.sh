clear
python kardboard/tests.py
if [ "$?" -eq "0" ]
then
    ./run-pyflakes.py kardboard
fi