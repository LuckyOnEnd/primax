from playwright.sync_api import Cookie
import json

from dataclasses import dataclass
from typing import List, Optional
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import logging
from datetime import datetime


def get_logger(logging_format='[%(asctime)s] [%(levelname)s] %(message)s', logging_file='logs.log'):
    class TimeFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            ct = datetime.fromtimestamp(record.created)
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            return t

    # Create or retrieve the logger
    logger = logging.getLogger(__name__)

    # Check if the logger already has handlers to avoid adding them multiple times
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        formatter = TimeFormatter(logging_format)

        # Create a file handler
        file_handler = logging.FileHandler(logging_file, encoding='utf-8')
        file_handler.setFormatter(formatter)

        # Create a stream handler (for displaying logs in the terminal)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Add both handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


def read_cookies_file(file_name):
    # Create an empty list to store cookies
    cookies = []

    # Open the specified file for reading
    with open(file_name, mode='r') as f:
        # Load the JSON data from the file and extract the 'cookies' key
        cookies_json = json.load(f)['cookies']

    # Iterate through the cookies in the JSON data
    for c in cookies_json:
        # Normalize the 'sameSite' attribute values for consistency
        if c['sameSite'] in ['unspecified', 'no_restriction']:
            c['sameSite'] = 'None'

        if c['sameSite'] == 'lax':
            c['sameSite'] = 'Lax'

        if c['sameSite'] == 'strict':
            c['sameSite'] = 'Strict'

        # Create a Cookie object using the attributes from the JSON data and append it to the list
        cookies.append(Cookie(**c))

    # Return the list of cookies
    return cookies

@dataclass
class Alert:
    aria_posinset: Optional[str] = None
    aria_setsize: Optional[str] = None
    title: Optional[str] = None
    ticker_symbol: Optional[str] = None
    ticker_url: Optional[str] = None
    alert_description: Optional[str] = None
    time: Optional[str] = None

    @classmethod
    def from_html(cls, html: str) -> List["Alert"]:
        """
        Parse the given HTML string and return a list of Alert instances.
        """
        soup = BeautifulSoup(html, "html.parser")
        alerts = []

        # select all <li> elements with the specific class
        li_elements = soup.select("li.item-JUpQSPBo")

        for li_element in li_elements:
            # Extract data
            aria_posinset = li_element.get("aria-posinset")
            aria_setsize = li_element.get("aria-setsize")

            # The main title (e.g. "Alert on")
            title_el = li_element.select_one("div.title-_YHAw05g .text-_YHAw05g")
            title_text = title_el.get_text(strip=True) if title_el else None

            # Ticker link & symbol (e.g. "BTCUSDT.P")
            ticker_link = li_element.select_one("a.tickerBox-_YHAw05g")
            if ticker_link:
                symbol_el = ticker_link.select_one(".text-LoO6TyUc")
                ticker_symbol = symbol_el.get_text(strip=True) if symbol_el else None
                ticker_url = ticker_link.get("href")
            else:
                ticker_symbol = None
                ticker_url = None

            # The alert description (e.g. "Sell Signal")
            desc_el = li_element.select_one("span.description-FoZESLBk")
            alert_description = desc_el.get_text(strip=True) if desc_el else None

            # Time (e.g. "17:20:42")
            time_el = li_element.select_one("span.time-m_7l3VrU")
            time_text = time_el.get_text(strip=True) if time_el else None

            # Create Alert instance
            alert = cls(
                aria_posinset=aria_posinset,
                aria_setsize=aria_setsize,
                title=title_text,
                ticker_symbol=ticker_symbol,
                ticker_url=ticker_url,
                alert_description=alert_description,
                time=time_text
            )

            alerts.append(alert)

        return alerts



    def __eq__(self, other) -> bool:
        if not isinstance(other, Alert):
            return NotImplemented
        return (
            self.title == other.title
            and self.ticker_symbol == other.ticker_symbol
            and self.ticker_url == other.ticker_url
            and self.alert_description == other.alert_description
            and self.time == other.time
        )


class AlertManager:
    def __init__(self):
        self.alerts: List[Alert] = []

    def is_new_alert(self, alert: Alert) -> bool:
        """
        Checks if the given alert is new.
        Returns True if the alert is not already present in the alerts list.
        """
        return alert not in self.alerts

    def add_alert(self, alert: Alert) -> None:
        """
        Adds a new alert to the alerts list if it's not already present.
        """
        if self.is_new_alert(alert):
            self.alerts.append(alert)


