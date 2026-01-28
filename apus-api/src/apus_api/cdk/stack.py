from typing import Optional

from apus_shared.cdk.stack import StackBuilder, register
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_s3_assets as s3_assets,
)

from apus_api.cdk import lookup
from apus_api.models import DataGateway


class ApiStackBuilder(StackBuilder):
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

        asset_file = s3_assets.Asset(
            stack,
            'AssetFile',
            path=lookup.file_dump(
                obj={
                    'resources': [r.model_dump() for r in resources],
                }
            ),
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            stack,
            'FargateService',
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
                domain_name='apus-api.vitalibo.click',
            ),
        )

        asset_file.grant_read(fargate_service.task_definition.task_role)

        fargate_service.target_group.configure_health_check(
            path='/health',
            healthy_http_codes='200',
        )

    @staticmethod
    def custom_domain_name(stack, domain_name: Optional[str]) -> dict:
        """Configures custom domain name with https support."""

        if not domain_name:
            return {}

        hosted_zone = lookup.hosted_zone_from_domain_name(
            stack,
            'HostedZone',
            domain_name=domain_name,
        )

        try:
            certificate = lookup.certificate_from_domain_name(
                stack,
                'Certificate',
                domain_name=domain_name,
            )

        except lookup.NotFoundError:
            certificate = acm.Certificate(
                stack,
                'Certificate',
                domain_name=domain_name,
                validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
            )

        return {
            'domain_name': domain_name,
            'domain_zone': hosted_zone,
            'certificate': certificate,
        }


register(ApiStackBuilder())
