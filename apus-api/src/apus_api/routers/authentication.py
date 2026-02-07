import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Annotated

import boto3
import pytz
from apus_shared.models import Resource  # noqa: TC002
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials  # noqa: TC002
from jose import jwt
from starlette import status

from apus_api import schemas
from apus_api.models import Authentication  # noqa: TC001


class AuthenticationRouter(APIRouter):
    """A router for an Authentication resource."""

    def __init__(self, resource: Resource[Authentication]) -> None:
        super().__init__()
        self.expires_in = timedelta(seconds=resource.spec.expires_in)

        self.cognito_idp = boto3.client('cognito-idp')

        self.client_id = os.environ['USER_POOL_CLIENT_ID']
        self.client_secret = self.cognito_idp.describe_user_pool_client(
            UserPoolId=os.environ['USER_POOL'], ClientId=self.client_id
        )['UserPoolClient']['ClientSecret']

        self.get(
            path=resource.spec.path,
            summary=resource.metadata.labels.get('summary', resource.metadata.name),
            description=resource.metadata.labels.get('description'),
            response_model=schemas.AccessTokenResponse,
            tags={k[4:]: v for k, v in resource.metadata.annotations.items() if k.startswith('tags/')},
            responses={
                '401': {
                    'model': schemas.ErrorResponse,
                    'description': 'Unauthorized Error',
                    'content': schemas.ErrorResponse.Unauthorized,
                },
            },
        )(self.auth)

    def auth(self, credentials: Annotated[HTTPBasicCredentials, Depends(HTTPBasic())]) -> schemas.AccessTokenResponse:
        digest = hmac.new(
            bytes(self.client_secret, 'latin-1'),
            bytes(credentials.username + self.client_id, 'latin-1'),
            hashlib.sha256,
        ).digest()
        secret_hash = base64.b64encode(digest).decode()

        try:
            self.cognito_idp.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': credentials.username,
                    'PASSWORD': credentials.password,
                    'SECRET_HASH': secret_hash,
                },
            )
        except (
            self.cognito_idp.exceptions.NotAuthorizedException,
            self.cognito_idp.exceptions.UserNotFoundException,
        ) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Unauthorized',
                headers={
                    'WWW-Authenticate': 'Bearer',
                },
            ) from e

        jwt_token = jwt.encode(
            {
                'sub': credentials.username,
                'exp': datetime.now(tz=pytz.UTC) + self.expires_in,
            },
            self.client_secret,
            algorithm='HS256',
        )

        return schemas.AccessTokenResponse(
            access_token=jwt_token,
            token_type='Bearer',  # noqa: S106
            expires_in=self.expires_in.seconds,
        )
