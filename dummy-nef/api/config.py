import os
import uuid
from typing import List
from models.nf_profile import NFProfile
from kubernetes import client, config

class Settings():
    def __init__(self):
        self.NF_IP = {}
        self.MONGO_IP = ""
        self.API_UUID = str(uuid.uuid4())
        
        try:
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            
            namespace = "open5gs"
            mongodb_svc_name = "nef-mongodb"
            nef_svc_name = "nef"
            nrf_svc_name = "open5gs-nrf-sbi"

            # Get mongodb service ip
            svc = v1.read_namespaced_service(mongodb_svc_name, namespace)
            self.NF_IP["mongodb"] = [svc.spec.cluster_ip]
            self.MONGO_IP = svc.spec.cluster_ip
            print(f"MONGODB service IP: {svc.spec.cluster_ip}")
            # Get nef service ip
            svc = v1.read_namespaced_service(nef_svc_name, namespace)
            self.NF_IP["nef"] = [svc.spec.cluster_ip]
            print(f"NEF service IP: {svc.spec.cluster_ip}")
            # Get nef service ip
            svc = v1.read_namespaced_service(nrf_svc_name, namespace)
            self.NF_IP["nrf"] = [svc.spec.cluster_ip]
            print(f"NRF service IP: {svc.spec.cluster_ip}")
        except client.ApiException as e:
            print(e)
            if os.getenv('MONGO_IP') is not None:
                self.MONGO_IP = os.getenv('MONGO_IP')
                print(f"Mongo DNS resolve docker-compose: {self.MONGO_IP}")
            else:
                self.MONGO_IP = "10.109.39.130"
                print(f"Mongodb manually resolved: {self.MONGO_IP}")

            if os.getenv('NRF_IP') is not None:
                self.NRF_IP = os.getenv('NRF_IP')+":7777"
                print(f"NFs DNS resolve docker-compose: {self.NRF_IP}")
            else:
                self.NRF_IP = "10.102.176.115:7777"
                print(f"NRFs manually resolved: {self.NRF_IP}")



        #MONGO_URI = "mongodb://root:pass@nef-mongodb.open5gs.svc.cluster.local:27017/admin?authSource=admin"
        self.MONGO_URI = "mongodb://"+self.MONGO_IP+"/nef"    
        self.FIRST_SUPERUSER = "admin@it.av.pt"
        self.FIRST_SUPERUSER_PASSWORD = "1234"    

        self.NEF_PROFILE = NFProfile(
            self.API_UUID, nf_type="NEF",
            nf_status="REGISTERED",
            heart_beat_timer=10,
            ipv4_addresses=self.NF_IP["NEF"],
            nf_service_list=[],
            nf_profile_changes_support_ind=True
        )

    def set_api_uuid(self, uuid):
        self.API_UUID = uuid
       
        return 1
    
    def set_nf_endpoints(self, profiles: List[NFProfile]):
        for profile in profiles:
            self.NF_IP[profile.nf_type] = profile.ipv4_addresses

        return 1

conf = Settings()