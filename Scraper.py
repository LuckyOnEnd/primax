from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from database.connection import key_col, Connection
from helper.utils import read_cookies_file
from selenium_stealth import stealth
from twocaptcha import TwoCaptcha
from time import sleep
import random

from tradingbinance.Binaceapi import BinanceApi
from tradingbinance.mt5 import MT5


class CredentialException(Exception):
    pass

class TradingView:
    def __init__(
            self,
            Captcha_API,
            Username,
            password,
            stop_event,
            chart_link,
            email
    ):
        if not Captcha_API or not Username or not password:
            raise ValueError("Captcha_API, Username, and Password must be provided.")
        self.email = email
        self.stop_event = stop_event
        self.chart_link = chart_link
        self.username=Username
        self.password=password
        self.options=self.chromeOptions()
        self.solver=TwoCaptcha(Captcha_API)
        self.driver=webdriver.Chrome(options=self.options, service=Service(ChromeDriverManager().install()))
        self.apply_sealth(self.driver)

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

    def apply_cookies(self):
        self.driver.get("https://www.tradingview.com/")
        sleep(2)

        cookies = read_cookies_file("local/cookies.json")
        for cookie in cookies:
            self.driver.add_cookie(cookie)

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
                    token = self.solve_captcha()
                    self.driver.execute_script(
                        "document.querySelector('#g-recaptcha-response').innerText = arguments[0];",
                        token
                    )

                    sleep(1)
                    iframe = WebDriverWait(self.driver, 20).until(
                        EC.frame_to_be_available_and_switch_to_it(
                            (By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')
                        )
                    )

                    click_checkbox = self.driver.find_element(
                        By.XPATH, '//*[@id="recaptcha-anchor"]'
                        )
                    click_checkbox.click()

                    self.driver.switch_to.default_content()

                    sleep(2)

                    self.driver.execute_script(
                        """
                            var overlay = document.querySelector('div[style="width: 100%; height: 100%; position: fixed; top: 0px; left: 0px; z-index: 2000000000; background-color: rgb(255, 255, 255); opacity: 0.05;"]');
                            if (overlay) {
                                overlay.style.display = 'none';  // Скроем его
                            }
                        """
                        )

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
         #self.apply_cookies()#todo
         try:
             sign_up_btn=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[3]/div[4]/div/div[2]/div/div[2]/button[1]/span')))
             sign_up_btn.click()
             sleep(1)
             try:
                sign_in=WebDriverWait(self.driver,10).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[8]/div/div/div[1]/div/div[2]/div[3]/p/a')))
                sign_in.click()
                sleep(1)
                self.call_enter_credentials()
                sleep(5)
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located(
                            (By.XPATH,
                             '//span[contains(text(), "Invalid username or password")]')
                        )
                    )

                    raise CredentialException('Authorize was not success')
                except TimeoutException:
                    pass
                try:
                    sign_in = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//span[text()='Sign in']"))
                    )
                    raise Exception('Authorize was not successful')
                except TimeoutException:
                    pass
             except TimeoutException as e:
                print('we unable to look signin link')   
         except TimeoutException as e:
             print('sign_up_btn not found')
        except Exception as e:
            raise

    def adjust_quantity(self, symbol, quantity, binance):
        exchange_info = binance.futures_exchange_info(symbol)
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                step_size = Decimal(symbol_info['filters'][1]['stepSize'])
                return Decimal(quantity).quantize(
                    step_size, rounding=ROUND_DOWN
                )
        return quantity

    def analyzeChart(self):
        try:
            cursor = Connection.get_cursor()
            alert_selector = '.highlighted-ucBqatk5'
            last_signal = None
            hide_repeat = 0
            while not self.stop_event.is_set():
                try:
                    get_alerts = WebDriverWait(self.driver, 20).until(
                        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, alert_selector))
                    )
                    get_alerts = get_alerts[::-1]
                    for get_alert in get_alerts:
                        msg = get_alert.text
                        if not msg.strip():
                            continue

                        print(f"\n\nAlert received: {msg}\nTime {datetime.now()}\n\n")
                        # if msg == 'This website uses cookies. Our policy.\nManage\nAccept all':
                        #     close_buttons = get_alert.find_elements(
                        #         By.XPATH,
                        #         "//*[contains(@class, 'acceptAll-ICNSJWAI apply-overflow-tooltip apply-overflow-tooltip--check-children apply-overflow-tooltip--allow-text button-D4RPB3ZC xsmall-D4RPB3ZC black-D4RPB3ZC primary-D4RPB3ZC stretch-D4RPB3ZC apply-overflow-tooltip apply-overflow-tooltip--check-children-recursively apply-overflow-tooltip--allow-text apply-common-tooltip')]"
                        #     )
                        #
                        #     if close_buttons:
                        #         close_buttons[-1].click()

                        message_split = msg.split('\n')
                        time = None
                        symbol_value = None

                        try:
                            signal = message_split[0]
                            symbol_value = message_split[1]
                            time = message_split[2]
                        except:
                            pass

                        if not time:
                            try:
                                get_time = get_alert.find_element(
                                    By.XPATH, ".//div[contains(@class, 'attributes-PQUvhamm')]//span[2]"
                                    )
                                time = get_time.text
                            except TimeoutException as e:
                                print('Miss Time')

                        if not symbol_value:
                            symbol_value = self.get_symbol(get_alert)

                        signal = None
                        if 'Buy Signal'.lower() in msg.lower():
                            signal = 'Buy'
                        elif 'Sell Signal'.lower() in msg.lower():
                            signal = 'Sell'
                        elif 'BTP Signal'.lower() in msg.lower():
                            signal = 'BTP'
                        elif 'STP Signal'.lower() in msg.lower():
                            signal = 'STP'
                        elif 'BSL Signal'.lower() in msg.lower():
                            signal = 'BSL'
                        elif 'SSL Signal'.lower() in msg.lower():
                            signal = 'SSL'
                        else:
                            print('')

                        if signal:
                            print(f'Received {signal} f{datetime.now()}')
                            if last_signal == signal:
                                hide_repeat += 1
                                if hide_repeat >= 10:
                                    print(f'Last signal was receiver {signal} {datetime.now()}')
                                    try:
                                        get_alert.click()
                                        self.driver.find_element(By.TAG_NAME, 'body').click()
                                        hide_repeat = 0
                                    except ElementClickInterceptedException:
                                        print("Element click intercepted! Refreshing the page...")
                                        self.driver.refresh()
                                        hide_repeat = 0
                                continue

                            last_signal = signal

                            cursor.execute("SELECT * FROM keyCollection WHERE email = ?", (self.email,))
                            result = cursor.fetchone()
                            if result is None:
                                continue

                            mt5 = MT5(int(result[1]), result[2], result[3])

                            symbol = symbol_value
                            if symbol_value.__contains__(".P"):
                                symbol = symbol_value.split(".P")[0]

                            amount = result[5]

                            data = {
                                'type': 'future',#todo
                                'Price': 1,
                                'Symbol': symbol,
                                'Time': time,
                                'Signal': signal,
                                'Quantity': float(0.01),
                                'PositionOpened': datetime.now(),
                                'Email': self.email,
                            }

                            if data['Price'] and data['Signal'] and data['Symbol']:
                                try:
                                    if data.get('Signal') == 'Buy' or data.get('Signal') == 'Sell':
                                        mt5.open_trade(data)
                                    else:
                                        mt5.close_trade(data)

                                    try:
                                        get_alert.click()
                                        self.driver.find_element(By.TAG_NAME, 'body').click()
                                    except ElementClickInterceptedException:
                                        print("Element click intercepted! Refreshing the page...")
                                        self.driver.refresh()

                                    #self.hide_alert(get_alert, symbol_value)
                                except Exception as e:
                                    print(f'Error while opening order in Binance: {e}')
                            else:
                                print(f'Order was ignored {data}\nTime: {datetime.now()}\n\n')

                        sleep(1)
                        continue
                except StaleElementReferenceException as e:
                    continue
                except TimeoutException as e:
                    pass
                    sleep(1)
                except Exception as e:
                    sleep(1)
                    if "element not interactable" in str(e):
                        continue
                    print(f'Exception handled: {e}')

        except Exception as e:
            pass

    @staticmethod
    def get_symbol(get_alert):
        try:
            get_symbol = get_alert.find_element(
                By.CSS_SELECTOR, 'span.ticker-PQUvhamm'
            )
            symbol = get_symbol.text
            return symbol
        except TimeoutException as e:
            print('Miss Symbol')
            return None

    @staticmethod
    def hide_alert(get_alert, symbol: str | None):
        try:
            get_symbol = TradingView.get_symbol(get_alert)
            if get_symbol and get_symbol != symbol:
                return

            close_buttons = get_alert.find_elements(
                By.XPATH,
                "//*[contains(@class, 'closeButton-ZZzgDlel') and .//*[contains(text(), 'Close')]]"
            )

            if close_buttons:
                close_buttons[-1].click()
                print(f'Closed alert {datetime.now()}')
        except TimeoutException as e:
            print('Unable To Close It')
        except StaleElementReferenceException as e:
            sleep(1)

    def openChart(self):
        try:
            self.driver.get(self.chart_link)
            sleep(1)
            self.analyzeChart()
        except Exception as e:
            print('Got Error while opening chart')

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
