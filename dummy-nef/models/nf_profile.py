import uuid
from datetime import datetime

class NFProfile(object):

    def __init__(self, nf_instance_id=None, nf_type="NEF",
                 nf_status="REGISTERED", heart_beat_timer=None, fqdn=None, ipv4_addresses=["10.102.141.12"],
                 ipv6_addresses=None, nef_info=None, custom_info=None, recovery_time=None,
                 nf_service_persistence=False, nf_services=None, nf_service_list=None,
                 nf_profile_changes_support_ind=True, nf_profile_changes_ind=False, default_notification_subscriptions=None):  # noqa: E501
        """NFProfile - a model defined in Swagger"""  # noqa: E501
        self._nf_instance_id = nf_instance_id
        self.nf_instance_id_gen()
        self._nf_type = "NEF"
        self._nf_status = "REGISTERED"
        self._heart_beat_timer = 10
        self._fqdn = fqdn
        self._ipv4_addresses = ipv4_addresses
        self._ipv6_addresses = ipv6_addresses
        self._nef_info = nef_info
        self._custom_info = custom_info
        self._recovery_time = datetime.now()
        self._nf_service_persistence = nf_service_persistence
        self._nf_services = []
        self._nf_service_list = nf_service_list
        self._nf_profile_changes_support_ind = True
        self._nf_profile_changes_ind = nf_profile_changes_ind
        self._default_notification_subscriptions = default_notification_subscriptions

    @property
    def nf_instance_id(self):
        """Gets the nf_instance_id of this NFProfile.  # noqa: E501

        String uniquely identifying a NF instance. The format of the NF Instance ID shall be a  Universally Unique Identifier (UUID) version 4, as described in IETF RFC 4122.    # noqa: E501

        :return: The nf_instance_id of this NFProfile.  # noqa: E501
        :rtype: str
        """
        return self._nf_instance_id

    @nf_instance_id.setter
    def nf_instance_id(self, nf_instance_id):
        """Sets the nf_instance_id of this NFProfile.

        String uniquely identifying a NF instance. The format of the NF Instance ID shall be a  Universally Unique Identifier (UUID) version 4, as described in IETF RFC 4122.    # noqa: E501

        :param nf_instance_id: The nf_instance_id of this NFProfile.  # noqa: E501
        :type: str
        """
        if nf_instance_id is None:
            raise ValueError("Invalid value for `nf_instance_id`, must not be `None`")  # noqa: E501

        self._nf_instance_id = nf_instance_id

    def nf_instance_id_gen(self):
        self._nf_instance_id = str(uuid.uuid4())

    @property
    def nf_type(self):
        """Gets the nf_type of this NFProfile.  # noqa: E501


        :return: The nf_type of this NFProfile.  # noqa: E501
        :rtype: NFType
        """
        return self._nf_type

    @nf_type.setter
    def nf_type(self, nf_type):
        """Sets the nf_type of this NFProfile.


        :param nf_type: The nf_type of this NFProfile.  # noqa: E501
        :type: NFType
        """
        if nf_type is None:
            raise ValueError("Invalid value for `nf_type`, must not be `None`")  # noqa: E501

        self._nf_type = nf_type

    @property
    def nf_status(self):
        """Gets the nf_status of this NFProfile.  # noqa: E501


        :return: The nf_status of this NFProfile.  # noqa: E501
        :rtype: NFStatus
        """
        return self._nf_status

    @nf_status.setter
    def nf_status(self, nf_status):
        """Sets the nf_status of this NFProfile.


        :param nf_status: The nf_status of this NFProfile.  # noqa: E501
        :type: NFStatus
        """
        if nf_status is None:
            raise ValueError("Invalid value for `nf_status`, must not be `None`")  # noqa: E501

        self._nf_status = nf_status

    @property
    def heart_beat_timer(self):
        """Gets the heart_beat_timer of this NFProfile.  # noqa: E501


        :return: The heart_beat_timer of this NFProfile.  # noqa: E501
        :rtype: int
        """
        return self._heart_beat_timer

    @property
    def fqdn(self):
        """Gets the fqdn of this NFProfile.  # noqa: E501


        :return: The fqdn of this NFProfile.  # noqa: E501
        :rtype: Fqdn
        """
        return self._fqdn

    @fqdn.setter
    def fqdn(self, fqdn):
        """Sets the fqdn of this NFProfile.


        :param fqdn: The fqdn of this NFProfile.  # noqa: E501
        :type: Fqdn
        """

        self._fqdn = fqdn

    @heart_beat_timer.setter
    def heart_beat_timer(self, heart_beat_timer):
        """Sets the heart_beat_timer of this NFProfile.


        :param heart_beat_timer: The heart_beat_timer of this NFProfile.  # noqa: E501
        :type: int
        """

        self._heart_beat_timer = heart_beat_timer
    
    @property
    def ipv4_addresses(self):
        """Gets the ipv4_addresses of this NFProfile.  # noqa: E501


        :return: The ipv4_addresses of this NFProfile.  # noqa: E501
        :rtype: list[str]
        """
        return self._ipv4_addresses

    @ipv4_addresses.setter
    def ipv4_addresses(self, ipv4_addresses):
        """Sets the ipv4_addresses of this NFProfile.


        :param ipv4_addresses: The ipv4_addresses of this NFProfile.  # noqa: E501
        :type: list[str]
        """

        self._ipv4_addresses = ipv4_addresses

    @property
    def ipv6_addresses(self):
        """Gets the ipv6_addresses of this NFProfile.  # noqa: E501


        :return: The ipv6_addresses of this NFProfile.  # noqa: E501
        :rtype: list[AllOfNFProfileIpv6AddressesItems]
        """
        return self._ipv6_addresses

    @ipv6_addresses.setter
    def ipv6_addresses(self, ipv6_addresses):
        """Sets the ipv6_addresses of this NFProfile.


        :param ipv6_addresses: The ipv6_addresses of this NFProfile.  # noqa: E501
        :type: list[AllOfNFProfileIpv6AddressesItems]
        """

        self._ipv6_addresses = ipv6_addresses

    @property
    def nef_info(self):
        """Gets the nef_info of this NFProfile.  # noqa: E501


        :return: The nef_info of this NFProfile.  # noqa: E501
        :rtype: NefInfo
        """
        return self._nef_info

    @nef_info.setter
    def nef_info(self, nef_info):
        """Sets the nef_info of this NFProfile.


        :param nef_info: The nef_info of this NFProfile.  # noqa: E501
        :type: NefInfo
        """

        self._nef_info = nef_info

    @property
    def custom_info(self):
        """Gets the custom_info of this NFProfile.  # noqa: E501


        :return: The custom_info of this NFProfile.  # noqa: E501
        :rtype: object
        """
        return self._custom_info

    @custom_info.setter
    def custom_info(self, custom_info):
        """Sets the custom_info of this NFProfile.


        :param custom_info: The custom_info of this NFProfile.  # noqa: E501
        :type: object
        """

        self._custom_info = custom_info

    @property
    def recovery_time(self):
        """Gets the recovery_time of this NFProfile.  # noqa: E501

        string with format 'date-time' as defined in OpenAPI.  # noqa: E501

        :return: The recovery_time of this NFProfile.  # noqa: E501
        :rtype: datetime
        """
        return self._recovery_time

    @recovery_time.setter
    def recovery_time(self, recovery_time):
        """Sets the recovery_time of this NFProfile.

        string with format 'date-time' as defined in OpenAPI.  # noqa: E501

        :param recovery_time: The recovery_time of this NFProfile.  # noqa: E501
        :type: datetime
        """

        self._recovery_time = recovery_time

    @property
    def nf_service_persistence(self):
        """Gets the nf_service_persistence of this NFProfile.  # noqa: E501


        :return: The nf_service_persistence of this NFProfile.  # noqa: E501
        :rtype: bool
        """
        return self._nf_service_persistence

    @nf_service_persistence.setter
    def nf_service_persistence(self, nf_service_persistence):
        """Sets the nf_service_persistence of this NFProfile.


        :param nf_service_persistence: The nf_service_persistence of this NFProfile.  # noqa: E501
        :type: bool
        """

        self._nf_service_persistence = nf_service_persistence

    @property
    def nf_services(self):
        """Gets the nf_services of this NFProfile.  # noqa: E501


        :return: The nf_services of this NFProfile.  # noqa: E501
        :rtype: list[NFService]
        """
        return self._nf_services

    @nf_services.setter
    def nf_services(self, nf_services):
        """Sets the nf_services of this NFProfile.


        :param nf_services: The nf_services of this NFProfile.  # noqa: E501
        :type: list[NFService]
        """

        self._nf_services = nf_services

    @property
    def nf_service_list(self):
        """Gets the nf_service_list of this NFProfile.  # noqa: E501


        :return: The nf_service_list of this NFProfile.  # noqa: E501
        :rtype: dict(str, NFService)
        """
        return self._nf_service_list

    @nf_service_list.setter
    def nf_service_list(self, nf_service_list):
        """Sets the nf_service_list of this NFProfile.


        :param nf_service_list: The nf_service_list of this NFProfile.  # noqa: E501
        :type: dict(str, NFService)
        """

        self._nf_service_list = nf_service_list

    @property
    def nf_profile_changes_support_ind(self):
        """Gets the nf_profile_changes_support_ind of this NFProfile.  # noqa: E501


        :return: The nf_profile_changes_support_ind of this NFProfile.  # noqa: E501
        :rtype: bool
        """
        return self._nf_profile_changes_support_ind

    @nf_profile_changes_support_ind.setter
    def nf_profile_changes_support_ind(self, nf_profile_changes_support_ind):
        """Sets the nf_profile_changes_support_ind of this NFProfile.


        :param nf_profile_changes_support_ind: The nf_profile_changes_support_ind of this NFProfile.  # noqa: E501
        :type: bool
        """

        self._nf_profile_changes_support_ind = nf_profile_changes_support_ind

    @property
    def nf_profile_changes_ind(self):
        """Gets the nf_profile_changes_ind of this NFProfile.  # noqa: E501


        :return: The nf_profile_changes_ind of this NFProfile.  # noqa: E501
        :rtype: bool
        """
        return self._nf_profile_changes_ind

    @nf_profile_changes_ind.setter
    def nf_profile_changes_ind(self, nf_profile_changes_ind):
        """Sets the nf_profile_changes_ind of this NFProfile.


        :param nf_profile_changes_ind: The nf_profile_changes_ind of this NFProfile.  # noqa: E501
        :type: bool
        """

        self._nf_profile_changes_ind = nf_profile_changes_ind

    @property
    def default_notification_subscriptions(self):
        """Gets the default_notification_subscriptions of this NFProfile.  # noqa: E501


        :return: The default_notification_subscriptions of this NFProfile.  # noqa: E501
        :rtype: list[DefaultNotificationSubscription]
        """
        return self._default_notification_subscriptions

    @default_notification_subscriptions.setter
    def default_notification_subscriptions(self, default_notification_subscriptions):
        """Sets the default_notification_subscriptions of this NFProfile.


        :param default_notification_subscriptions: The default_notification_subscriptions of this NFProfile.  # noqa: E501
        :type: list[DefaultNotificationSubscription]
        """

        self._default_notification_subscriptions = default_notification_subscriptions

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(NFProfile, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, NFProfile):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
