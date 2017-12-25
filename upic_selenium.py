from selenium import webdriver
import time
import random
from deathbycaptcha import deathbycaptcha
from PIL import Image
import csv
import os

CANADIAN_PROVINCES = [
    "Ontario",  # apply checkboxes filter
    "Quebec",
    "British Columbia",
    "Alberta",
    "Manitoba",
    "Saskatchewan",
    "Nova Scotia",
    "New Brunswick",
    "Newfoundland",
    "Prince Edward Island",
    "Northwest Territories"
]

SEARCH_CHECKBOXES_IDS = [
    "plcContent_ctl00_chkPPAIMember",
    "plcContent_ctl00_chkUnion",
    "plcContent_ctl00_chkFullfillmentCenter",
    "plcContent_ctl00_chkOnlineCatalog",
    "plcContent_ctl00_chkAcceptsCreditCards",
    "plcContent_ctl00_chkWomanOwned",
    "plcContent_ctl00_chkRushServices",
    "plcContent_ctl00_chkElectronicCatalog",
    "plcContent_ctl00_chkAcceptsUPICCredit",
    "plcContent_ctl00_chkMinorityOwned",
    "plcContent_ctl00_chkMadeInUSA",
    "plcContent_ctl00_chkPrintedCatalog"
]

MIN_PARSED_PAGES_COUNT = 165
MAX_PARSED_PAGES_COUNT = 178

DEATH_BY_CAPTCHA_USERNAME = "CardiffBlues"
DEATH_BY_CAPTCHA_PASSWORD = "dNR3kBQD=nH[i8zvQt4ogqdp6EExPn4By"
CSV_FILE_NAME = "output.csv"
CSV_HEADERS = [
    "Company Name",
    "UPIC",
    "PPAI",
    "PPAI Credit",
    "ESPA",
    "PS",
    "State",
    "Name",
    "E-mail Address",
    "Website",
    "Company Type",
    "Business Description",
    "Line Names",
    "Products",
    "Phone Number",
    "Toll Free",
    "FAX",
    "Toll Free FAX",
    "General E-mail Address",
    "Primary Contact",
    "Company Websites",
    "Mailing",
    "Shipping",
    "Billing",
]


