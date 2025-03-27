import threading
from config.config import Config
from Scraper import TradingView, CredentialException

bot_thread: threading.Thread | None = None
stop_event = threading.Event()
bot: TradingView | None = None

def run_scrapper(login_id, password, chart_link, email):
    global bot_thread, bot
    print('event stop')
    stop_event.clear()
    print('create thread')
    bot_thread = threading.Thread(
        target=Bot, args=(Config.Captcha_API, login_id,
                          password, chart_link, email)
    )
    print('start thread')
    bot_thread.start()
    print('started')

def stop_scrapper():
    global bot_thread, bot
    stop_event.set()

    if bot:
        bot.close()

    if bot_thread:
        bot_thread.join()
        bot_thread = None
        bot = None


def Bot(Captcha_API, Username, password, chart_link, email):
    global bot
    bot = TradingView(Captcha_API, Username, password, stop_event, chart_link, email)
    count = 0
    #for x in range(0, 10):
    try:
        bot.Login()
        #break
    except Exception as e:
        count += 1
        print(f'{e}\nTry again: {count}')

    if count == 10:
        stop_scrapper()
        return
    bot.openChart()
