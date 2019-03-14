from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os


class FreelanceBot:
    def __init__(self):
        print('Start working\n')

        # logging
        self.success_file = open('success.txt', 'a')
        self.success_file.write(
            datetime.now().strftime("%d-%m-%Y %H:%M:%S") + '\n\n')
        self.fail_file = open('fail.txt', 'a')
        self.fail_file.write(datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S") + '\n\n')
        self.success_count = 0
        self.fail_count = 0

        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'phantomjs.exe')
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
                              'модел', 'python', '3д', 'архитектор', 'юнити',
                              'zbrush', 'maya', 'revit', 'ревит']
        self.not_welcome_words = ['интерьер',
                                  'django', 'джанго', 'rest', 'сайт', 'видео', 'json']

        self.time_long = 300  # seconds = 5min
        self.last_pubdate = ''
        self.submitted_guids = []

    def login(self):
        self.driver.get(self.url + '/login')
        self.driver.find_element_by_id('login').send_keys(self.lgn)
        self.driver.find_element_by_id('passwd').send_keys(self.passwd)
        self.driver.find_element_by_name('submit').click()
        print('Login is successful\n')

    def submit_offer(self, task_url):
        self.driver.get(task_url)
        try:
            offer = self.driver.find_element_by_css_selector(
                "a[title='Заявка на участие']")
            # offer = self.driver.find_element_by_xpath('//*[@id="discussion_div"]/div[2]/a')
        except:
            print('Fail: task is closed\n')
            return False
        if offer.text == 'Предложить услуги':
            offer.click()
            cost = self.driver.find_element_by_id('cost')
            if not cost.get_attribute('value'):
                cost.send_keys('1')
            self.driver.find_element_by_id('msg_body').send_keys(self.message)
            self.driver.find_element_by_xpath(
                '//*[@id="msg_form"]/input[2]').click()
            print('Success: offer submitted\n')
            return True
        else:
            print('Unsuccess: offer was already submitted\n')
            return False

    def is_valid_title(self, title):
        title = title.lower()
        welcome_bool = any(
            [i in title for i in self.welcome_words]) if self.welcome_words else True
        not_welcome_bool = not any(
            [i in title for i in self.not_welcome_words])
        return welcome_bool & not_welcome_bool

    def parse_rss(self):
        r = requests.get(self.rss_url)
        links = []
        titles = []
        soup = BeautifulSoup(r.content, 'lxml')
        pubdate = soup.find('pubdate').text
        if self.last_pubdate == pubdate:
            return None
        else:
            for item in soup.find_all('item'):
                title = item.find('title').text
                if not self.is_valid_title(title):
                    continue
                link = item.find('guid').text
                if link not in self.submitted_guids:
                    titles.append(title)
                    links.append(link)
                    self.submitted_guids.append(link)
            self.last_pubdate = pubdate
            return list(zip(titles, links))

    def process(self):
        while True:
            start_time = time.time()
            tasks = self.parse_rss()
            if tasks:
                for task in tasks:
                    if self.is_valid_title(task[0]):
                        print(task[0])
                        print(task[1])
                        ok = self.submit_offer(task[1])
                        if ok:
                            self.success_file.write(
                                task[0] + '\n' + task[1] + '\n\n')
                            self.success_count += 1
                        else:
                            self.fail_file.write(
                                task[0] + '\n' + task[1] + '\n\n')
                            self.fail_count += 1
            end_time = time.time()
            process_time = end_time - start_time
            if process_time < self.time_long:
                print('Waiting %d seconds for next cycle...' %
                      (self.time_long - process_time))
                time.sleep(self.time_long - process_time)
            print("Ok, it's time for next cycle\n")


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    error_count = 0
    while error_count < 5:
        try:
            f = FreelanceBot()
            f.login()
            f.process()
        except (KeyboardInterrupt, SystemExit):
            print("Bot's work is stopped: %d accepted tasks, %d declined tasks. See logs for more information" %
                  (f.success_count, f.fail_count))
            f.success_file.close()
            f.fail_file.close()
            input()
            break
        except Exception as e:
            f.driver.save_screenshot(
                './errors_screens/' + datetime.now().strftime("%d-%m-%Y %H:%M:%S") + '.png')
            f.driver.quit()
           # error_count += 1
            print('Something is wrong')
            print(e)
