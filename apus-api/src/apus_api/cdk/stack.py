import re
from collections import defaultdict
from typing import Optional

from apus_shared.cdk.builder_registry import Builder, register
from apus_shared.models import Connection
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
)

from apus_api.cdk import lookup
from apus_api.models import Authentication, DataGateway


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

        user_pools = self.cognito_user_pools(stack, resources)

        for domain_name, domain_resources in self.group_by_domain(resources):
            self.service(stack, cluster, domain_name, user_pools, domain_resources)

    def service(self, stack, cluster, domain_name, user_pools, resources) -> None:
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

        user_pools_envs = {
            f'{resource.metadata.name.upper()}_{key}': value
            for resource in resources
            if isinstance(resource.spec, Authentication)
            for key, value in user_pools[resource.metadata.name].items()
        }

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            stack,
            f'{construct_id}FargateService',
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry('vitalibo/apus-api:latest'),
                environment={
                    'CONFIG_FILE': asset_file.s3_object_url,
                    **user_pools_envs,
                },
            ),
            public_load_balancer=True,
            **self.custom_domain_name(
                stack=stack,
                construct_id=construct_id,
                domain_name=domain_name,
            ),
        )

        resource_arns = [
            f'arn:aws:cognito-idp:{stack.region}:{stack.account}:userpool/'
            f'{user_pools[resource.metadata.name]["USER_POOL"]}'
            for resource in resources
            if isinstance(resource.spec, Authentication)
        ]

        if resource_arns:
            fargate_service.task_definition.add_to_task_role_policy(
                iam.PolicyStatement(
                    actions=[
                        'cognito-idp:DescribeUserPoolClient',
                        'cognito-idp:InitiateAuth',
                    ],
                    resources=resource_arns,
                )
            )

        asset_file.grant_read(fargate_service.task_definition.task_role)

        fargate_service.target_group.configure_health_check(
            path='/health',
            healthy_http_codes='200',
        )

    @staticmethod
    def cognito_user_pools(stack, resources):
        """Create Cognito User Pools and return their props."""

        def user_pool_props(auth):
            if auth.user_pool:
                return {
                    'USER_POOL': auth.user_pool,
                    'CLIENT_ID': auth.client_id,
                }

            construct_id = ''.join(o.title() for o in re.split(r'[-._]', auth.domain or ''))

            user_pool = cognito.CfnUserPool(
                stack,
                f'{construct_id}UserPool',
                admin_create_user_config=cognito.CfnUserPool.AdminCreateUserConfigProperty(
                    allow_admin_create_user_only=True,
                ),
            )

            user_pool_client = cognito.CfnUserPoolClient(
                stack,
                f'{construct_id}UserPoolClient',
                user_pool_id=user_pool.ref,
                generate_secret=True,
                explicit_auth_flows=[
                    'ALLOW_USER_PASSWORD_AUTH',
                ],
            )

            return {
                'USER_POOL': user_pool.ref,
                'CLIENT_ID': user_pool_client.ref,
            }

        return {
            resource.metadata.name: user_pool_props(resource.spec)
            for resource in resources
            if isinstance(resource.spec, Authentication)
        }

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
            if isinstance(resource.spec, (DataGateway, Authentication)):
                domains[resource.spec.domain].append(resource)

        for gateways in domains.values():  # noqa: PLR1702
            domain_connections = []
            for gateway in gateways:
                if not isinstance(gateway.spec, DataGateway):
                    continue

                for connection in connections:
                    if connection.spec == gateway.spec.connection and connection not in domain_connections:
                        domain_connections.append(connection)
            gateways.extend(domain_connections)

        return domains.items()


register(ApiStackBuilder())
