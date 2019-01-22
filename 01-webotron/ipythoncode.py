# coding: utf-8
import boto3
session = boto3.Session(profile_name='default')
s3 = session.rescource('s3')


#new_bucket = s3.create_bucket
#for bucket in s3.buckets.all():
#    print(bucket)
