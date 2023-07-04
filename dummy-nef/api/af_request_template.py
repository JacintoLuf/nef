#from datetime import datetime, timedelta
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
from models.route_to_location import RouteToLocation
from models.route_information import RouteInformation
from models.flow_info import FlowInfo
from models.snssai import Snssai

def create_sub():
    snssai = Snssai(sst=1, sd="0x111111")
    route_info = RouteInformation(ipv4_addr="10.255.32.132", port_number=80)
    route_to_loc = RouteToLocation(dnai="internet", route_info=route_info, route_prof_id='default')
    flow_infu = FlowInfo(flow_id=10, flow_descriptions="permit out ip from 10.45.0.2 to 10.255.32.132")
    flow_infu2 = FlowInfo(flow_id=11, flow_descriptions="permit in ip from 10.255.32.132 to 10.45.0.2")
    #temp_val = TemporalValidity(str(datetime.now()), str(datetime.now()+timedelta(minutes=10)))

    traffic_influ = TrafficInfluSub(
        af_service_id="24caa907-f1ba-4e29-8a78-f9728dd45d83",
        #af_app_id="udp-server1",
        af_trans_id="1",
        #app_relo_ind=False,
        dnn="internet",
        #snssai=snssai,
        any_ue_ind=True,
        subscribed_events="UP_PATH_CHANGE",
        #ipv4_addr="10.45.0.2",
        #dnai_chg_type="EARLY_LATE",
        notification_destination=f"http://{conf.HOSTS['NEF'][0]}:80/pcf-policy-authorization-callback",
        traffic_filters=[flow_infu, flow_infu2],
        request_test_notification=True,
        traffic_routes=[route_to_loc],
        #temp_validities=[temp_val],
        addr_preser_ind=True,
    )
    return traffic_influ

influ_sub = create_sub()