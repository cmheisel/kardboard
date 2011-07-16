pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null
mongod -vv --dbpath=$SCRIPTPATH/../var/