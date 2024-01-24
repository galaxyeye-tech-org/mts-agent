# -*- coding: utf-8 -*-
from typing import NamedTuple

import httpx

from setting import Config

HTTP_RETRY_COUNT = 10
HTTP_CLIENT_TIMEOUT = httpx.Timeout(timeout=600)


DIALOG_MONGO_COLLECTION = r'dialog_storage'

DOCUMENT_ELASTICSEARCH_INDEX = f'{Config.MongoDBName}_{Config.MilvusCollectionDocumentName}'
