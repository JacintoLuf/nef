import os
import uuid
from typing import List
from models.nf_profile import NFProfile
from models.nf_service import NFService
from models.nf_service_version import NFServiceVersion
from kubernetes import client, config

class Settings():
    def __init__(self):
        self.NAME = os.environ['NAME']
        self.CORE = os.environ['CORE_5G']
        self.NAMESPACE = os.environ['NAMESPACE']
        self.PLMN = os.environ['PLMN']
        print(f'deploy name: {self.NAME}')
        print(f'core: {self.CORE}')
        print(f'namespace: {self.NAMESPACE}')
        print(f'plmn: {self.PLMN}')

        self.HOSTS = {}
        self.MONGO_URI = ""
        self.API_UUID = str(uuid.uuid4())
        self.GLOBAL_HEADERS = {
            'Accept': 'application/json,application/problem+json',
            'Content-Type': 'application/json',
            'charsets': 'utf-8',
        }

        service_names = [] #[('','')]
        self.SERVICE_LIST = {}

        for svc_name, supp_feat in service_names:
            base_svc = self.create_svc(svc_name, supp_feat)
            self.SERVICE_LIST[svc_name] = base_svc

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
            ipv4_addresses=[self.HOSTS["NEF"][0][:-5]],
            nf_service_list=self.SERVICE_LIST,
            nef_info=None
        )

        self.NF_SCOPES = {
            #"NRF": "nnrf-nfm nnrf-disc nnrf-oauth2",
            "AMF": "namf-evts",
            "SMF": "event-exposure",
            "BSF": "nbsf-management",
            "PCF": "npcf-policyauthorization npcf-eventexposure",
            "UDR": "nudr-dr",
            "UDM": "nudm-sdm nudm-uecm nudm-ueau",
        }
    
    
    def create_svc(self, svc_name, supp_feat, oauth=False):
        return NFService(service_instance_id=str(uuid.uuid4()),
                             service_name=svc_name,
                             versions=NFServiceVersion("v1", "1.0.0"),
                             scheme="http",
                             nf_service_status="REGISTERED",
                             supported_features=supp_feat,
                             oauth2_required=oauth)

    def set_nf_endpoints(self, profiles: List[NFProfile] = None, instances = None):
        if profiles:
            for profile in profiles:
                if profile.nf_type in self.HOSTS:
                    self.HOSTS[profile.nf_type].append(f"{profile.ipv4_addresses[0]}:{'80' if self.CORE=='free5gc' else '7777'}")
                else:
                    self.HOSTS[profile.nf_type] = [f"{profile.ipv4_addresses[0]}:{'80' if self.CORE=='free5gc' else '7777'}"]

    def update_values(self, profile):
        config.load_incluster_config()
        v1 = client.CoreV1Api()

        for key, value in profile.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.update_values(item)
            elif isinstance(value, dict):
                self.update_values(value)
            if  key == "ipv4Addresses":
                for i, addr in enumerate(profile[key]):
                    svc = v1.read_namespaced_service(addr, self.NAMESPACE)
                    profile[key][i] = svc.spec.cluster_ip
            elif key == "ipv4Address":
                svc = v1.read_namespaced_service(profile[key], self.NAMESPACE)
                profile[key] = svc.spec.cluster_ip
        return profile

conf = Settings()