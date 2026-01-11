import logging
import sys

import uvicorn
from fastapi import FastAPI
from pyxis.config import ConfigFactory

from apus_api import exts, routers

config = ConfigFactory.default_load()

logging.basicConfig(
    level=config.get('envs.LOG_LEVEL', logging.INFO),
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(module)s.%(funcName)s(%(lineno)d) %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

app = FastAPI(
    title='APUS RESTful API',
    swagger_ui_parameters={
        'defaultModelsExpandDepth': -1,
    },
)

exts.register(app)
routers.register(app, config)

if __name__ == '__main__':
    uvicorn.run(app='apus_api.main:app', host='0.0.0.0', port=8000)  # noqa: S104
