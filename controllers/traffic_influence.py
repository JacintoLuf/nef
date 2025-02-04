import httpx
from fastapi import APIRouter, Request, Response, HTTPException
from api.config import conf
import json
import uuid
import httpx
from time import time
from api.config import conf
from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from main import send_notification
from models.pcf_binding import PcfBinding
from models.traffic_influ_sub import TrafficInfluSub
from models.event_notification import EventNotification
from models.traffic_influ_sub_patch import TrafficInfluSubPatch
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import core.udm_handler as udm_handler
import core.udr_handler as udr_handler
import crud.trafficInfluSub as trafficInfluSub


router = APIRouter()

@router.get("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_get(afId: str, subId: str=None):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscription retrieval {subId}")
    res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@router.get("/3gpp-traffic-influence/v1/{afId}/subscriptions")
async def ti_get_all(afId: str):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscriptions retrieval")
    res = await trafficInfluSub.traffic_influence_subscription_get(afId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@router.post("/3gpp-traffic-influence/v1/{afId}/subscriptions")
async def traffic_influ_create(afId: str, data: Request, background_tasks: BackgroundTasks):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscription creation")
    try:
        data_dict = await data.json()
        traffic_sub = TrafficInfluSub.from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

    if not ((traffic_sub.af_app_id is not None)^(traffic_sub.traffic_filters is not None)^(traffic_sub.eth_traffic_filters is not None)):
        conf.logger.info(f"app id: {type(traffic_sub.af_app_id)}, traffic filters: {type(traffic_sub.traffic_filters)}, eth traffic filters: {type(traffic_sub.eth_traffic_filters)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of afAppId, trafficFilters or ethTrafficFilters")
    if not ((traffic_sub.ipv4_addr is not None)^(traffic_sub.ipv6_addr is not None)^(traffic_sub.mac_addr is not None)^(traffic_sub.gpsi is not None)^(traffic_sub.external_group_id is not None)^(traffic_sub.any_ue_ind is not None)):
        conf.logger.info(f"ipv4: {type(traffic_sub.ipv4_addr)}, any ue: {type(traffic_sub.any_ue_ind)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of ipv4Addr, ipv6Addr, macAddr, gpsi, externalGroupId or anyUeInd")
   
    #---------------------------any ue, gpsi or ext group id------------------------
    if traffic_sub.any_ue_ind or traffic_sub.gpsi or traffic_sub.external_group_id:
        if traffic_sub.any_ue_ind and not traffic_sub.dnn or not traffic_sub.snssai:
            raise HTTPException(httpx.codes.BAD_REQUEST, detail="Cannot parse message")
        supi = intGroupId = None
        if traffic_sub.gpsi:
            supi = udm_handler.udm_sdm_id_translation(traffic_sub.gpsi)
        elif traffic_sub.external_group_id:
            intGroupId = udm_handler.udm_sdm_group_identifiers_translation(traffic_sub.external_group_id)
        res = await udr_handler.udr_app_data_insert(traffic_sub, intGroupId, supi)
        if res.status_code == httpx.codes.CREATED:
            sub_id = trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'])
            if sub_id:
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-traffic-influence/v1/{afId}/subscriptions/{sub_id}"
                traffic_sub.supp_feat = "ffff"
                headers={'location': traffic_sub.__self, 'content-type': 'application/json'}
                if traffic_sub.request_test_notification:
                    test_notif = EventNotification(af_trans_id=traffic_sub.af_trans_id)
                    background_tasks.add_task(send_notification, test_notif.to_dict(), traffic_sub.notification_destination)
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                conf.logger.info("Server error")
                raise HTTPException(status_code=500, detail="Error creating resource")
        else:
            raise HTTPException(status_code=500, detail="Error creating resource")
        
    #------------------------ipv4, ipv6 or eth---------------------------
    else:
        if "BSF" in conf.HOSTS.keys():
            bsf_params = {}
            bsf_params['gpsi'] = traffic_sub.gpsi
            bsf_params['dnn'] = traffic_sub.dnn,
            bsf_params['snssai'] = traffic_sub.snssai
            if traffic_sub.ipv4_addr:
                bsf_params['ipv4Addr'] = traffic_sub.ipv4_addr
            elif traffic_sub.ipv6_addr:
                bsf_params['ipv6Prefix'] = traffic_sub.ipv6_addr
            elif traffic_sub.mac_addr:
                bsf_params['macAddr48'] = traffic_sub.mac_addr

            res = await bsf_handler.bsf_management_discovery(bsf_params)
            if res['code'] != httpx.codes.OK:
                raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
            
            pcf_binding = PcfBinding.from_dict(res['response'])
            _id = str(uuid.uuid4().hex)
            while await trafficInfluSub.check_id(_id):
                _id = str(uuid.uuid4().hex)
            res = await pcf_handler.pcf_policy_authorization_create_ti(pcf_binding, traffic_sub, _id)
        else:
            _id = str(uuid.uuid4().hex)
            while await trafficInfluSub.check_id(_id):
                _id = str(uuid.uuid4().hex)
            res = await pcf_handler.pcf_policy_authorization_create_ti(traffic_influ_sub=traffic_sub, _id=_id)

        if res.status_code == httpx.codes.CREATED:
            conf.logger.info("Storing request and generating 'Traffic Influence' resource.")
            sub_id = await trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'], _id)
            if sub_id:
                if traffic_sub.request_test_notification:
                    test_notif = {'subscription': traffic_sub.notification_destination}
                    background_tasks.add_task(send_notification, test_notif, traffic_sub.notification_destination)
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-traffic-influence/v1/{afId}/subscriptions/{sub_id}"
                conf.logger.info(f"Resource stored at {traffic_sub.__self} with ID: {sub_id}")
                headers = conf.GLOBAL_HEADERS
                headers['location'] = traffic_sub.__self
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                conf.logger.info("Server error")
                return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Error creating resource!")
    return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Unknown server error!")

@router.put("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_put(afId: str, subId: str, data: Request):
    start_time = time()
    try:
        data_dict = await data.json()
        traffic_sub = TrafficInfluSub.from_dict(data_dict)
        res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=traffic_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content=res)

@router.patch("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_patch(afId: str, subId: str, data: Request):
    start_time = time()
    try:
        traffic_sub = TrafficInfluSubPatch.from_dict(data.json())
        res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=traffic_sub.to_dict(), partial=True)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content=res)

@router.delete("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def delete_ti(afId: str, subId: str):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscription deletion: {subId}")
    try:
        res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
        if not res:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        else:
            contextId = res['location'].split('/')[-1]
            res = await pcf_handler.pcf_policy_authorization_delete(contextId)
            if res.status_code != httpx.codes.NO_CONTENT:
                conf.logger.info("Context not found!")
                raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")

            conf.logger.info(f"deleting: {subId} from db")
            res = await trafficInfluSub.individual_traffic_influence_subscription_delete(afId, subId)
            if res == 1:
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return Response(status_code=httpx.codes.NO_CONTENT, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)