from models.traffic_influ_sub import TrafficInfluSub
from models.route_to_location import RouteToLocation
from models.route_information import RouteInformation

route_info = RouteInformation(
    ipv4_addr="",
    ipv6_addr="",
    port_number=""
)

route_to_loc = RouteToLocation(
    dnai="",
    route_info=route_info,
    route_prof_id=""
)

traffic_influ = TrafficInfluSub(
    af_service_id="24caa907-f1ba-4e29-8a78-f9728dd45d83",
    #af_app_id="",
    af_trans_id="1",
    dnn="internet",
    snssai="111111",
    any_ue_ind=False,
    subscribed_events="",
    ipv4_addr="10.45.0.3",
    notification_destination="uri",
    traffic_filters="",#-----------------------------------------
    traffic_routes=route_to_loc,
    temp_validities="",
    supp_feat="InfluenceOnTrafficRouting"

)

imsi = "999700000000001" #imsi/supi
msin = "0000000001"