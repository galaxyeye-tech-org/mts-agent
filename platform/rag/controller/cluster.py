# -*- coding: utf-8 -*-
# @FileName  : cluster.py
# @Description TODO
# @Author： yangmingxing
# @Email: yangmingxing@galaxyeye-tech.com
# @Date 12/15/23 2:18 PM 
# @Version 1.0

import fastapi


from fastapi import Body
from hagworm.frame.fastapi.base import APIRouter
from hagworm.frame.fastapi.model import BaseModel
from pydantic import Field
from model.responses import Response
from model.responses import ErrorResponse, ErrorCode


router = APIRouter(prefix=r'/cluster', default_response_class=Response, tags=[r'cluster'])


class FormAddClusterMessage(BaseModel):
    impression: list[dict] = Field(..., title=r'印象: 植物性认知推导得到')

class FormSearchImpression(BaseModel):
    uid: str = Field(..., title=r'用户id')


@router.post(r'/impression_cluster', summary=r'impressions to cluster')
async def impression_cluster(form: FormAddClusterMessage = Body(...)):
    from service.cluster_service import ClusterService
    result = await ClusterService().impression_cluster(
         form.impression
    )

    if result is False:
        raise ErrorResponse(ErrorCode.ClusterParamError)
    return result

@router.post(r'/impressions_search', summary=r'search impressions by uid')
async def impression_cluster(form: FormSearchImpression = Body(...)):
    from service.cluster_service import ClusterService
    result = await ClusterService().search_impression(
         form.uid
    )

    if result is False:
        raise ErrorResponse(ErrorCode.ClusterParamError)
    return result
