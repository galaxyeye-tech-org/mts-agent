# -*- coding: utf-8 -*-

__author__ = r'wsb310@gmail.com'

from fastapi import Body
from pydantic.fields import Field

from hagworm.frame.fastapi.base import APIRouter
from hagworm.frame.fastapi.model import BaseModel

from service import DataSource


router = APIRouter(prefix=r'/tool', tags=[r'tool'])


class FormVector(BaseModel):

    query: str = Field(..., description=r'数据')


@router.post(r'/vector')
async def vector(data: FormVector = Body(...)):

    return await DataSource().get_vector(data.query)
