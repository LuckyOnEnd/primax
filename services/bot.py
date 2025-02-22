import threading
from config.config import Config
from Scraper import TradingView

bot_thread: threading.Thread | None = None
stop_event = threading.Event()
bot: TradingView | None = None

def run_scrapper(login_id, password, chart_link):
    global bot_thread, bot
    bot_thread = threading.Thread(
        target=Bot, args=(Config.Captcha_API, login_id,
                          password, chart_link)
    )
    bot_thread.start()


def stop_scrapper():
    global bot_thread, bot
    stop_event.set()

    if bot:
        bot.close()

    if bot_thread:
        bot_thread.join()
        bot_thread = None
        bot = None


def Bot(Captcha_API, Username, password, chart_link):
    global bot
    bot = TradingView(Captcha_API, Username, password, stop_event, chart_link)
    bot.Login()
    bot.openChart()
