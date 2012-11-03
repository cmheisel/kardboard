# Set global package provider
Package { provider => 'aptitude' }

#################### Imports
include mongodb
include git

mongodb::setup { "kardboard": }