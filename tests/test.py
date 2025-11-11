from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import time
import os

class OpenBMCConfig:
    def __init__(self):
        self.base_url = "https://localhost:2443"
        self.credentials = {
            "valid": {
                "username": "vostrik",
                "password": "Lolkek123"
            },
            "invalid": {
                "username": "vostrik", 
                "password": "wrongpass"
            }
        }

class TestDriver:
    def __init__(self):
        self.driver = None
    
    def setup(self):
        options = webdriver.ChromeOptions()
        
        # Обязательные опции для работы в контейнере
        options.add_argument('--headless=new')  # Новый headless режим
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        
        # Для отладки можно добавить
        options.add_argument('--verbose')
        options.add_argument('--log-path=/tmp/chromedriver.log')
        
        # Используем системный Chromium
        options.binary_location = '/usr/bin/chromium'
        
        try:
            # Пробуем с service
            service = Service(
                '/usr/bin/chromedriver',
                service_args=['--verbose', '--log-path=/tmp/chromedriver.log']
            )
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"Chrome with service failed: {e}")
            # Fallback: пробуем без service
            try:
                self.driver = webdriver.Chrome(options=options)
            except Exception as e2:
                print(f"Chrome without service failed: {e2}")
                raise
        
        self.driver.implicitly_wait(10)
        return self.driver
    
    def cleanup(self):
        if self.driver:
            self.driver.quit()

class BMCTestSuite:
    def __init__(self):
        self.config = OpenBMCConfig()
        self.driver_manager = TestDriver()
        self.driver = None
    
    def sleep(self, milliseconds):
        time.sleep(milliseconds / 1000)
    
    def wait_for_element(self, by, selector, timeout=10):
        """Ждать появления элемента"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    
    def block_user_after_incorrect_credential(self):
        """Тест блокировки пользователя после нескольких неверных попыток входа"""
        self.driver = self.driver_manager.setup()
        
        try:
            self.sleep(2000)
            
            self.driver.get(self.config.base_url)
            print("Страница загружена")
            
            # Ждем появления полей ввода
            username_field = self.wait_for_element(By.CSS_SELECTOR, '[data-test-id="login-input-username"]')
            password_field = self.wait_for_element(By.CSS_SELECTOR, '[data-test-id="login-input-password"]')
            
            for i in range(4):
                username_field.clear()
                username_field.send_keys(self.config.credentials["invalid"]["username"])
                
                password_field.clear()
                password_field.send_keys(self.config.credentials["invalid"]["password"])
                
                login_button = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="login-button-submit"]')
                login_button.click()
                self.sleep(3000)
            
            username_field.clear()
            username_field.send_keys(self.config.credentials["valid"]["username"])
            
            password_field.clear()
            password_field.send_keys(self.config.credentials["valid"]["password"])
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="login-button-submit"]')
            login_button.click()
            self.sleep(3000)
            
            self.driver.back()
            
            try:
                error_alert = self.driver.find_element(By.CSS_SELECTOR, "div.alert.alert-danger")
                print("✓ Пользователь заблокирован")
                return True
            except NoSuchElementException:
                raise Exception("Пользователь не был заблокирован")
                
        except Exception as e:
            print(f"Ошибка в блокировке пользователя: {e}")
            self.driver.save_screenshot('error_block_user.png')
            raise
        finally:
            self.driver_manager.cleanup()
    
    def test_login_invalid_credentials(self):
        """Тест входа с неверными учетными данными"""
        self.driver = self.driver_manager.setup()
        
        try:
            self.driver.get(self.config.base_url)
            print("Страница загружена для теста неверных данных")
            
            # Ждем появления полей ввода
            username_field = self.wait_for_element(By.CSS_SELECTOR, '[data-test-id="login-input-username"]')
            password_field = self.wait_for_element(By.CSS_SELECTOR, '[data-test-id="login-input-password"]')
            
            username_field.send_keys(self.config.credentials["invalid"]["username"])
            password_field.send_keys(self.config.credentials["invalid"]["password"])
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="login-button-submit"]')
            login_button.click()
            
            self.sleep(3000)
            self.driver.back()
            
            try:
                error_alert = self.driver.find_element(By.CSS_SELECTOR, "div.alert.alert-danger")
                print("✓ Ошибка при неверных пользовательских данных")
                return True
            except NoSuchElementException:
                raise Exception("Ошибка при неверных пользовательских данных не была найдена")
                
        except Exception as e:
            print(f"Ошибка в тесте неверных данных: {e}")
            self.driver.save_screenshot('error_invalid_login.png')
            raise
        finally:
            self.driver_manager.cleanup()
    
    def test_login_success(self):
        """Тест успешного входа в систему"""
        self.driver = self.driver_manager.setup()
        
        try:
            self.driver.get(self.config.base_url)
            print("Страница загружена для успешного входа")
            
            # Ждем появления полей ввода
            username_field = self.wait_for_element(By.CSS_SELECTOR, '[data-test-id="login-input-username"]')
            password_field = self.wait_for_element(By.CSS_SELECTOR, '[data-test-id="login-input-password"]')
            
            username_field.send_keys(self.config.credentials["valid"]["username"])
            password_field.send_keys(self.config.credentials["valid"]["password"])
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, '[data-test-id="login-button-submit"]')
            login_button.click()
            
            try:
                overview_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-v-51f73898]"))
                )
                overview_text = overview_element.text
                
                if overview_text == "Overview":
                    print("✓ Успешный логин, Overview загружен")
                    return True
                else:
                    raise Exception(f"Ожидался Overview, но получен: {overview_text}")
                    
            except TimeoutException:
                raise Exception("Страница Overview не загрузилась")
                
        except Exception as e:
            print(f"Ошибка в тесте успешного входа: {e}")
            self.driver.save_screenshot('error_success_login.png')
            raise
        finally:
            self.driver_manager.cleanup()

def run_all_tests():
    """Запуск всех тестов"""
    test_suite = BMCTestSuite()
    
    print("Запуск тестов BMC...")
    
    try:
        # print("\n1. Тест успешного входа:")
        # test_suite.test_login_success()
        
        print("\n2. Тест входа с неверными данными:")
        test_suite.test_login_invalid_credentials()
        
        print("\n3. Тест блокировки пользователя:")
        test_suite.block_user_after_incorrect_credential()
        
        print("\n✓ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"\n✗ Тест провален: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)