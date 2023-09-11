#from datetime import datetime, timedelta
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
from models.route_to_location import RouteToLocation
from models.route_information import RouteInformation
from models.flow_info import FlowInfo
from models.snssai import Snssai
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
from models.alternative_service_requirements_data import AlternativeServiceRequirementsData


def create_sub():
    route_info = RouteInformation(ipv4_addr="10.255.32.123", port_number=80)
    route_to_loc = RouteToLocation(dnai="internet", route_info=route_info)
    flow_info = FlowInfo(flow_id=1,
                        flow_descriptions=["permit out ip from any to 10.255.32.132 80", "permit out ip from 10.255.32.132 to any"])

    traffic_influ = TrafficInfluSub(
        af_trans_id="1",
        dnn="internet",
        any_ue_ind=False,
        subscribed_events="UP_PATH_CHANGE",
        ipv4_addr="10.45.0.4",
        notification_destination=f"http://{conf.HOSTS['NEF'][0]}:7777/pcf-policy-authorization-callback",
        traffic_filters=[flow_info],
        request_test_notification=True,
        traffic_routes=[route_to_loc],
        #addr_preser_ind=True,
        supp_feat="F",
    )
    return traffic_influ

def create_sub2():
    snssai = Snssai(sst=1, sd="0x111111")
    route_info = RouteInformation(ipv4_addr="10.255.32.132", port_number=80)
    route_to_loc = RouteToLocation(dnai="internet", route_info=route_info)
    flow_info = FlowInfo(flow_id=10,
                         flow_descriptions=["permit out ip from any to 10.255.32.132 80", "permit out ip from 10.255.32.132 to 10.45.0.0/16"])
    
    traffic_influ = TrafficInfluSub(
        af_trans_id="2",
        dnn="internet",
        snssai=snssai,
        any_ue_ind=True,
        #subscribed_events="UP_PATH_CHANGE",
        notification_destination=f"http://{conf.HOSTS['NEF'][0]}:7777/pcf-policy-authorization-callback",
        traffic_filters=[flow_info],
        request_test_notification=True,
        traffic_routes=[route_to_loc],
        #dnai_chg_type="LATE",
        #addr_preser_ind=True,
        supp_feat="0",
    )
    return traffic_influ

def create_sub3():
    snssai = Snssai(sst=1, sd="0x111111")
    flow_info = FlowInfo(flow_id=10,
                         flow_descriptions=["permit out ip from 10.45.0.0/16 to 10.255.32.123 80", "permit out ip from 10.255.32.123 to 10.45.0.0/16"])

    
    qos_sub = AsSessionWithQoSSubscription(
        dnn="internet",
        snssai=snssai,
        supported_features="18000",
        notification_destination="http://10.102.141.12:7777/pcf-policy-authorization-qos-callback",
        flow_info=[flow_info],
        qos_reference="1",
        alt_qo_s_references=["7","80"],
        ue_ipv4_addr="10.45.0.4",
        # tsc_qos_req=TscQosRequirement(req_gbr_dl=100000000,
        #                               req_gbr_ul=1000000,
        #                               req_mbr_dl=10000000,
        #                               req_mbr_ul=1000000,
        #                               max_tsc_burst_size=100000,
        #                               req5_gsdelay=3,
        #                               priority=1),
    )
    return qos_sub

def create_sub4():
    snssai = Snssai(sst=1, sd="0x111111")
    flow_info = FlowInfo(flow_id=10,
                         flow_descriptions=["permit out ip from 10.45.0.0/16 to 10.255.32.123 80", "permit out ip from 10.255.32.123 to 10.45.0.0/16"])

    alt_reqs =  AlternativeServiceRequirementsData(
        alt_qos_param_set_ref="big file dl",
        gbr_dl=1024,
        gbr_ul=1024,
        pdb=1
    )

    qos_sub = AsSessionWithQoSSubscription(
        dnn="internet",
        snssai=snssai,
        supported_features="18000",
        notification_destination="http://10.102.141.12:7777/pcf-policy-authorization-qos-callback",
        flow_info=[flow_info],
        alt_qos_reqs=[alt_reqs],
        ue_ipv4_addr="10.45.0.4",
    )
    return qos_sub

influ_sub = create_sub()
any_influ_sub = create_sub2()
qos_subscription = create_sub3()
any_qos_sub = create_sub4()