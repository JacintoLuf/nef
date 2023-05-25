import os
import uuid
from models.nf_profile import NFProfile
from kubernetes import client, config

class Settings():
    def __init__(self):
        nfs = ['nrf', 'pcf', 'udm', 'udr', 'bsf']
        try:
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            
            namespace = "open5gs"
            nef_svc_name = "nef"
            nrf_svc_name = "open5gs-nrf"
            pcf_svc_name = "open5gs-pcf"
            udm_svc_name = "open5gs-udm"
            udr_svc_name = "open5gs-udr"
            bsf_svc_name = "open5gs-bsf"

            svc = v1.read_namespaced_service(bsf_svc_name, namespace)
            svc_ip = svc.spec.cluster_ip
            print(f"BSF service IP: {svc_ip}")
        except client.ApiException as e:
            print(e)
        except Exception as e:
            print(e)

        if os.getenv('MONGO_IP') is not None:
            self.MONGO_IP = os.getenv('MONGO_IP')
            print("Mongo DNS resolve docker-compose")
        elif os.getenv('NEF_MONGODB_HOST') is not None:
            self.MONGO_IP = os.getenv('NEF_MONGODB_HOST')
            print("Mongo DNS resolve kubernetes")
        else:
            self.MONGO_IP = "10.109.39.130"
            print("Mongodb manually resolved")
        print("mongo ip: "+self.MONGO_IP)
        self.MONGO_URI = "mongodb://"+self.MONGO_IP+"/nef"    #MONGO_URI = "mongodb://root:pass@nef-mongodb.open5gs.svc.cluster.local:27017/admin?authSource=admin"
        self.FIRST_SUPERUSER = "admin@it.av.pt"
        self.FIRST_SUPERUSER_PASSWORD = "1234"

        self.API_UUID = str(uuid.uuid4())
        
        if os.getenv('NRF_IP') is not None and os.getenv('AMF_IP')  is not None and os.getenv('SMF_IP') is not None:
            self.NRF_IP = os.getenv('NRF_IP')+":7777"
            self.AMF_IP = os.getenv('AMF_IP')+":7777"
            self.SMF_IP = os.getenv('SMF_IP')+":7777"
            print("NFs DNS resolve docker-compose")
        elif os.getenv('OPEN5GS_NRF_SBI_HOST') is not None and os.getenv('OPEN5GS_AMF_SBI_HOST') is not None and os.getenv('OPEN5GS_SMF_SBI_HOST') is not None:
            self.NRF_IP = os.getenv('OPEN5GS_NRF_SBI_HOST')+":7777"
            self.AMF_IP = os.getenv('OPEN5GS_AMF_SBI_HOST')+":7777"
            self.SMF_IP = os.getenv('OPEN5GS_SMF_SBI_HOST')+":7777"
            print("NFs DNS resolve kubernetes")
        else:
            self.NRF_IP = "10.102.176.115:7777"
            self.AMF_IP = "10.101.24.251:7777"
            self.SMF_IP = "10.111.84.210:7777"
            print("NFs manually resolved")

        self.nef_profile = NFProfile(
            self.API_UUID, nf_type="NEF",
            nf_status="REGISTERED",
            heart_beat_timer=10,
            ipv4_addresses=["10.102.141.12"],
            nf_service_list=[],
            nf_profile_changes_support_ind=True
        )

    def set_api_uuid(self, uuid):
        self.API_UUID = uuid
        return None

conf = Settings()