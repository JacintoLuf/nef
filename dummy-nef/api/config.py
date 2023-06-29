import os
import uuid
#from datetime import datetime, timedelta
from typing import List
from models.nf_profile import NFProfile
from models.traffic_influ_sub import TrafficInfluSub
from models.route_to_location import RouteToLocation
from models.route_information import RouteInformation
from models.temporal_validity import TemporalValidity
from models.dnai_change_type import DnaiChangeType
from models.snssai import Snssai
from kubernetes import client, config

class Settings():
    def __init__(self):
        self.HOSTS = {}
        self.MONGO_URI = ""
        self.API_UUID = str(uuid.uuid4())
        self.GLOBAL_HEADERS = {'Accept': 'application/json,application/problem+json'}

        try:
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            
            namespace = "open5gs"
            #mongodb_svc_name = "nef-mongodb"
            mongodb_svc_name = "open5gs-mongodb"
            nef_svc_name = "nef"
            nrf_svc_name = "open5gs-nrf-sbi"

            # Get mongodb service ip
            svc = v1.read_namespaced_service(mongodb_svc_name, namespace)
            self.HOSTS["MONGODB"] = svc.spec.cluster_ip
            self.MONGO_IP = svc.spec.cluster_ip
            self.MONGO_URI = "mongodb://"+svc.spec.cluster_ip+"/nef"    
            #print(f"MONGODB service IP: {svc.spec.cluster_ip}")
            # Get nef service ip
            svc = v1.read_namespaced_service(nef_svc_name, namespace)
            self.HOSTS["NEF"] = [svc.spec.cluster_ip]
            #print(f"NEF service IP: {svc.spec.cluster_ip}")
            # Get nef service ip
            svc = v1.read_namespaced_service(nrf_svc_name, namespace)
            self.HOSTS["NRF"] = [svc.spec.cluster_ip]
            self.MONGO_IP = svc.spec.cluster_ip+":7777"
            #print(f"NRF service IP: {svc.spec.cluster_ip}")
        except client.ApiException as e:
            print(e)
            if os.getenv('MONGO_IP') is not None:
                self.HOSTS["MONGODB"] = os.getenv('MONGO_IP')
                self.MONGO_URI = "mongodb://"+self.HOSTS["MONGODB"]+"/nef" 
                print("Mongo DNS resolve docker-compose: "+self.HOSTS["MONGODB"])
            else:
                self.HOSTS["MONGODB"] = "10.109.39.130"
                print("Mongodb manually resolved: "+self.HOSTS["MONGODB"])

            if os.getenv('NRF_IP') is not None:
                self.HOSTS["NRF"] = os.getenv('NRF_IP')
                print("NFs DNS resolve docker-compose: "+self.HOSTS["NRF"])
            else:
                self.HOSTS["NRF"] = "10.102.176.115:7777"
                print("NRFs manually resolved: "+self.HOSTS["NRF"])



        #MONGO_URI = "mongodb://root:pass@nef-mongodb.open5gs.svc.cluster.local:27017/admin?authSource=admin"
        #self.MONGO_URI = "mongodb://"+self.MONGO_IP+"/nef"
        self.FIRST_SUPERUSER = "admin@it.av.pt"
        self.FIRST_SUPERUSER_PASSWORD = "1234"    

        self.NEF_PROFILE = NFProfile(
            nf_instance_id=self.API_UUID,
            nf_type="NEF",
            nf_status="REGISTERED",
            heart_beat_timer=60,
            ipv4_addresses=self.HOSTS["NEF"]
        )

        self.SUB_TEMP = TrafficInfluSub(
            af_service_id="24caa907-f1ba-4e29-8a78-f9728dd45d83",
            #af_app_id="udp-server1",
            af_trans_id="1",
            #app_relo_ind=False,
            dnn="internet",
            snssai= Snssai(sst=1, sd="111111"),
            any_ue_ind=False,
            subscribed_events="UP_PATH_CHANGE",
            ipv4_addr="10.45.0.2",
            dnai_chg_type="EARLY_LATE",
            notification_destination=f"http://{self.HOSTS['NEF'][0]}:80/pcf-policy-authorization-callback",
            #traffic_filters="",
            traffic_routes=[RouteToLocation(dnai="1-111111", route_info=RouteInformation(ipv4_addr="10.255.32.132", port_number=80))],
            #temp_validities=[temp_val],
            addr_preser_ind=True,
            supp_feat="InfluenceOnTrafficRouting"
        )

    def set_new_api_uuid(self):
        self.API_UUID = str(uuid.uuid4())
       
        return self.API_UUID
    
    def set_nf_endpoints(self, profiles: List[NFProfile]):
        for profile in profiles:
            self.HOSTS[profile.nf_type] = profile.ipv4_addresses

        return 1
    
    def create_sub(self):
        snssai = Snssai(sst=1, sd="111111")
        route_info = RouteInformation(ipv4_addr="10.255.32.132", port_number=80)
        route_to_loc = RouteToLocation(dnai="1-111111", route_info=route_info)
        #temp_val = TemporalValidity(str(datetime.now()), str(datetime.now()+timedelta(minutes=10)))

        traffic_influ = TrafficInfluSub(
            af_service_id="24caa907-f1ba-4e29-8a78-f9728dd45d83",
            #af_app_id="udp-server1",
            af_trans_id="1",
            #app_relo_ind=False,
            dnn="internet",
            snssai=snssai,
            any_ue_ind=False,
            subscribed_events="UP_PATH_CHANGE",
            ipv4_addr="10.45.0.2",
            dnai_chg_type="EARLY_LATE",
            notification_destination=f"http://{self.HOSTS['NEF'][0]}:80/pcf-policy-authorization-callback",
            #traffic_filters="",
            traffic_routes=[route_to_loc],
            #temp_validities=[temp_val],
            addr_preser_ind=True,
            supp_feat="InfluenceOnTrafficRouting"
        )
        return traffic_influ.to_dict()

conf = Settings()