import re
from collections import defaultdict
from typing import Optional

from apus_shared.cdk.builder_registry import Builder, register
from apus_shared.models import Connection
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_s3_assets as s3_assets,
)

from apus_api.cdk import lookup
from apus_api.models import DataGateway


class ApiStackBuilder(Builder):
    """CDK stack for APUS API service."""

    def build(self, stack, resources) -> None:
        if not any(isinstance(r.spec, DataGateway) for r in resources):
            return

        vpc = ec2.Vpc(
            stack,
            'Vpc',
            max_azs=2,
        )

        cluster = ecs.Cluster(
            stack,
            'Cluster',
            cluster_name='apus-api',
            vpc=vpc,
        )

        for domain_name, domain_resources in self.group_by_domain(resources):
            self.service(stack, cluster, domain_name, domain_resources)

    def service(self, stack, cluster, domain_name, resources) -> None:
        construct_id = ''.join(o.title() for o in re.split(r'[-._]', domain_name or ''))

        asset_file = s3_assets.Asset(
            stack,
            f'{construct_id}AssetFile',
            path=lookup.file_dump(
                obj={
                    'resources': [r.model_dump() for r in resources],
                }
            ),
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            stack,
            f'{construct_id}FargateService',
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry('vitalibo/apus-api:latest'),
                environment={
                    'CONFIG_FILE': asset_file.s3_object_url,
                },
            ),
            public_load_balancer=True,
            **self.custom_domain_name(
                stack=stack,
                construct_id=construct_id,
                domain_name=domain_name,
            ),
        )

        asset_file.grant_read(fargate_service.task_definition.task_role)

        fargate_service.target_group.configure_health_check(
            path='/health',
            healthy_http_codes='200',
        )

    @staticmethod
    def custom_domain_name(stack, construct_id, domain_name: Optional[str]) -> dict:
        """Configures custom domain name with https support."""

        if not domain_name:
            return {}

        hosted_zone = lookup.hosted_zone_from_domain_name(
            stack,
            f'{construct_id}HostedZone',
            domain_name=domain_name,
        )

        try:
            certificate = lookup.certificate_from_domain_name(
                stack,
                f'{construct_id}Certificate',
                domain_name=domain_name,
            )

        except lookup.NotFoundError:
            certificate = acm.Certificate(
                stack,
                f'{construct_id}Certificate',
                domain_name=domain_name,
                validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
            )

        return {
            'domain_name': domain_name,
            'domain_zone': hosted_zone,
            'certificate': certificate,
        }

    @staticmethod
    def group_by_domain(resources):
        domains = defaultdict(list)
        connections = []
        for resource in resources:
            if isinstance(resource.spec, Connection):
                connections.append(resource)
            if isinstance(resource.spec, DataGateway):
                domains[resource.spec.domain].append(resource)

        for gateways in domains.values():  # noqa: PLR1702
            domain_connections = []
            for gateway in gateways:
                for connection in connections:
                    if connection.spec == gateway.spec.connection and connection not in domain_connections:
                        domain_connections.append(connection)
            gateways.extend(domain_connections)

        return domains.items()


register(ApiStackBuilder())
