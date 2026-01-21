from aws_cdk import (  # noqa: I001
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_s3_assets as s3_assets,
    Stack,
)

from typing import Optional

from apus_api.cdk import lookup


class ApusApiStack(Stack):
    """CDK stack for APUS API service."""

    def __init__(self, scope: Stack, construct_id, config, domain_name=None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            'Vpc',
            max_azs=2,
        )

        cluster = ecs.Cluster(
            self,
            'Cluster',
            cluster_name='apus-api',
            vpc=vpc,
        )

        asset_file = s3_assets.Asset(
            self,
            'AssetFile',
            path=lookup.file_dump(obj=dict(config)),
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            'FargateService',
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry('vitalibo/apus-api:latest'),
                environment={
                    'CONFIG_FILE': asset_file.s3_object_url,
                },
            ),
            public_load_balancer=True,
            **self.custom_domain_name(domain_name=domain_name),
        )

        asset_file.grant_read(fargate_service.task_definition.task_role)

        fargate_service.target_group.configure_health_check(
            path='/health',
            healthy_http_codes='200',
        )

    def custom_domain_name(self, domain_name: Optional[str]) -> dict:
        """Configures custom domain name with https support."""

        if not domain_name:
            return {}

        hosted_zone = lookup.hosted_zone_from_domain_name(
            self,
            'HostedZone',
            domain_name=domain_name,
        )

        try:
            certificate = lookup.certificate_from_domain_name(
                self,
                'Certificate',
                domain_name=domain_name,
            )

        except lookup.NotFoundError:
            certificate = acm.Certificate(
                self,
                'Certificate',
                domain_name=domain_name,
                validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
            )

        return {
            'domain_name': domain_name,
            'domain_zone': hosted_zone,
            'certificate': certificate,
        }
