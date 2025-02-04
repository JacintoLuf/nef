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
from internal import send_notification
from models.pcf_binding import PcfBinding
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import crud.asSessionWithQoSSub as asSessionWithQoSSub


router = APIRouter()

@router.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_get(scsAsId: str, subId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscription retrieve {subId}")
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@router.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
async def qos_get_all(scsAsId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscriptions retrieve")
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@router.post("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
async def qos_create(scsAsId: str, data: Request, background_tasks: BackgroundTasks):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscription creation")

    try:
        data_dict = await data.json()
        qos_sub = AsSessionWithQoSSubscription().from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

    if not ((qos_sub.ue_ipv4_addr is not None)^(qos_sub.ue_ipv6_addr is not None)^(qos_sub.mac_addr is not None)):
        conf.logger.info("Only one of ipv4Addr, ipv6Addr or macAddr")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of ipv4Addr, ipv6Addr or macAddr")
    if not ((qos_sub.flow_info is not None)^(qos_sub.eth_flow_info is not None)^(qos_sub.exter_app_id is not None)):
        conf.logger.info("Only one of IP flow info, Ethernet flow info or External Application")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of IP flow info, Ethernet flow info or External Application")
    if (qos_sub.ue_ipv4_addr or qos_sub.ue_ipv6_addr) and not qos_sub.flow_info:
        conf.logger.info("No flow info")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.mac_addr and not qos_sub.eth_flow_info:
        conf.logger.info("No eth flow info")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if (qos_sub.qos_reference and qos_sub.alt_qos_reqs) or (qos_sub.alt_qo_s_references and qos_sub.alt_qos_reqs):
        conf.logger.info("Alt QoS Ref & Alt QoS Reqs are mutually exclusive. If qos reference alt qos reqs should not be provided")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.qos_mon_info and qos_sub.events and "QOS_MONITORING" not in qos_sub.events:
        conf.logger.info("qos mon info and events and QOS_MONITORING not in events")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.alt_qo_s_references and not qos_sub.notification_destination:
        conf.logger.info("no notif destination")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    
    conf.logger.info("\n------------------------------qos sub---------------------------------------")
    conf.logger.info(qos_sub.to_str())
    conf.logger.info("---------------------------------------------------------------------\n")
    if "BSF" in conf.HOSTS.keys():
        bsf_params = {}
        if qos_sub.ue_ipv4_addr:
            bsf_params['ipv4Addr'] = qos_sub.ue_ipv4_addr
        elif qos_sub.ue_ipv6_addr:
            bsf_params['ipv6Prefix'] = qos_sub.ue_ipv6_addr
        elif qos_sub.mac_addr:
            bsf_params['macAddr48'] = qos_sub.mac_addr

        res = await bsf_handler.bsf_management_discovery(bsf_params)
        if res['code'] != httpx.codes.OK:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
        pcf_binding = PcfBinding.from_dict(res['response'])
        _id = str(uuid.uuid4().hex)
        while await asSessionWithQoSSub.check_id(_id):
            _id = str(uuid.uuid4().hex)
        response = await pcf_handler.pcf_policy_authorization_create_qos(pcf_binding, qos_sub, _id)
    else:
        _id = str(uuid.uuid4().hex)
        while await asSessionWithQoSSub.check_id(_id):
            _id = str(uuid.uuid4().hex)
        response = await pcf_handler.pcf_policy_authorization_create_qos(as_session_qos_sub=qos_sub, _id=_id)
    
    if response.status_code == httpx.codes.CREATED:
        conf.logger.info("Storing request and generating 'As Aession With QoS' resource.")
        sub_id = await asSessionWithQoSSub.as_session_with_qos_subscription_insert(scsAsId, qos_sub, response.headers['Location'], _id)
        if sub_id:
            if qos_sub.request_test_notification:
                test_notif = {'subscription': qos_sub.notification_destination}
                background_tasks.add_task(send_notification, test_notif, qos_sub.notification_destination)
            qos_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{sub_id}"
            conf.logger.info(f"Resource stored at {qos_sub.__self} with ID: {sub_id}")
            headers = conf.GLOBAL_HEADERS
            headers['location'] = qos_sub.__self
            end_time = (time() - start_time) * 1000
            headers = conf.GLOBAL_HEADERS
            headers.update({'X-ElapsedTime-Header': str(end_time)})
            return JSONResponse(status_code=httpx.codes.CREATED, content=qos_sub.to_dict())
        else:
            conf.logger.info("Error creating resource")
            #delete from pcf
            return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Error creating resource!")
    return Response(status_code=response.status_code, content=response.content)

@router.put("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_put(scsAsId: str, subId: str, data: Request):
    start_time = time()
    try:
        qosSub = AsSessionWithQoSSubscription.from_dict(data.json())
        await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scsAsId, subId=subId, sub=qosSub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content="The subscription was updated successfully.")

@router.patch("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_patch(scAsId: str, subId: str, data: Request):
    start_time = time()
    try:
        qosSub = AsSessionWithQoSSubscription.from_dict(data.json())
        await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scAsId, subId=subId, sub=qosSub.to_dict(), partial=True)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content="The subscription was updated successfully.")
    
@router.delete("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_delete(scsAsId: str, subId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscription deletion: {subId}")
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        
        conf.logger.info(f"deleting: {subId} from db")
        res = await asSessionWithQoSSub.as_session_with_qos_subscription_delete(scsAsId, subId)
        if res == 1:
            end_time = (time() - start_time) * 1000
            headers = conf.GLOBAL_HEADERS
            headers.update({'X-ElapsedTime-Header': str(end_time)})
            return Response(status_code=httpx.codes.NO_CONTENT, headers=headers)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")