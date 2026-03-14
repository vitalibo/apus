import json
import re
import tempfile

import pyxis.resources
from apus_shared.cdk import requirements
from apus_shared.cdk.builder_registry import Builder, register
from apus_shared.models import ScheduleStr
from aws_cdk import aws_glue, aws_iam, aws_s3_assets

from apus_monitoring.models import BusinessMonitor


class MonitoringStackBuilder(Builder):
    """CDK stack for APUS Monitoring service."""

    def build(self, stack, resources) -> None:
        if not any(isinstance(r.spec, BusinessMonitor) for r in resources):
            return

        for resource in resources:
            if isinstance(resource.spec, BusinessMonitor):
                self.create_glue_job(stack, resource, resources)

    def create_glue_job(self, stack, resource, resources):
        construct_id = self.logical_id(resource.metadata.name)

        script_file = aws_s3_assets.Asset(
            stack,
            f'{construct_id}ScriptFile',
            path=pyxis.resources.resource(__file__, '../driver.py'),
        )

        asset_file = aws_s3_assets.Asset(
            stack,
            f'{construct_id}AssetFile',
            path=file_dump(
                obj={
                    'resources': [r.model_dump() for r in resources],
                }
            ),
        )

        role = aws_iam.Role(
            stack,
            f'{construct_id}Role',
            assumed_by=aws_iam.ServicePrincipal('glue.amazonaws.com'),
            inline_policies={
                'LogsPolicy': aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources=['arn:aws:logs:*:*:*'],
                        )
                    ]
                )
            },
        )

        script_file.grant_read(role)
        asset_file.grant_read(role)

        job = aws_glue.CfnJob(
            stack,
            f'{construct_id}Job',
            name=resource.metadata.name + '-mon-job',
            glue_version='1.0',
            command=aws_glue.CfnJob.JobCommandProperty(
                name='pythonshell',
                python_version='3.9',
                script_location=script_file.s3_object_url,
            ),
            role=role.role_arn,
            max_capacity=0.0625,
            max_retries=0,
            timeout=60,
            default_arguments={
                '--additional-python-modules': requirements.apus_monitoring,
                '--config-file': asset_file.s3_object_url,
            },
        )

        aws_glue.CfnTrigger(
            stack,
            f'{construct_id}Trigger',
            name=resource.metadata.name + '-mon-trig',
            type='SCHEDULED',
            schedule=(
                f'cron({resource.spec.schedule})'
                if ScheduleStr.is_cron(resource.spec.schedule)
                else resource.spec.schedule
            ),
            start_on_creation=True,
            actions=[
                aws_glue.CfnTrigger.ActionProperty(job_name=job.ref),
            ],
        )

        return job

    @staticmethod
    def logical_id(name):
        return re.sub(r'[^a-zA-Z0-9]+', '', name.title())


register(MonitoringStackBuilder())


def file_dump(obj):
    """Dumps an object to a temporary JSON file and returns the file path."""

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json', delete=False) as file:
        json.dump(obj, file)
        return file.name
