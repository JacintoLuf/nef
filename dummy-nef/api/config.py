import os
import uuid
from typing import List
from models.nf_profile import NFProfile
from models.nef_info import NefInfo
from kubernetes import client, config

class Settings():
    def __init__(self):
        self.HOSTS = {}
        self.MONGO_URI = ""
        self.API_UUID = str(uuid.uuid4())

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
            self.API_UUID, nf_type="NEF",
            nf_status="REGISTERED",
            heart_beat_timer=10,
            ipv4_addresses=self.HOSTS["NEF"]
        )

    def set_new_api_uuid(self):
        self.API_UUID = str(uuid.uuid4())
       
        return self.API_UUID
    
    def set_nf_endpoints(self, profiles: List[NFProfile]):
        for profile in profiles:
            self.HOSTS[profile.nf_type] = profile.ipv4_addresses

        return 1

conf = Settings()