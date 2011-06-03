kanboard_path=`dirname "$0"`
cd $kanboard_path
mongod -vv --dbpath=$kanboard_path/var/