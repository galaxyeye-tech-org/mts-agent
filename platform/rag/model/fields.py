# -*- coding: utf-8 -*-
from typing import Any, TypeAlias

from fastapi import Query

OFFSET = Query(0, ge=0, le=0xffff, description=r'偏移')
LIMIT = Query(10, ge=1, le=0xff, description=r'数量')

QANode: TypeAlias = dict[str, Any]
QAPair: TypeAlias = dict[str, list[QANode]]
