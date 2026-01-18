import json
import re
import tempfile

import boto3
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53


def hosted_zone_from_domain_name(cls, construct_id, domain_name: str) -> route53.IHostedZone:
    """Finds and returns a Route53 hosted zone by domain name."""

    route53_client = boto3.client('route53')

    domain_name_parts = domain_name.split('.')
    for i in range(len(domain_name_parts) - 1):
        response = route53_client.list_hosted_zones_by_name(DNSName='.'.join(domain_name_parts[i:]), MaxItems='1')
        hosted_zones = response.get('HostedZones', [])
        if hosted_zones:
            hosted_zone = hosted_zones[0]
            return route53.HostedZone.from_hosted_zone_attributes(
                cls,
                construct_id,
                zone_name=hosted_zone['Name'],
                hosted_zone_id=hosted_zone['Id'].split('/')[-1],
            )

    raise NotFoundError(f'No hosted zone found for domain name: {domain_name}')


def certificate_from_domain_name(cls, construct_id, domain_name: str):
    """Finds and returns an ACM certificate by domain name."""

    acm_client = boto3.client('acm')
    paginator = acm_client.get_paginator('list_certificates')

    certificates = []
    for page in paginator.paginate(CertificateStatuses=['ISSUED']):  # noqa: PLR1702
        for cert in page['CertificateSummaryList']:
            for cert_domain in [cert['DomainName'], *cert['SubjectAlternativeNameSummaries']]:
                cert_domain_pattern = re.compile(re.escape(cert_domain).replace(r'\*', '[^.]+'))
                if re.fullmatch(cert_domain_pattern, domain_name):
                    certificates.append(cert)
                    break

    if not certificates:
        raise NotFoundError(f'No certificate found for domain name: {domain_name}')

    cert = max(certificates, key=lambda c: (len(c['DomainName'].replace('*', '')), -c['DomainName'].count('*')))
    return acm.Certificate.from_certificate_arn(cls, construct_id, certificate_arn=cert['CertificateArn'])


def file_dump(obj):
    """Dumps an object to a temporary JSON file and returns the file path."""

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json', delete=False) as file:
        json.dump(obj, file)
        return file.name


class NotFoundError(Exception):
    """Lookup resource not found error."""
