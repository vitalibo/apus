from unittest import mock

import pytest
from pyxis.resources import load_json

from apus_api.cdk.lookup import NotFoundError, certificate_from_domain_name, file_dump, hosted_zone_from_domain_name


def test_hosted_zone_from_domain_name(subtests):
    with (
        mock.patch('apus_shared.cdk.boto3_session.__getattr__') as mock_session,
        mock.patch('aws_cdk.aws_route53.HostedZone.from_hosted_zone_attributes') as mock_from_hosted_zone_attributes,
    ):
        mock_route53 = mock.Mock()
        mock_session.return_value.return_value = mock_route53
        mock_stack = mock.Mock()
        mock_hosted_zone = mock.Mock()
        mock_from_hosted_zone_attributes.return_value = mock_hosted_zone

        with subtests.test('found'):
            mock_route53.list_hosted_zones_by_name.side_effect = [
                {'HostedZones': []},
                {'HostedZones': []},
                {'HostedZones': [{'Name': 'vitalibo.click.', 'Id': '/hostedzone/ZONEID12345'}]},
            ]

            actual = hosted_zone_from_domain_name(mock_stack, 'TestConstruct', 'foo.bar.vitalibo.click')

            assert actual == mock_hosted_zone
            mock_from_hosted_zone_attributes.assert_called_once_with(
                mock_stack, 'TestConstruct', zone_name='vitalibo.click.', hosted_zone_id='ZONEID12345'
            )
            mock_route53.list_hosted_zones_by_name.assert_has_calls(
                [
                    mock.call(DNSName='foo.bar.vitalibo.click', MaxItems='1'),
                    mock.call(DNSName='bar.vitalibo.click', MaxItems='1'),
                    mock.call(DNSName='vitalibo.click', MaxItems='1'),
                ]
            )

        with subtests.test('not found'):
            mock_route53.list_hosted_zones_by_name.side_effect = [{'HostedZones': []}, {'HostedZones': []}]

            with pytest.raises(NotFoundError) as e:
                hosted_zone_from_domain_name(mock_stack, 'TestConstruct', 'foo.vitalibo.click')

            assert str(e.value) == 'No hosted zone found for domain name: foo.vitalibo.click'


def test_certificate_from_domain_name(subtests):
    def cert(arn, domain_name, subject_alternative_names):
        return {
            'CertificateArn': f'arn:aws:acm:region:account:certificate/{arn}',
            'DomainName': domain_name,
            'SubjectAlternativeNameSummaries': subject_alternative_names,
        }

    with (
        mock.patch('apus_shared.cdk.boto3_session.__getattr__') as mock_session,
        mock.patch('aws_cdk.aws_certificatemanager.Certificate.from_certificate_arn') as mock_from_certificate_arn,
    ):
        mock_acm_client = mock.Mock()
        mock_session.return_value.return_value = mock_acm_client
        mock_acm_paginator = mock.Mock()
        mock_acm_client.get_paginator.return_value = mock_acm_paginator
        mock_stack = mock.Mock()
        mock_certificate = mock.Mock()
        mock_from_certificate_arn.return_value = mock_certificate

        with subtests.test('wildcard match'):
            mock_acm_paginator.paginate.return_value = [
                {
                    'CertificateSummaryList': [
                        cert('cert-3858', '*.vitalibo.click', ['vitalibo.click', 'api.vitalibo.click']),
                        cert('cert-9012', '*.example.com', []),
                    ]
                },
                {
                    'CertificateSummaryList': [
                        cert('cert-8704', 'foo.example.com', []),
                    ]
                },
                {'CertificateSummaryList': []},
            ]

            actual = certificate_from_domain_name(mock_stack, 'TestCert', 'foo.vitalibo.click')

            assert actual == mock_certificate
            mock_from_certificate_arn.assert_called_once_with(
                mock_stack, 'TestCert', certificate_arn='arn:aws:acm:region:account:certificate/cert-3858'
            )
            mock_acm_paginator.paginate.assert_called_once_with(CertificateStatuses=['ISSUED'])

        with subtests.test('exact match'):
            mock_from_certificate_arn.reset_mock()
            mock_acm_paginator.paginate.return_value = [
                {
                    'CertificateSummaryList': [
                        cert('cert-3858', '*.vitalibo.click', ['vitalibo.click', 'api.vitalibo.click']),
                        cert('cert-9012', '*.example.com', []),
                    ]
                },
                {
                    'CertificateSummaryList': [
                        cert('cert-3858', 'foo.vitalibo.click', []),
                        cert('cert-8704', 'foo.example.com', []),
                    ]
                },
            ]

            certificate_from_domain_name(mock_stack, 'TestCert', 'foo.vitalibo.click')

            mock_from_certificate_arn.assert_called_once_with(
                mock_stack, 'TestCert', certificate_arn='arn:aws:acm:region:account:certificate/cert-3858'
            )

        with subtests.test('not found'):
            mock_from_certificate_arn.reset_mock()
            mock_acm_paginator.paginate.return_value = [
                {
                    'CertificateSummaryList': [
                        cert('cert-9012', '*.example.com', []),
                    ]
                },
                {
                    'CertificateSummaryList': [
                        cert('cert-8704', 'foo.example.com', []),
                    ]
                },
            ]

            with pytest.raises(NotFoundError) as e:
                certificate_from_domain_name(mock_stack, 'TestCert', 'foo.vitalibo.click')

            assert str(e.value) == 'No certificate found for domain name: foo.vitalibo.click'
            mock_from_certificate_arn.assert_not_called()


def test_file_dump():
    actual = file_dump({'key': 'value'})

    assert load_json('', actual) == {'key': 'value'}
