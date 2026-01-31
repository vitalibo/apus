from unittest import mock

from pyxis.resources import load_text
from typer.testing import CliRunner


def test_cli(subtests):
    runner = CliRunner()

    with mock.patch('apus_shared.cdk.boto3_session.Session') as mock_session:
        from apus_cli.main import app  # noqa: PLC0415

        with subtests.test('shows main help'):
            result = runner.invoke(app, args=['--help'])

            assert load_text(__file__, 'data/cli/help.txt') == result.output

        with subtests.test('shows deploy help'):
            result = runner.invoke(app, args=['deploy', '--help'])

            assert load_text(__file__, 'data/cli/help_deploy.txt') == result.output

        with subtests.test('shows destroy help'):
            result = runner.invoke(app, args=['destroy', '--help'])

            assert load_text(__file__, 'data/cli/help_destroy.txt') == result.output

        with subtests.test('passes profile and region'):
            mock_session.reset_mock()

            runner.invoke(app, args=['--profile', 'my-profile', '--region', 'us-west-2', 'deploy', '--help'])

            mock_session.assert_called_once_with(profile_name='my-profile', region_name='us-west-2')