class UpicBaseScrapper:

    def __init__(self):
        # init the webdriver
        self.return_two_pages = False
        self.counter = 0
        self.maximum_profiles_count = random.choice(range(MIN_PARSED_PAGES_COUNT, MAX_PARSED_PAGES_COUNT))
        self.selenium = webdriver.Chrome()
        self.current_page_number = 1
        self.search_url = ""
        self.company = ""
        self.upic = ""
        self.ppai = ""
        self.ppai_credit = ""
        self.epsa = ""
        self.ps = ""
        self.state = ""
        self.name = ""
        self.email = ""
        self.website = ""
        self.company_type = ""
        self.business_discribtion = ""
        self.line_names = ""
        self.products = ""
        self.phone = ""
        self.toll_free = ""
        self.fax = ""
        self.toll_free_fax = ""
        self.general_email = ""
        self.primary_contact = ""
        self.websites = ""
        self.mailing = ""
        self.shipping = ""
        self.billing = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # close the driver
        self.selenium.close()

    def go_to_search_page(self):
        # go to the home page
        self.selenium.get("http://www.upic.org/")

        # insert the email
        self.selenium.find_element_by_id('UserName').send_keys(
            "brendan.singbeil@navigateapparel.com"
        )

        # insert the password
        self.selenium.find_element_by_id('Password').send_keys(
            "haq0nrg4"
        )

        # check remember me
        self.selenium.find_element_by_id('RememberMe').click()

        # press the login button
        self.selenium.find_element_by_id('LoginButton').click()

        # get the frame link
        frame_link = self.selenium.find_element_by_xpath('/html/frameset/frame[2]').get_attribute("src")

        # go to frame link
        self.selenium.get(frame_link)

        # press search link
        self.selenium.find_element_by_id('ctl15_HyperLinkSearch').click()

        # store search url
        self.search_url = self.selenium.current_url

    def go_to_detail_pages(self):
        # for each canadian provinces
        for province in CANADIAN_PROVINCES:
            if province == "Ontario":
                for checkbox_id in SEARCH_CHECKBOXES_IDS:

                    # select checkbox
                    self.selenium.find_element_by_id(checkbox_id).click()

                    self._apply_search(province)
                    self._get_to_detail_page()
            else:
                self._apply_search(province)
                self._get_to_detail_page()

    def _apply_search(self, province):
        # select state
        self.selenium.find_element_by_id('plcContent_ctl00_ddlState').send_keys(province)

        # click submit search
        self.selenium.find_element_by_id('plcContent_ctl00_imgSubmit').click()

        # wait 2 secs
        time.sleep(2)

    def _check_for_captcha(self):

        if "ctlCrawlerKiller" in self.selenium.current_url:
            print("CAPTCHA DETECTED")
            # take a screenshot of the whole page
            captcha_file_name = "screenshot.png"
            self.selenium.save_screenshot(captcha_file_name)
            # crop the screenshot to get the captcha image only
            im = Image.open(captcha_file_name)
            captcha_image = im.crop(
                (420, 250, 600, 300)
            )
            captcha_image.save("captcha_image.png")
            # initiate deathbycaptcha client to solve it
            client = deathbycaptcha.SocketClient(
                DEATH_BY_CAPTCHA_USERNAME,
                DEATH_BY_CAPTCHA_PASSWORD
            )
            try:
                balance = client.get_balance()
                print("balance", balance)

                # Put your CAPTCHA file name or file-like object, and optional
                # solving timeout (in seconds) here:
                captcha = client.decode("captcha_image.png", 500)
                if captcha:
                    # The CAPTCHA was solved; captcha["captcha"] item holds its
                    # numeric ID, and captcha["text"] item its text.
                    print("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))
                    # write captcha and click submit
                    self.selenium.find_element_by_name('ctl00$plcContent$CaptchaControl1').send_keys(captcha["text"])
                    self.selenium.find_element_by_xpath('//input[@type="Submit"]').click()
                    time.sleep(5)
                    self._parse_company_profile_page()
                    return True
                else:
                    print("CAPTCHA not solved", captcha)

            except deathbycaptcha.AccessDeniedException:
                print("Access to DBC API denied, check your credentials and/or balance")

        else:
            self._parse_company_profile_page()
            return False

    def _get_to_detail_page(self):
        # get number of the rows in the current page
        num_rows = len(self.selenium.find_elements_by_xpath('//*[@id="plcContent_ctl00_dgUpicList"]/tbody/tr'))

        for i in range(2, num_rows + 1):
            # get info from the listing table

            self.upic = self.selenium.find_element_by_id(
                'plcContent_ctl00_dgUpicList_lnkUPIC_{}'.format(i - 2)
            ).text

            self.company = self.selenium.find_element_by_id(
                'plcContent_ctl00_dgUpicList_lnkCompany_{}'.format(i - 2)
            ).text

            try:
                self.ppai = self.selenium.find_element_by_id(
                    'plcContent_ctl00_dgUpicList_imgID_{}'.format(i - 2)
                ).get_attribute('title')
            except:
                self.ppai = ""
            try:
                self.ppai_credit = self.selenium.find_element_by_id(
                    'plcContent_ctl00_dgUpicList_imgUPICCredit_{}'.format(i - 2)
                ).get_attribute('title')
            except:
                self.ppai_credit = ""
            try:
                self.epsa = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_dgUpicList"]/tbody/tr[{}]/td[5]'.format(i)
                ).get_attribute('title')
            except:
                self.epsa = ""
            try:
                self.ps = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_dgUpicList"]/tbody/tr[{}]/td[6]'.format(i)
                ).get_attribute('title')
            except:
                self.ps = ""
            try:  #
                self.state = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_dgUpicList"]/tbody/tr[{}]/td[7]'.format(i)
                ).text
            except:
                self.state = ""
            try:
                self.name = self.selenium.find_element_by_id(
                    'plcContent_ctl00_dgUpicList_lnkFirstName_{}'.format(i - 2)
                ).text
            except:
                self.name = ""
            try:
                self.email = self.selenium.find_element_by_id(
                    'plcContent_ctl00_dgUpicList_imgEmail_{}'.format(i - 2)
                ).get_attribute('alt')
            except:
                self.email = ""
            try:
                self.website = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_dgUpicList_lblWesite_{}"]/a[1]'.format(i - 2)
                ).get_attribute('href')
            except:
                self.website = ""

            # check if company profile parsed before
            with open("upic.txt", 'r') as upic_file:
                if self.upic in upic_file.read().split('\n'):
                    continue

            # open the company profile to get more data
            self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_dgUpicList"]/tbody/tr[{}]/td[1]/a'.format(i)
            ).click()
            # check if there is a captcha appeared
            is_captcha_detected = self._check_for_captcha()
            # move back to list page
            if is_captcha_detected or self.return_two_pages:
                self.selenium.execute_script("window.history.go(-2)")
                self.return_two_pages = False
            else:
                self.selenium.execute_script("window.history.go(-1)")

            time.sleep(3)

        # check for pagination, if found, click next
        try:
            paginate_link = self.selenium.find_element_by_id('plcContent_ctl00_lbTopNextPage')
            if len(paginate_link.get_attribute('href').strip()) > 0:
                print("Going to next page")
                paginate_link.click()
                self._get_to_detail_page()
        except:
            print("Pagination done")
            # move back to search page
            self.selenium.get(self.search_url)
            # wait 2 secs
            time.sleep(2)

    def _parse_company_profile_page(self):
        # parse the company profile page for the required information

        try:
            if "Company Type" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[1]/td[1]'
            ).text:
                self.company_type = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[2]/td[1]'
                ).text
        except:
            pass

        try:
            if "Business Description" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[3]/td[1]'
            ).text:
                self.business_discribtion = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[4]/td[1]'
                ).text
        except:
            pass

        # click more products
        try:
            self.selenium.find_element_by_id("productsLink").click()
            self.return_two_pages = True
        except:
            pass

        try:
            if "Line Name" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[5]/td[1]'
            ).text:
                self.line_names = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[6]/td[1]'
                ).text
            elif "Products" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[5]/td[1]'
            ).text:
                self.products = ""
                for element in self.selenium.find_elements_by_xpath(
                    '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[6]/td'
                ):
                    self.products += element.text + "\n"
        except:
            pass

        try:
            if "Products" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[7]/td[1]'
            ).text:
                self.products = ""
                for element in self.selenium.find_elements_by_xpath(
                    '//*[@id="plcContent_ctl00_generalPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[8]/td'
                ):
                    self.products += element.text + "\n"
        except:
            pass

        try:
            if "Phone" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[1]/td[1]'
            ).text:
                self.phone = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[1]/td[2]'
                ).text
        except:
            pass

        try:
            if "Toll Free" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[2]/td[1]'
            ).text:
                self.toll_free = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[2]/td[2]'
                ).text
        except:
            pass

        try:
            if "Fax" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[3]/td[1]'
            ).text:
                self.fax = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[3]/td[2]'
                ).text
        except:
            pass

        try:
            if "Toll Free Fax" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[4]/td[1]'
            ).text:
                self.toll_free_fax = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[4]/td[2]'
                ).text
        except:
            pass

        try:
            if "General Email" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[5]/td[1]'
            ).text:
                self.general_email = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[5]/td[2]'
                ).text
        except:
            pass

        try:
            if "Primary Contact" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[6]/td[1]'
            ).text:
                self.primary_contact = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[6]/td[2]'
                ).text
        except:
            pass

        try:
            if "Websites" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[7]/td[1]'
            ).text:
                self.websites = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_contactPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[7]/td[2]'
                ).text
        except:
            pass

        try:
            if "Mailing" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_addressPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[1]/td[1]'
            ).text:
                self.mailing = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_addressPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[2]/td[1]'
                ).text
        except:
            pass

        try:
            if "Shipping" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_addressPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[3]/td[1]'
            ).text:
                self.shipping = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_addressPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[4]/td[1]'
                ).text
        except:
            pass

        try:
            if "Billing" in self.selenium.find_element_by_xpath(
                '//*[@id="plcContent_ctl00_addressPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[5]/td[1]'
            ).text:
                self.billing = self.selenium.find_element_by_xpath(
                    '//*[@id="plcContent_ctl00_addressPanel"]/fieldset/table/tbody/tr/td[2]/table/tbody/tr[6]/td[1]'
                ).text
        except:
            pass

        self.counter += 1
        print("{}- Company {} parsed successfully".format(self.counter, self.company))
        self._csv_writer()
        time.sleep(2)

        # write the current upic to upic.txt to keep track of all scrapped companies
        with open("upic.txt", "a") as upic_file:
            upic_file.write(self.upic)
            upic_file.write("\n")

        # check the parsing counter
        if self.counter > self.maximum_profiles_count:
            self.selenium.close()

    def _csv_writer(self):
        with open(CSV_FILE_NAME, 'a', newline='') as csvfile:
            content_writer = csv.writer(csvfile, delimiter=',')
            content_writer.writerow(
                [
                    self.company,
                    self.upic,
                    self.ppai,
                    self.ppai_credit,
                    self.epsa,
                    self.ps,
                    self.state,
                    self.name,
                    self.email,
                    self.website,
                    self.company_type,
                    self.business_discribtion,
                    self.line_names,
                    self.products,
                    self.phone,
                    self.toll_free,
                    self.fax,
                    self.toll_free_fax,
                    self.general_email,
                    self.primary_contact,
                    self.websites,
                    self.mailing,
                    self.shipping,
                    self.billing,
                ]
            )

    @staticmethod
    def csv_headers_writer():
        with open(CSV_FILE_NAME, 'w', newline='') as csvfile:
            headers_writer = csv.writer(csvfile, delimiter=',')
            headers_writer.writerow(CSV_HEADERS)


def main():
    # check if CSV_FILE_NAME is already exists
    if not os.path.exists(CSV_FILE_NAME):
        UpicBaseScrapper.csv_headers_writer()
    with UpicBaseScrapper() as scrapper:
        scrapper.go_to_search_page()
        scrapper.go_to_detail_pages()


if __name__ == '__main__':
    main()
