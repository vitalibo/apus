import json
import os
from pathlib import Path

import aws_cdk as cdk

from apus_shared.cdk import boto3_session

__all__ = [
    'synth',
]


def synth(cls, *args, **kwargs):
    """Synthesize the CDK stack and return the template as a YAML string."""

    app = cdk.App(
        analytics_reporting=False,
        context={
            'aws:cdk:enable-path-metadata': True,
        },
        outdir='cdk.out',
    )

    cls(
        app,
        'Stack',
        *args,
        synthesizer=cdk.DefaultStackSynthesizer(
            bucket_prefix=kwargs.pop('bucket_prefix').removesuffix('/') + '/',
            generate_bootstrap_version_rule=False,
            file_assets_bucket_name=kwargs.pop('file_assets_bucket_name'),
        ),
        **kwargs,
    )

    synthesized = app.synth()
    copy_artifacts(app.outdir)
    stack = synthesized.get_stack_by_name('Stack')
    return stack.stack_template_asset_object_url


def copy_artifacts(outdir):
    """Copy file assets to their respective S3 buckets."""

    def find_assets():
        for file in [
            Path(parent) / file
            for parent, _, files in os.walk(outdir)
            for file in files
            if file.endswith('.assets.json')
        ]:
            yield json.load(file.open())

    s3 = boto3_session.client('s3')
    for assets in find_assets():
        for asset in assets['files'].values():
            source_path = (Path(outdir) / asset['source']['path']).resolve()
            for destination in asset['destinations'].values():
                s3.upload_file(source_path, destination['bucketName'], destination['objectKey'])
