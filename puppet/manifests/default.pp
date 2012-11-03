# Set global package provider
Package { provider => 'aptitude' }

#################### Imports
include mongodb

mongodb::setup { "kardboard": }