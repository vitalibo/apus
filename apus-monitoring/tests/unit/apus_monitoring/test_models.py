import textwrap

from apus_shared.models import Connection, Engine, create_resource
from pyxis.resources import load_yaml, load_yaml_all

from apus_monitoring.models import BusinessMonitor, Channel, CloudWatchChannel, EmailChannel, SlackChannel

Resource = create_resource()


def test_channel_slack(subtests):
    objs = load_yaml_all(__file__, 'data/channels/slack.yaml')

    with subtests.test('simple'):
        resource = Resource(**objs[0]).root

        assert isinstance(resource.spec, SlackChannel)
        assert resource.spec.type == 'slack'
        assert resource.spec.token == 'xoxb-123456789012-123456789012-123456789012-123456789012'  # noqa: S105 # pragma: allowlist secret
        assert resource.spec.channels is None

    with subtests.test('with channels'):
        resource = Resource(**objs[1]).root

        assert resource.api_version == 'apus/v1'
        assert resource.kind == 'Channel'
        assert resource.metadata.name == 'MySlackChannel'
        assert isinstance(resource.spec, SlackChannel)
        assert resource.spec.type == 'slack'
        assert resource.spec.token == 'xoxb-123456789012-123456789012-123456789012-123456789012'  # noqa: S105 # pragma: allowlist secret
        assert resource.spec.channels == ['general', 'random']


def test_channel_email(subtests):
    objs = load_yaml_all(__file__, 'data/channels/email.yaml')

    with subtests.test('simple'):
        resource = Resource(**objs[0]).root

        assert resource.api_version == 'apus/v1'
        assert resource.kind == 'Channel'
        assert resource.metadata.name == 'MyEmailChannel'
        assert isinstance(resource.spec, EmailChannel)
        assert resource.spec.type == 'email'
        assert resource.spec.host == 'smtp.example.com'
        assert resource.spec.port == 587
        assert resource.spec.username == 'admin'
        assert resource.spec.password == '5ecr3t'  # noqa: S105 # pragma: allowlist secret
        assert resource.spec.recipients is None

    with subtests.test('with recipients'):
        resource = Resource(**objs[1]).root

        assert isinstance(resource.spec, EmailChannel)
        assert resource.spec.type == 'email'
        assert resource.spec.recipients == ['foo@apus.io', 'bar@apus.io']


def test_channel_cloudwatch():
    objs = load_yaml_all(__file__, 'data/channels/cloudwatch.yaml')

    resource = Resource(**objs[0]).root

    assert isinstance(resource.spec, CloudWatchChannel)
    assert resource.spec.type == 'cloudwatch'
    assert resource.spec.namespace == 'APUS/MyApp'


def test_business_monitor():
    objs = load_yaml_all(__file__, 'data/business_monitor.yaml')
    context = load_yaml(__file__, 'data/business_monitor_contex.yaml')

    resource = Resource.model_validate(objs[0], context=context).root

    assert resource.api_version == 'apus/v1'
    assert resource.kind == 'BusinessMonitor'
    assert resource.metadata.name == 'MyBusinessMonitor'
    assert isinstance(resource.spec, BusinessMonitor)
    assert resource.spec.schedule == '* */6 * * ? *'
    assert isinstance(resource.spec.connection, Connection)
    assert resource.spec.connection.engine == Engine.MYSQL
    assert resource.spec.connection.host == 'mysql.example.com'
    assert resource.spec.connection.port == 3306
    assert resource.spec.connection.username == 'root'
    assert resource.spec.connection.password == '5ecr3t'  # noqa: S105 # pragma: allowlist secret
    assert resource.spec.connection.database == 'mydb'
    assert resource.spec.metric.field == 'foo'
    assert resource.spec.metric.name is None
    assert resource.spec.metric.description is None
    assert resource.spec.dimensions['bar'].field == 'bar'
    assert resource.spec.dimensions['bar'].name is None
    assert resource.spec.dimensions['bar'].description is None
    assert resource.spec.dimensions['baz'].field == 'baz'
    assert resource.spec.dimensions['baz'].name == 'Baz'
    assert resource.spec.dimensions['baz'].description is None
    assert resource.spec.dimensions['qux'].field == 'qux'
    assert resource.spec.dimensions['qux'].name == 'Qux'
    assert resource.spec.dimensions['qux'].description == 'Qux description'
    assert resource.spec.query_template == textwrap.dedent(
        """\
        SELECT bar,
               baz,
               qux,
               COUNT(*) AS foo
        FROM table
        GROUP BY bar, baz"""
    )
    assert isinstance(resource.spec.channels[0], Channel)
    assert resource.spec.channels[0].type == 'cloudwatch'
    assert resource.spec.channels[0].namespace == 'APUS/MyApp'
    assert isinstance(resource.spec.channels[1], Channel)
    assert resource.spec.channels[1].type == 'email'
    assert resource.spec.channels[1].host == 'smtp.example.com'
    assert resource.spec.channels[1].port == 587
    assert resource.spec.channels[1].username == 'admin'
    assert resource.spec.channels[1].password == '5ecr3t'  # noqa: S105 # pragma: allowlist secret
    assert resource.spec.channels[1].recipients == ['vboyarsky@apus.io']
    assert isinstance(resource.spec.channels[2], Channel)
    assert resource.spec.channels[2].type == 'slack'
    assert resource.spec.channels[2].token == 'xoxb-123456789012-1234567890123-12345678901234567890'  # noqa: S105 # pragma: allowlist secret
    assert resource.spec.channels[2].channels == ['foo', 'bar']
