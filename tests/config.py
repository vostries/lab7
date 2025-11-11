class BmcConfig:
    IP = '127.0.0.1'
    PORT = 2443
    BASE_URL = f'https://{IP}:{PORT}'
    CREDENTIALS = {
        'login': 'root',
        'password': '0penBmc'
    }