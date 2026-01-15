import json
import os
from pathlib import Path

import aws_cdk as cdk
import boto3
import yaml

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
            bucket_prefix=kwargs.pop('bucket_prefix'),
            generate_bootstrap_version_rule=False,
            file_assets_bucket_name=kwargs.pop('file_assets_bucket_name'),
        ),
        **kwargs,
    )

    synthesized = app.synth()
    copy_artifacts(app)
    template = synthesized.get_stack_by_name('Stack').template
    return yaml.dump(template, sort_keys=False)


def copy_artifacts(app):
    """Copy file assets to their respective S3 buckets."""

    def find_assets():
        for file in [
            Path(parent) / file
            for parent, _, files in os.walk(app.outdir)
            for file in files
            if file.endswith('.assets.json')
        ]:
            yield json.load(file.open())

    s3 = boto3.client('s3')
    for assets in find_assets():
        for asset in assets['files'].values():
            source_path = (Path(app.outdir) / asset['source']['path']).resolve()
            for destination in asset['destinations'].values():
                s3.upload_file(source_path, destination['bucketName'], destination['objectKey'])
