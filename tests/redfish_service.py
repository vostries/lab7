import requests
from config import BmcConfig
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RedfishService:
    def __init__(self):
        self.base_url = BmcConfig.BASE_URL
        self.session = requests.Session()
        self.session.auth = (BmcConfig.CREDENTIALS['login'], BmcConfig.CREDENTIALS['password'])
        self.session.verify = False
        self.session.headers.update({'Content-Type': 'application/json'})

    def auth(self):
        """Аутентификация"""
        url = f"{self.base_url}/redfish/v1/SessionService/Sessions"
        data = {
            "UserName": BmcConfig.CREDENTIALS['login'],
            "Password": BmcConfig.CREDENTIALS['password']
        }
        return self.session.post(url, json=data)

    def get_system_info(self):
        """Получение информации о системе"""
        url = f"{self.base_url}/redfish/v1/Systems/system"
        return self.session.get(url)

    def get_thermal_info(self):
        """Получение термической информации"""
        url = f"{self.base_url}/redfish/v1/Chassis/chassis/Thermal"
        return self.session.get(url)

    def get_processors(self):
        """Получение информации о процессорах"""
        url = f"{self.base_url}/redfish/v1/Systems/system/Processors"
        return self.session.get(url)

    def toggle_server_status(self, reset_type: str):
        """Управление питанием сервера"""
        url = f"{self.base_url}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        data = {
            "ResetType": reset_type
        }
        return self.session.post(url, json=data)