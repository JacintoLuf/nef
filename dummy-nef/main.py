import httpx
import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi_utils.tasks import repeat_every
from fastapi.responses import JSONResponse
from session import async_db, clean_db
from api.config import conf
from api.sbi_req import get_req, delete_req
from models.pcf_binding import PcfBinding
from models.traffic_influ_sub import TrafficInfluSub
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
import core.nrf_handler as nrf_handler
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import core.udm_handler as udm_handler
import core.udr_handler as udr_handler
import crud.nfProfile as nfProfile
import crud.trafficInfluSub as trafficInfluSub
import crud.asSessionWithQoSSub as asSessionWithQoSSub
from api.af_request_template import influ_sub, any_influ_sub, qos_subscription, qos_subscription2, any_qos_sub

app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    res = await nrf_handler.nf_register()
    if res.status_code == httpx.codes.CREATED:
        await nrf_heartbeat()
    res = await nrf_handler.nrf_discovery()
    await status_subscribe()

    # res = await nrf_handler.nrf_get_access_token()
    # if res != httpx.codes.OK:
    #     print("Tokens denied")

@repeat_every(seconds=conf.NEF_PROFILE.heart_beat_timer - 2)
async def nrf_heartbeat():
    await nrf_handler.nf_register_heart_beat()

@repeat_every(seconds=86400)
async def status_subscribe():
    res = await nrf_handler.nf_status_subscribe()

@app.on_event("shutdown")
async def shutdown():
    print("shuting down...")
    await nrf_handler.nf_deregister()
    await nrf_handler.nf_status_unsubscribe()

@app.get("/")
async def read_root():
    insts = await nfProfile.get_all()
    return {'nfs instances': str(insts)}

@app.post("/nnrf-nfm/v1/subscriptions")
async def nrf_notif(notif):
    print("--------------------------nrf callback notif-------------------------")
    print(type(notif))
    print(notif)
    #notif_data = notif.json()
    #res = await nrf_handler.nf_update(notif_data)
    return Response(status_code=httpx.codes.NO_CONTENT)

@app.post("/up_path_change")
async def up_path_chg_notif(notif):
    print(type(notif))
    print(notif)
    return Response(status_code=httpx.codes.NO_CONTENT)

# @app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions")
@app.get("/get")
async def get():
    res = await trafficInfluSub.traffic_influence_subscription_get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_get(afId: str, subId: str=None):
    res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=res, status_code=httpx.codes.OK)

