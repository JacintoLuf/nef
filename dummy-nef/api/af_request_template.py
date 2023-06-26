from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
from models.route_to_location import RouteToLocation
from models.route_information import RouteInformation
from models.snssai import Snssai

def create_sub():
    snssai = Snssai(1, "111111")

    route_info = RouteInformation(
        ipv4_addr="10.255.32.132",
        ipv6_addr="",
        port_number="80"
    )

    route_to_loc = RouteToLocation(
        dnai="1-111111",
        route_info=route_info
    )

    traffic_influ = TrafficInfluSub(
        af_service_id="24caa907-f1ba-4e29-8a78-f9728dd45d83",
        #af_app_id="",
        af_trans_id="1",
        dnn="internet",
        snssai=snssai,
        any_ue_ind=False,
        subscribed_events="UP_PATH_CHANGE",
        ipv4_addr="10.45.0.2",
        notification_destination=f"http://{conf.HOSTS['NEF'][0]}:80/pcf-policy-authorization-callback",
        traffic_filters="",#-----------------------------------------
        traffic_routes=[route_to_loc],
        temp_validities="",
        #supp_feat=1 "InfluenceOnTrafficRouting"
    )
    print(traffic_influ.notification_destination)
    print("---------------------to dict----------------------")
    print(traffic_influ.to_dict())
    return traffic_influ

# imsi = "999700000000001" #imsi/supi
# msin = "0000000001"