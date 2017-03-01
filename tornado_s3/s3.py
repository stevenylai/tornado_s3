"""
Async Tornado S3 uploader with AWS4 sign.
Original code: https://gist.github.com/stalkerg/63bad3ea49be6268df49

Edited by @nanvel 2015-07-24

Usage example:

.. code-block:: python

    client = S3Client(
        access_key=options.AWS_ACCESS_KEY, secret_key=options.AWS_SECRET_KEY,
        bucket=options.S3_BUCKET, region=options.AWS_REGION)

    response = yield client.upload(path=path, data=stream, headers={
        'X-Amz-Acl': 'public-read',
    })

"""
import hashlib
import hmac
import mimetypes
import datetime
from calendar import timegm
from email.utils import formatdate
from urllib import parse
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient, HTTPError
AWS_S3_BUCKET_URL = 'http://{bucket}.s3.amazonaws.com/{path}'
AWS_S3_CONNECT_TIMEOUT = 10
AWS_S3_REQUEST_TIMEOUT = 30


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(key, datestamp, region, service):
    k_date = sign(('AWS4' + key).encode('utf-8'), datestamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing


class S3Client(object):
    """ AWS client that handles asynchronous uploads to S3 buckets """

    def __init__(self, access_key=None, secret_key=None, bucket=None,
                 region="eu-central-1"):

        super(S3Client, self).__init__()
        self._access_key = access_key
        self._secret_key = secret_key
        self.bucket = bucket
        self._region = region
        self._service = 's3'
        self._request_scope = 'aws4_request'
        self._algorithm = 'AWS4-HMAC-SHA256'

    def generate_url(self, path):
        """ Generates a URL for the given file path. """
        return AWS_S3_BUCKET_URL.format(bucket=self.bucket, path=path)

    def _guess_mimetype(self, filename, default="application/octet-stream"):
        """
        Guess mimetype from file name
        """
        if "." not in filename:
            return default

        prefix, extension = filename.lower().rsplit(".", 1)

        if extension == "jpg":
            extension = "jpeg"

        return mimetypes.guess_type(prefix + "." + extension)[0] or default

    def _rfc822_datetime(self, t=None):
        """ Generate date in RFC822 format """

        if t is None:
            t = datetime.datetime.utcnow()

        return formatdate(timegm(t.timetuple()), usegmt=True)

    def get_credential_scope(self, request_date):
        return (
            request_date.strftime('%Y%m%d') + '/' +
            self._region + '/' +
            self._service + '/' +
            self._request_scope
        )

    def get_canonical_request(self, request_date, host, endpoint, headers,
                              method, params=None, payload=None):
        """ Method used to obtain the canonical string used to sign the
        aws request.
        """
        payload = payload or b''
        canonical_uri = endpoint
        canonical_querystring = (
            parse.urlencode(params) if params is not None else ''
        )
        headers['Host'] = host
        headers['x-amz-date'] = request_date.strftime('%Y%m%dT%H%M%SZ')
        headers['x-amz-content-sha256'] = hashlib.sha256(payload).hexdigest()

        lowered_headers = {
            key.lower(): value.strip() for key, value in headers.items()
        }
        # create canonical headers
        canonical_headers = [
            key + ':' + lowered_headers[key]
            for key in sorted(lowered_headers.keys())
        ]
        canonical_headers = '\n'.join(canonical_headers) + '\n'

        # create signed headers
        signed_headers = [key for key in sorted(lowered_headers.keys())]
        signed_headers = ';'.join(signed_headers)

        payload_hash = hashlib.sha256(payload).hexdigest()
        return signed_headers, (
            method + '\n' +
            canonical_uri + '\n' +
            canonical_querystring + '\n' +
            canonical_headers + '\n' +
            signed_headers + '\n' +
            payload_hash
        )

    def sign_request(self, host, endpoint, headers, method,
                     params=None, payload=None):
        """Sign request"""
        request_date = datetime.datetime.utcnow()
        signed_headers, canonical_request = self.get_canonical_request(
            request_date, host, endpoint, headers, method, params, payload
        )
        string_to_sign = (
            self._algorithm + '\n' +
            request_date.strftime('%Y%m%dT%H%M%SZ') + '\n' +
            self.get_credential_scope(request_date) + '\n' +
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        )
        signing_key = get_signature_key(
            self._secret_key, request_date.strftime('%Y%m%d'),
            self._region, self._service
        )
        signature = hmac.new(
            signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256
        ).hexdigest()
        authorization_header = (
            self._algorithm + ' ' +
            'Credential=' + self._access_key +
            '/' + self.get_credential_scope(request_date) + ', ' +
            'SignedHeaders=' + signed_headers + ', ' +
            'Signature=' + signature
        )
        auth_header = {
            'x-amz-date': request_date.strftime('%Y%m%dT%H%M%SZ'),
            'Authorization': authorization_header
        }
        headers.update(auth_header)
        return 'http://{host}{endpoint}?{query}'.format(
            host=host, endpoint=endpoint,
            query=parse.urlencode(params) if params is not None else ''
        )

    @coroutine
    def put(self, path, data, headers=None, timeout=None):
        """ Asynchronously uploads the given data stream to the specified path
        """
        client = AsyncHTTPClient()
        method = 'PUT'
        url = self.generate_url(path)
        url_object = parse.urlparse(url)
        headers = headers or {}
        headers.update({
            'Content-Length': str(len(data)),
            'Content-Type': self._guess_mimetype(path),
            'Date': self._rfc822_datetime(),
            'Host': url_object.netloc,
            'X-Amz-Content-sha256': hashlib.sha256(data).hexdigest(),
        })

        try:
            response = yield client.fetch(
                self.sign_request(
                    url_object.netloc,
                    url_object.path,
                    headers,
                    method,
                    payload=data
                ),
                method=method,
                body=data,
                connect_timeout=AWS_S3_CONNECT_TIMEOUT,
                request_timeout=timeout or AWS_S3_REQUEST_TIMEOUT,
                headers=headers
            )
        except HTTPError as error:
            raise Return(error.response)

        raise Return(response)

    @coroutine
    def get(self, path, method='GET', timeout=None):
        """ Asynchronously get the data of path"""

        client = AsyncHTTPClient()
        url = self.generate_url(path)
        url_object = parse.urlparse(url)
        headers = {}
        try:
            response = yield client.fetch(
                self.sign_request(
                    url_object.netloc,
                    url_object.path,
                    headers,
                    method
                ),
                method=method,
                connect_timeout=AWS_S3_CONNECT_TIMEOUT,
                request_timeout=timeout or AWS_S3_REQUEST_TIMEOUT,
                headers=headers
            )
        except HTTPError as error:
            raise Return(error.response)

        raise Return(response)
