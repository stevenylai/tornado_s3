"""Simple command line interface"""
import argparse
import functools
import json
from tornado import ioloop
from . import s3, xml


def cmdline(args=None):
    """Command line"""
    parsers = {}
    parsers['main'] = argparse.ArgumentParser(
        description='AWS S3 command line'
    )
    parsers['main'].add_argument(
        'access_key', type=str, help='AWS access key'
    )
    parsers['main'].add_argument(
        'secret_key', type=str, help='AWS secret key'
    )
    parsers['main'].add_argument(
        'bucket', type=str, help='S3 bucket name'
    )
    parsers['main'].add_argument(
        'region', type=str, default='S3 bucket name', help='AWS region'
    )
    parsers['command'] = parsers['main'].add_subparsers(
        title="Commands", dest='command'
    )
    parsers['put'] = parsers['command'].add_parser(
        'put', help='Upload to S3'
    )
    parsers['copy'] = parsers['command'].add_parser(
        'copy', help='Copy an existing item on the server'
    )
    parsers['head'] = parsers['command'].add_parser(
        'head', help='Get HTTP head of a file in S3'
    )
    parsers['get'] = parsers['command'].add_parser(
        'get', help='Download a file from S3'
    )
    parsers['delete'] = parsers['command'].add_parser(
        'delete', help='Delete a file from S3'
    )
    for cmd in ('put', 'head', 'get', 'delete', 'copy'):
        parsers[cmd].add_argument(
            'server_path', type=str, help='Dest path on the server'
        )
    for cmd in ('put', 'get'):
        parsers[cmd].add_argument(
            'local_path', type=str, help='Path to the local file'
        )
    parsers['copy'].add_argument(
        'src', type=str,
        help='Src path on the server in the form of bucket/path'
    )
    args = parsers['main'].parse_args(args)
    client = s3.S3Client(
        args.access_key, args.secret_key, args.bucket, args.region
    )
    fun = None
    if args.command in {'head', 'get', 'delete'}:
        fun = functools.partial(
            client.get, args.server_path, method=args.command.upper()
        )
    elif args.command == 'put':
        with open(args.local_path, 'rb') as data:
            fun = functools.partial(
                client.put, args.server_path, data.read()
            )
    elif args.command == 'copy':
        fun = functools.partial(
            client.put, args.server_path, b'', {
                'x-amz-copy-source': args.src
            }
        )
    if fun is not None:
        res = ioloop.IOLoop.current().run_sync(fun)
        print('Status', res.code)
        print(res.headers)
        if args.command == 'get' and res.code == 200:
            with open(args.local_path, 'wb') as data:
                data.write(res.body)
        elif res.body is not None and len(res.body) > 0:
            print(json.dumps(xml.to_json(res.body.decode('utf-8')), indent=2))


if __name__ == '__main__':
    cmdline()
