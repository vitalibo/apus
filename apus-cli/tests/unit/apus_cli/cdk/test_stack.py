from unittest import mock

import aws_cdk as cdk
from apus_shared.cdk.builder_registry import Builder, register
from aws_cdk import assertions, aws_s3, aws_sqs

from apus_cli.cdk.stack import ApusStack


class S3StackBuilder(Builder):
    def build(self, stack, resources):
        if any(r.spec == 's3' for r in resources):
            aws_s3.Bucket(stack, 'MyBucket', bucket_name='my-test-bucket')


class SQSStackBuilder(Builder):
    def build(self, stack, resources):
        if any(r.spec == 'sqs' for r in resources):
            aws_sqs.Queue(stack, 'MyQueue', queue_name='my-test-queue')


def test_stack(subtests):
    register(S3StackBuilder())

    mock_s3 = mock.Mock()
    mock_s3.spec = 's3'
    mock_sqs = mock.Mock()
    mock_sqs.spec = 'sqs'

    with subtests.test('unknown SQS queue is ignored'):
        stack = ApusStack(cdk.App(), 'Stack1', resources=[mock_s3, mock_sqs])
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties('AWS::S3::Bucket', {'BucketName': 'my-test-bucket'})
        template.resource_count_is('AWS::SQS::Queue', 0)

    register(SQSStackBuilder())

    with subtests.test('creates S3 bucket and SQS queue'):
        stack = ApusStack(cdk.App(), 'Stack2', resources=[mock_s3, mock_sqs])
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties('AWS::S3::Bucket', {'BucketName': 'my-test-bucket'})
        template.has_resource_properties('AWS::SQS::Queue', {'QueueName': 'my-test-queue'})

    with subtests.test('creates only S3 bucket'):
        stack = ApusStack(cdk.App(), 'Stack3', resources=[mock_s3])
        template = assertions.Template.from_stack(stack)

        template.has_resource_properties('AWS::S3::Bucket', {'BucketName': 'my-test-bucket'})
        template.resource_count_is('AWS::SQS::Queue', 0)

    with subtests.test('creates only SQS queue'):
        stack = ApusStack(cdk.App(), 'Stack4', resources=[mock_sqs])
        template = assertions.Template.from_stack(stack)

        template.resource_count_is('AWS::S3::Bucket', 0)
        template.has_resource_properties('AWS::SQS::Queue', {'QueueName': 'my-test-queue'})
