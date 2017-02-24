Tornado_s3 - Tornado client for AWS S3
======================================

This is based on:

https://gist.github.com/nanvel/c489761a11ec2db184c5

and:

http://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html

The code has been modified to work with Python3. I used this to handle
some user uploaded small binaries (can fit into memory) to the server.

Command line testing tool
-------------------------

python -m tornado_s3.cmdline --help

Tornado Example
---------------

TODO
