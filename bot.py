from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os


class FreelanceBot:
    def __init__(self):
        # logging
        self.log_filename = 'offer_log.txt'
        self.write_log('(START TIME: '+datetime.now().strftime("%d-%m-%Y %H:%M:%S")+')')

        p = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'phantomjs.exe')
        self.driver = webdriver.PhantomJS(p)

        self.url = 'https://freelance.ru'
        # настройка rss тут
        # https://freelance.ru/rss/index
        self.rss_url = 'https://freelance.ru/rss/feed/project/s.577.4.590.580.116.565.40.598.584.593.540.98'

        self.lgn = 'yazmolod'
        self.passwd = 'paulallender666'
        self.message = '''Добрый день! Имею богатый опыт выполнения подобной работы, готов обсудить подробности. Буду рад помочь, обращайтесь!'''

        self.welcome_words = ['3d', 'визуализаци', 'печать', 'чертеж', 'stl',
                              'рендер', 'аксонометри', 'визуализатор', 'unity',
                              'модел', '3д', 'архитектор', 'юнити',
                              'zbrush', 'maya', 'revit', 'ревит']
        self.not_welcome_words = ['интерьер',
                                  'django', 'джанго', 'rest', 'сайт', 'видео']

        self.time_long = 300  # seconds = 5min
        self.last_pubdate = ''
        self.submitted_links = []

    def login(self):
        self.driver.get(self.url + '/login')
        self.driver.find_element_by_id('login').send_keys(self.lgn)
        self.driver.find_element_by_id('passwd').send_keys(self.passwd)
        self.driver.find_element_by_name('submit').click()
        print('login successfully...')

    def submit_offer(self, task):
        self.driver.get(task['link'])
        task['client_name'] = self.driver.find_element_by_xpath(r"//div[@class='name']/a").text
        try:
            offer = self.driver.find_element_by_css_selector(
                "a[title='Заявка на участие']")
            if offer.text == 'Предложить услуги':
                href = self.url + offer.get_attribute("href")
                self.driver.get(href)
                cost = self.driver.find_element_by_id('cost')
                if not cost.get_attribute('value'):
                    cost.send_keys('1')
                self.driver.find_element_by_id('msg_body').send_keys(self.message)
                self.driver.find_element_by_xpath(
                    '//*[@id="msg_form"]/input[2]').click()
                self.submitted_links.append(link)
                # Success: offer submitted
                msg = """✓ {title}
                Заказчик: {client_name}
                Время публикации: {pubdate}
                Ссылка: {link}""".format(**task)
                status = True
            else:
                # Unsuccess: offer was already submitted
                msg = """XXX {title}
                Ссылка: {link}""".format(**task)
                status = False
        except:
            # Unsuccess: task is closed, submitted or unavaliable
            msg = """X {title}
            Ссылка: {link}""".format(**task)
            status = False
        return status, msg

    def is_valid_category(self, category):
        return True

    def is_valid_title(self, title):
        title = title.lower()
        welcome_bool = any(
            [i in title for i in self.welcome_words]) if self.welcome_words else True
        not_welcome_bool = not any(
            [i in title for i in self.not_welcome_words])
        return welcome_bool & not_welcome_bool

    def parse_rss(self):
        print ('parse...')
        r = requests.get(self.rss_url)
        result = []
        soup = BeautifulSoup(r.content, 'lxml')
        current_pubdate = soup.find('pubdate').text
        if self.last_pubdate == current_pubdate:
            return None
        else:
            for item in soup.find_all('item'):
                title = item.find('title').text
                description = item.find('description').text
                pubdate = item.find('pubdate').text
                link = item.find('guid').text   #link выдает пустую строку
                category = item.find('category').text
                if self.is_valid_title(title) and link not in self.submitted_links and self.is_valid_category(category):
                    result.append({
                        'title': title,
                        'link': link,
                        'description': description,
                        'pubdate': pubdate,
                        'category': category,
                    })
            self.last_pubdate = current_pubdate
            return result

    def write_log(self, msg):
        print (msg, end='\n\n')
        with open(self.log_filename, 'a') as log:
            log.write(msg)
            log.write('\n\n')

    def process(self):
        while True:
            start_time = time.time()
            tasks = self.parse_rss()
            if tasks:
                print ('offering...\n')
                print ('*'*19, 
                    datetime.now().strftime("[%d-%m-%Y %H:%M:%S]"),
                    '*'*19,
                    sep='\n',
                    end='\n\n')
                for task in tasks:
                    status, msg = self.submit_offer(task)
                    self.write_log(msg)
                end_time = time.time()
                process_time = end_time - start_time
                if process_time < self.time_long:
                    print ('waiting...')
                    time.sleep(self.time_long - process_time)
            else:
                print ('waiting...')
                time.sleep(self.time_long)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    error_count = 0
    while error_count < 5:
        try:
            f = FreelanceBot()
            f.login()
            f.process()
        except (KeyboardInterrupt, SystemExit):
            f.write_log('(END TIME: '+datetime.now().strftime("%d-%m-%Y %H:%M:%S")+')')
            input()
            break
        # except Exception as e:
        #     f.driver.save_screenshot(
        #         './errors_screens/' + datetime.now().strftime("%d-%m-%Y %H:%M:%S") + '.png')
        #     f.driver.quit()
        #     error_count += 1
        #     f.write_log('(ERROR: '+datetime.now().strftime("%d-%m-%Y %H:%M:%S")+')')
        #     print(e)
