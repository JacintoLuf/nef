import os
import uuid
from typing import List
from models.nf_profile import NFProfile
from models.nf_service import NFService
from kubernetes import client, config

class Settings():
    def __init__(self):
        self.CORE = os.environ['CORE_5G']
        self.NAMESPACE = os.environ['NAMESPACE']
        print(f"core: {self.CORE}")
        print(f'namespace: {self.NAMESPACE}')

        self.HOSTS = {}
        self.MONGO_URI = ""
        self.API_UUID = str(uuid.uuid4())
        self.GLOBAL_HEADERS = {'Accept': 'application/json,application/problem+json'}

        try:
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            
            svc_list = v1.list_namespaced_service(namespace=self.NAMESPACE)
            nrf_svc = []
            mongo_svc = [svc for svc in svc_list.items if "mongodb" in svc.metadata.name]
            self.HOSTS["MONGODB"] = mongo_svc[0].spec.cluster_ip
            self.MONGO_URI = "mongodb://"+mongo_svc[0].spec.cluster_ip+"/nef"
            if self.CORE == "open5gs":
                nrf_svc = [svc for svc in svc_list.items if "nrf-sbi" in svc.metadata.name]
            else:
                nrf_svc = [svc for svc in svc_list.items if "nrf" in svc.metadata.name]
            if nrf_svc:
                for svc in nrf_svc:
                    if "NRF" in self.HOSTS:
                        self.HOSTS["NRF"].append(f"{svc.metadata.name}:{svc.spec.ports[0].port}")
                    else:
                        self.HOSTS["NRF"] = [f"{svc.metadata.name}:{svc.spec.ports[0].port}"]

            svc = v1.read_namespaced_service("nef", self.NAMESPACE)
            self.HOSTS["NEF"] = [f"{svc.spec.cluster_ip}:{svc.spec.ports[0].port}"]
        
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

        self.NEF_PROFILE = NFProfile(
            nf_instance_id=self.API_UUID,
            nf_type="NEF",
            nf_status="REGISTERED",
            heart_beat_timer=3600,
            ipv4_addresses=self.HOSTS["NEF"],
            nf_services=[],
            nef_info=None
        )

        self.NF_SCOPES = {
            "NRF": "nnrf-nfm nnrf-disc nnrf-oauth2",
            "AMF": "namf-evts",
            "SMF": "event-exposure",
            "BSF": "nbsf-management",
            "PCF": "npcf-policyauthorization npcf-eventexposure",
            "UDR": "nudr-dr",
            "UDM": "nudm-sdm nudm-uecm nudm-ueau",
        }

    def set_new_api_uuid(self):
        self.API_UUID = str(uuid.uuid4())
       
        return self.API_UUID
    
    def set_nf_endpoints(self, profiles: List[NFProfile] = None, instances = None):
        print("printing instances")
        print(instances)
        if profiles:
            for profile in profiles:
                if profile.nf_type in self.HOSTS:
                    self.HOSTS[profile.nf_type].append(f"{profile.ipv4_addresses}:7777")
                else:
                    self.HOSTS[profile.nf_type] = [f"{profile.ipv4_addresses}:7777"]
        # elif instances:
        #     for instance in instances:
        #         if instance['nfType'] in self.HOSTS:
        #             self.HOSTS[instance['nfType']].append(instance['ipv4Addresses'])
        #         else:
        #             self.HOSTS[instance['nfType']] = [instance['ipv4Addresses']]


conf = Settings()