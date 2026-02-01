import shutil
from pathlib import Path
from unittest import mock

from aws_cdk import CfnOutput, CfnParameter, Stack, aws_s3, aws_s3_assets
from pyxis.resources import load_json, load_text

from apus_shared.cdk import synthesizer


class TestStack(Stack):
    def __init__(self, scope: Stack, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        env = CfnParameter(self, 'Environment', type='String', default='test')
        aws_s3_assets.Asset(self, 'AssetFile', path=__file__)
        bucket = aws_s3.Bucket(self, 'TestBucket', bucket_name=f'apus-{env.value_as_string}-bucket')
        CfnOutput(self, 'OutputValue', value=bucket.bucket_name)


def test_synth():
    with mock.patch('apus_shared.cdk.boto3_session.__getattr__') as mock_session:
        mock_s3 = mock.Mock()
        mock_session.return_value.return_value = mock_s3

        template_url = synthesizer.synth(
            TestStack,
            bucket_prefix='apus-test/v1.2.34',
            file_assets_bucket_name='apus-test-assets',
        )

        upload_files = [(str(o.args[0]), o.args[1], o.args[2]) for o in mock_s3.upload_file.mock_calls]
        stack_path, stack_s3_bucket, stack_s3_key = next(o for o in upload_files if o[0].endswith('.template.json'))
        assert load_json('', stack_path) == load_json(__file__, 'data/stack.template.json')
        assert template_url == f's3://{stack_s3_bucket}/{stack_s3_key}'
        assert stack_s3_bucket == 'apus-test-assets'
        assert stack_s3_key.startswith('apus-test/v1.2.34/')
        py_file_path, py_file_s3_bucket, py_file_s3_key = next(o for o in upload_files if o[0].endswith('.py'))
        assert load_text('', py_file_path) == load_text(__file__, 'test_synthesizer.py')
        assert py_file_s3_bucket == 'apus-test-assets'
        assert py_file_s3_key.startswith('apus-test/v1.2.34/')
        shutil.rmtree(Path(stack_path).parent)
