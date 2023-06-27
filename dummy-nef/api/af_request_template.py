from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
from models.route_to_location import RouteToLocation
from models.route_information import RouteInformation
from models.snssai import Snssai

def create_sub():
    snssai = Snssai()
    snssai.sst=1
    snssai.sd='111111'

    route_info = RouteInformation()
    route_info.ipv4_addr='10.255.32.132'
    route_info.port_number=80

    route_to_loc = RouteToLocation()
    route_to_loc.dnai='1-111111'
    route_to_loc.route_info=route_info

    traffic_influ = TrafficInfluSub()
    traffic_influ.af_service_id='24caa907-f1ba-4e29-8a78-f9728dd45d83',
    #af_app_id='',
    traffic_influ.af_trans_id='1',
    traffic_influ.dnn='internet',
    traffic_influ.snssai=snssai,
    traffic_influ.any_ue_ind=False,
    traffic_influ.subscribed_events='UP_PATH_CHANGE',
    traffic_influ.ipv4_addr='10.45.0.2',
    traffic_influ.notification_destination=f'http://{conf.HOSTS["NEF"][0]}:80/pcf-policy-authorization-callback',
    traffic_influ.traffic_filters='',#-----------------------------------------
    traffic_influ.traffic_routes=[route_to_loc],
    traffic_influ.any_ue_ind=False
    #supp_feat=1 'InfluenceOnTrafficRouting'

    return traffic_influ


sub_template = create_sub()
# imsi = '999700000000001' #imsi/supi
# msin = '0000000001'