# @app.post("/3gpp-traffic-influence/v1/{afId}/subscriptions")
# async def ti_create(afId, data: Request):
@app.get("/create")
async def ti_create(afId: str=None):
    if not afId:
        afId = "default"
    # try:
    #     traffic_sub = TrafficInfluSub.from_dict(data.json())
    # except:
    #     raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse HTTP message")
    
    # if traffic_sub.notification_destination and not traffic_sub.subscribed_events:
    #     raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse HTTP message")
    
    # if traffic_sub.tfc_corr_ind and not traffic_sub.external_group_id:
    #     raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse HTTP message")
    traffic_sub = influ_sub
    if not ((traffic_sub.af_app_id is not None)^(traffic_sub.traffic_filters is not None)^(traffic_sub.eth_traffic_filters is not None)):
        print(f"app id: {type(traffic_sub.af_app_id)}, traffic filters: {type(traffic_sub.traffic_filters)}, eth traffic filters: {type(traffic_sub.eth_traffic_filters)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of afAppId, trafficFilters or ethTrafficFilters")
    if not ((traffic_sub.ipv4_addr is not None)^(traffic_sub.ipv6_addr is not None)^(traffic_sub.mac_addr is not None)^(traffic_sub.gpsi is not None)^(traffic_sub.external_group_id is not None)^(traffic_sub.any_ue_ind)):
        print(f"ipv4: {type(traffic_sub.ipv4_addr)}, any ue: {type(traffic_sub.any_ue_ind)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of ipv4Addr, ipv6Addr, macAddr, gpsi, externalGroupId or anyUeInd")
    #---------------------------any ue, gpsi or ext group id------------------------
    if traffic_sub.any_ue_ind or traffic_sub.gpsi or traffic_sub.external_group_id:
        if traffic_sub.any_ue_ind and not traffic_sub.dnn or not traffic_sub.snssai:
            raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
        supi = intGroupId = None
        if traffic_sub.gpsi:
            supi = udm_handler.udm_sdm_id_translation(traffic_sub.gpsi)
        elif traffic_sub.external_group_id:
            intGroupId = udm_handler.udm_sdm_group_identifiers_translation(traffic_sub.external_group_id)
        res = await udr_handler.udr_app_data_insert(traffic_sub, intGroupId, supi)
        if res.status_code == httpx.codes.CREATED:
            sub_id = trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'])
            if sub_id:
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-trafficInfluence/v1/{afId}/subscriptions/{sub_id}"
                traffic_sub.supp_feat = "0"
                headers={'location': traffic_sub.__self, 'content-type': 'application/json'}
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                print("Server error")
                raise HTTPException(status_code=500, detail="Error creating resource")
        else:
            raise HTTPException(status_code=500, detail="Error creating resource")
        
    #------------------------ipv4, ipv6 or eth---------------------------
    else:
        if "BSF" in conf.HOSTS.keys():
            print("Temos BSF!")
        if conf.CORE != "free5gc":
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
            print("No binding")
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
        pcf_binding = PcfBinding.from_dict(res['response'])
        
        res = await pcf_handler.pcf_policy_authorization_create_ti(pcf_binding, traffic_sub)
        if res.status_code == httpx.codes.CREATED:
            sub_id = await trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'])
            if sub_id:
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-traffic-influence/v1/{afId}/subscriptions/{sub_id}"
                headers={'location': traffic_sub.__self, 'content-type': 'application/json'}
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                print("Server error")
                return Response(status_code=500, content="Error creating resource")
    
    return res.status_code

