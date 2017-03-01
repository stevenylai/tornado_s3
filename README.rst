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

An example handler would roughly look like below

.. code-block:: python

  class Handler(web.RequestHandler):
      def initialize(self, **kwargs):
          self.client = tornado_s3.S3Client(**kwargs)

      @gen.coroutine
      def post(self, path):
          fileinfo = self.request.files['upload'][0]
          name = fileinfo['filename']
          data = fileinfo['body']
          resp = yield self.client.put(path + '/' + name, data)
          self.set_status(resp.code)
          self.write(resp.body)

      @gen.coroutine
      def get(self, path, include_body=True):
          resp = yield self.client.get(
              path, method='GET' if include_body else 'HEAD'
          )
          self.set_status(resp.code)
          if include_body:
              self.write(resp.body)
          for key, value in resp.headers.get_all():
              self.add_header(key, value)

      def head(self, path):
          return self.get(path, False)

      @gen.coroutine
      def delete(self, path):
          resp = yield self.client.get(path, method='DELETE')
          self.set_status(resp.code)
          self.write(resp.body)
