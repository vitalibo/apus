from typing import Annotated
from unittest import mock

import aws_cdk
from aws_cdk import Stack, aws_route53 as route53
from pydantic import Field

from apus_api.cdk import lookup
from apus_api.cdk.stack import ApiStackBuilder
from apus_api.models import DataGateway


def test_build():
    builder = ApiStackBuilder()
    with (
        mock.patch('apus_api.cdk.lookup.hosted_zone_from_domain_name') as mock_hosted_zone,
        mock.patch('apus_api.cdk.lookup.certificate_from_domain_name') as mock_certificate,
    ):
        stack = Stack(aws_cdk.App(), 'Stack')
        mock_hosted_zone.return_value = route53.HostedZone.from_hosted_zone_attributes(
            stack,
            'HostedZone',
            zone_name='apus-api.vitalibo.click.',
            hosted_zone_id='Z1234567890ABCDEFGH',
        )
        mock_certificate.side_effect = lookup.NotFoundError
        mock_resource = mock.Mock()
        mock_resource.model_dump.return_value = {'foo': 'bar'}
        fields = {
            '__annotations__': {
                name: Annotated[type(None), Field(None)]
                for name in ['request', 'response', 'connection', 'query_template']
            }
        }
        mock_resource.spec = type('TestDataGateway', (DataGateway,), fields)(domain='apus-api.vitalibo.click')

        builder.build(stack, [mock_resource])

        template = aws_cdk.assertions.Template.from_stack(stack)
        template.resource_count_is('AWS::EC2::VPC', 1)
        template.has_resource_properties('AWS::ECS::Cluster', {'ClusterName': 'apus-api'})
        template.has_resource_properties(
            'AWS::CertificateManager::Certificate',
            {
                'DomainName': 'apus-api.vitalibo.click',
                'DomainValidationOptions': [
                    {
                        'DomainName': 'apus-api.vitalibo.click',
                        'HostedZoneId': 'Z1234567890ABCDEFGH',
                    }
                ],
            },
        )
        template.has_resource_properties('AWS::ElasticLoadBalancingV2::LoadBalancer', {'Scheme': 'internet-facing'})
        template.has_resource_properties('AWS::Route53::RecordSet', {'Name': 'apus-api.vitalibo.click.', 'Type': 'A'})
        template.has_resource_properties(
            'AWS::ECS::TaskDefinition',
            {
                'ContainerDefinitions': [
                    {
                        'Environment': [
                            {
                                'Name': 'CONFIG_FILE',
                                'Value': {
                                    'Fn::Sub': aws_cdk.assertions.Match.string_like_regexp(r's3://.*\.json'),
                                },
                            }
                        ],
                        'Image': 'vitalibo/apus-api:latest',
                        'Name': 'web',
                        'PortMappings': [
                            {
                                'ContainerPort': 80,
                                'Protocol': 'tcp',
                            }
                        ],
                    }
                ],
                'Cpu': '256',
                'Memory': '512',
            },
        )
        template.has_resource_properties('AWS::ECS::Service', {'LaunchType': 'FARGATE'})