@app.put("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_put(afId, subId, data: Request):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200
    res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=data.json())
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.patch("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_patch(afId, subId, data: Request):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200 
    res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=data.json(), partial=True)
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.get("/delete/{subId}")
async def delete_ti(subId: str):
    afId = "default"
    res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        # print(f"deleting at location: {res['location']}")
        # res :httpx.Response = await delete_req(f"{res['location']}/delete", conf.GLOBAL_HEADERS)
        if res.status_code != httpx.codes.NO_CONTENT:
            print("Context not found!")

        res = await trafficInfluSub.individual_traffic_influence_subscription_delete(afId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")
    
@app.delete("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_delete(afId: str, subId: str):
    res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        print(f"deleting at location: {res['location']}")
        res :httpx.Response = await get_req(f"{res['location']}/delete", conf.GLOBAL_HEADERS)
        if res.status_code != httpx.codes.NO_CONTENT:
            print("Context not found!")

        res = await trafficInfluSub.individual_traffic_influence_subscription_delete(afId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")

@app.post("/pcf-policy-authorization-callback")
async def pcf_callback(data):
    print("-------------------------smf callback msg--------------------")
    print(data)
    return httpx.codes.OK
#--------------------------dummy---------------------------------
@app.post("/dummy/{x}")
async def dummy(x: str, data):
    return f"dummy data: {data} at location {x}"
#---------------------as-session-with-qos------------------------
#
#
@app.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def qos_get(scsAsId: str, subscriptionId: str=None):
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subscriptionId)
    if not res:
        return {"subs": []}
        #raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return {'sub': res}

@app.get("/qget")
async def qget():
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get()
    if not res:
        return {'subs': []}
    return {'subs': res}

# @app.post("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
# async def qos_create(scsAsId: str, data: Request):
@app.get("/qos/{i}")
async def qos_create(i: str):
    scsAsId = "default"
    if i == "0":
        qos_sub: AsSessionWithQoSSubscription = qos_subscription2 #data
    else:
        qos_sub: AsSessionWithQoSSubscription = qos_subscription #data
    if not ((qos_sub.ue_ipv4_addr is not None)^(qos_sub.ue_ipv6_addr is not None)^(qos_sub.mac_addr is not None)):
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of ipv4Addr, ipv6Addr or macAddr")
    if not ((qos_sub.flow_info is not None)^(qos_sub.eth_flow_info is not None)^(qos_sub.exter_app_id is not None)):
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of IP flow info, Ethernet flow info or External Application")
    if (qos_sub.ue_ipv4_addr or qos_sub.ue_ipv6_addr) and not qos_sub.flow_info:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.mac_addr and not qos_sub.eth_flow_info:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if (qos_sub.qos_reference and qos_sub.alt_qos_reqs) or (qos_sub.alt_qo_s_references and qos_sub.alt_qos_reqs):
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.qos_mon_info and qos_sub.events and "QOS_MONITORING" not in qos_sub.events:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.alt_qo_s_references and not qos_sub.notification_destination:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    
    bsf_params = {}
    if qos_sub.ue_ipv4_addr:
        bsf_params['ipv4Addr'] = qos_sub.ue_ipv4_addr
    elif qos_sub.ue_ipv6_addr:
        bsf_params['ipv6Prefix'] = qos_sub.ue_ipv6_addr
    elif qos_sub.mac_addr:
        bsf_params['macAddr48'] = qos_sub.mac_addr

    res = await bsf_handler.bsf_management_discovery(bsf_params)
    if res['code'] != httpx.codes.OK:
        print("No binding")
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
    pcf_binding = PcfBinding.from_dict(res['response'])
    
    response = await pcf_handler.pcf_policy_authorization_create_qos(pcf_binding, qos_sub)
    if response.status_code == httpx.codes.CREATED:
        sub_id = await asSessionWithQoSSub.as_session_with_qos_subscription_insert(scsAsId, qos_sub, response.headers['Location'])
        if sub_id:
            qos_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{sub_id}"
            headers={'location': qos_sub.__self, 'content-type': 'application/json'}
            return JSONResponse(status_code=httpx.codes.CREATED, content=qos_sub.to_dict(), headers=headers)
        else:
            return Response(status_code=500, content="Error creating resource")
    return response

@app.post("/pcf-policy-authorization-qos-callback")
async def pcf_callback(data):
    print("-------------------------smf callback msg--------------------")
    print(data)
    return httpx.codes.OK

@app.put("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def qos_put(scsAsId, subId, data: Request):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scsAsId, subId=subId, sub=data.json())
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.patch("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_patch(afId, subId, data: Request):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200 
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=afId, subId=subId, sub=data.json(), partial=True)
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.get("/qdelete/{subId}")
async def qo_s_delete(subId: str):
    scsAsId = "default"
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        # print(f"deleting at location: {res['location']}")
        # res :httpx.Response = await delete_req(f"{res['location']}/delete")
        if res.status_code != httpx.codes.NO_CONTENT:
            print("Context not found!")

        res = await asSessionWithQoSSub.as_session_with_qos_subscription_delete(scsAsId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")
    
@app.delete("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_delete(scsAsId: str, subId: str):
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        print(f"deleting at location: {res['location']}")
        res :httpx.Response = await get_req(f"{res['location']}/delete", conf.GLOBAL_HEADERS)
        if res.status_code != httpx.codes.NO_CONTENT:
            print("Context not found!")

        res = await trafficInfluSub.individual_traffic_influence_subscription_delete(scsAsId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")

#----------------------clean db-------------------
#
#
@app.get("/clean")
async def clean():
    res = clean_db()
    if res:
        return {"result": "Database cleaned."}
    else:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Error cleaning database!")