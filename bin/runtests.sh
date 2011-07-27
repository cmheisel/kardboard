pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null

clear
$SCRIPTPATH/run-pyflakes.py ../kardboard
if [ "$?" -eq "0" ]
then
    python $SCRIPTPATH/../kardboard/tests.py
fi