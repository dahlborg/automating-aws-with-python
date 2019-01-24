#!/usr/bin/oython
# -*- coding: utf-8 -*-

"""Webotron: Deploy websites with AWS.

Webotron automates the process of deploying static websites to AWS.
- Configure AWS S3 list_buckets
  - Create them
  - Set them up for static website hosting
  - Deploy local files to them
- Configure DNS with AWS Route 53
- Configure a Content Delivery Network and SSL with AWS CloudFront
"""


from pathlib import Path
import mimetypes
import boto3
from botocore.exceptions import ClientError
import click

session = boto3.Session(profile_name='default')
s3 = session.resource('s3')


@click.group()
def cli():
    """Webotron deploys websites to AWS."""
    pass


@cli.command('list-buckets')
def list_buckets():
    """List all s3 buckets."""
    for bucket in s3.buckets.all():
        print(bucket)


@cli.command('list-buckets-objects')
@click.argument('bucket')
def list_buckets_objects(bucket):
    """List objects in an s3 bucket."""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)
    pass


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure s3 bucket."""
    s3bucket = None
    try:
        s3bucket = s3.create_bucket(
            Bucket='bucket',
            CreateBucketConfiguration={
                'LocationConstraint': session.region_name}
        )
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3bucket = s3.Bucket(bucket)
        else:
            raise error

    policy = """
    {
        "Version": "2012-10-17",
        "Id": "Policy1548236922651",
        "Statement": [
            {
                "Sid": "Stmt1548236884919",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::%s/*"
            }
        ]
    }
    """ % s3bucket.name
    policy = policy.strip()

    pol = s3bucket.Policy()
    pol.put(Policy=policy)

    ws = s3bucket.Website()

    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })

    return


def upload_file(s3bucket, path, key):
    """Upload path to s3_bucket at key."""
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': content_type
        })


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to bucket."""
    s3bucket = s3.Bucket(bucket)
    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
        for path in target.iterdir():
            if path.is_dir():
                handle_directory(path)
            if path.is_file():
                upload_file(s3bucket, str(path), str(path.relative_to(root)))
    handle_directory(root)


if __name__ == '__main__':
    cli()
