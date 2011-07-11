pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null

pywatch "bash $SCRIPTPATH/runtests.sh" $SCRIPTPATH/../kardboard/*.py