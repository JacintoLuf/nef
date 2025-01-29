import time
import httpx
from main import app
from fastapi import Request, Response, HTTPException
from api.config import conf
from models.pcf_binding import PcfBinding
from models.ue_id_req import UeIdReq
from models.ue_id_info import UeIdInfo
import core.bsf_handler as bsf_handler
import core.udm_handler as udm_handler


@app.post("/3gpp-ue-id/v1/retrieve")
async def ue_id_retrieval(data: Request):
    start_time = time()
    try:
        data_dict = await data.json()
        ue_req = UeIdReq.from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    
    if ue_req.ue_ip_addr and ue_req.ue_mac_addr:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of UeIpAddr, UeMacAddr")

    if ue_req.ip_domain and not ue_req.ue_ip_addr:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Cannot parse message. No UE ip address.")

    if "BSF" in conf.HOSTS.keys():
        bsf_params = {}
        if ue_req.ue_ip_addr:
            if ue_req.ue_ip_addr.ipv4_addr:
                bsf_params['ipv4Addr'] = ue_req.ue_ip_addr.ipv4_addr
            if ue_req.ue_ip_addr.ipv6_addr:
                bsf_params['ipv6Addr'] = ue_req.ue_ip_addr.ipv6_addr
        elif ue_req.ue_mac_addr:
            bsf_params['macAddr48'] = ue_req.ue_mac_addr

        res = await bsf_handler.bsf_management_discovery(bsf_params)
        if res['code'] != httpx.codes.OK:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
        pcf_binding = PcfBinding.from_dict(res['response'])
        if not pcf_binding.supi:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="UE_ID_NOT_AVAILABLE") ###############################3

    translated_id = await udm_handler.udm_sdm_id_translation(pcf_binding.supi, ue_req)

    ue_info = UeIdInfo(external_id=translated_id)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content=ue_info)