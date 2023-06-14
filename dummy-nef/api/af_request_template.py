from models.traffic_influ_sub import TrafficInfluSub

traffic_influ = TrafficInfluSub(
    #af_app_id="63a30a70-72ee-401b-97b3-0b3d9f0404ea",
    af_trans_id="1",
    dnn="internet",
    snssai="111111",
    any_ue_ind=False,
    subscribed_events="",
    ipv4_addr="10.45.0.3",
    notification_destination="cenas",
    #traffic_filters="",
    #eth_traffic_filters="",
    traffic_routes="",

)

imsi = "999700000000001" #imsi/supi
msin = "0000000001"