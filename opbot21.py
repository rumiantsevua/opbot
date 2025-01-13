import imaplib
import email
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bdpass import EMAIL, PASSWORD_EMAIL, FROM_ADDRESS_BD

# Параметри підключення
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = EMAIL
PASSWORD = PASSWORD_EMAIL

# Параметр пошуку, у даному випадку емейл відправника
FROM_ADDRESS = FROM_ADDRESS_BD

# Ініціалізація змінної останнбого обробленого листа
last_processed_email_id = None

def connect_to_mailbox():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")
    return mail

def load_random_review(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        reviews = file.readlines()
    return random.choice(reviews).strip()

# Initialize mail connection
mail = connect_to_mailbox()
status, messages = mail.search(None, f'FROM "{FROM_ADDRESS}" UNSEEN')
email_ids = messages[0].split()
if email_ids:
    last_processed_email_id = email_ids[-1]
    print("OpBOT v1.2-COOKIE EDITION Rumiantsev - The last email is found and saved, waiting for new emails...")
else:
    print("There are no emails from the specified sender.")
mail.logout()

try:
    while True:
        mail = connect_to_mailbox()
        status, messages = mail.search(None, f'FROM "{FROM_ADDRESS}" UNSEEN')
        email_ids = messages[0].split()

        if email_ids:
            latest_email_id = email_ids[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            try:
                msg = email.message_from_bytes(raw_email)

                html_content = None
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            html_content = part.get_payload(decode=True).decode(errors='replace')
                else:
                    html_content = msg.get_payload(decode=True).decode(errors='replace')

                # Помітка що лист прочитаний
                mail.store(latest_email_id, '+FLAGS', '\\Seen')
                last_processed_email_id = latest_email_id

                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    images = soup.find_all('img', src=lambda x: x and "opinion_rating_5" in x)

                    positive_links = []
                    for img in images:
                        link = img.find_parent('a')
                        if link and 'href' in link.attrs:
                            positive_links.append(link['href'])

                    if positive_links:
                        review_link = positive_links[0]

                        chrome_options = Options()
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_argument("--no-sandbox")
                        chrome_options.add_argument("--window-size=1920x1080")
                        chrome_options.add_argument("--enable-unsafe-webgl")
                        chrome_options.add_argument("--enable-unsafe-swiftshader")

                        driver = webdriver.Chrome(options=chrome_options)
                        driver.get(review_link)

                        # Додатковий час, щоб сторінка точно завантажилася
                        time.sleep(5)  

                        # Якщо з'являється вікно з підтвердженням кукі:
                        try:
                            cookie_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, "//a[@href='#rejectAll' and contains(text(),'Potwierdzam wymagane')]")
                                )
                            )
                            cookie_button.click()
                            print("Cookie confirmation clicked.")
                            time.sleep(1)
                        except:
                            # Якщо кнопка не з'являється, то пропускаємо це
                            print("No cookie confirmation was displayed or failed to click.")

                        # Скріншот для дебагу
                        driver.save_screenshot("debug_screenshot.png")

                        # Відправлення відгуку про замовлення
                        order_review = load_random_review("op.txt")
                        order_review_label = WebDriverWait(driver, 30).until(
                            EC.visibility_of_element_located(
                                (By.XPATH,
                                 "//label[contains(text(), 'Napisz swoją opinię o obsłudze zamówienia')]")
                            )
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", order_review_label)
                        order_review_field = order_review_label.find_element(By.XPATH, "preceding-sibling::textarea")
                        order_review_field.clear()
                        order_review_field.send_keys(order_review)
                        time.sleep(1)

                        submit_button = WebDriverWait(driver, 30).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(text(), 'Wyślij nam swoją opinię')]")
                            )
                        )
                        submit_button.click()
                        time.sleep(1)

                        # Відправлення відгуку про товар
                        product_review = load_random_review("opop.txt")
                        product_review_label = WebDriverWait(driver, 30).until(
                            EC.visibility_of_element_located(
                                (By.XPATH,
                                 "//label[contains(text(), 'Napisz swoją opinię o produkcie')]")
                            )
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", product_review_label)
                        product_review_field = product_review_label.find_element(By.XPATH, "preceding-sibling::textarea")
                        product_review_field.clear()
                        product_review_field.send_keys(product_review)
                        time.sleep(1)

                        submit_button_product = WebDriverWait(driver, 30).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(text(), 'Wyślij opinię')]")
                            )
                        )
                        submit_button_product.click()

                        time.sleep(2)
                        print("Reviews successfully submitted.")
                        driver.quit()
                else:
                    print("HTML content not found in the email.")
            except UnicodeDecodeError as e:
                print(f"Error decoding email: {e}")
        else:
            print("No new emails.")

        mail.logout()
        # 30 хвилин (1800 сек) + невелика пауза
        time.sleep(1860)

except KeyboardInterrupt:
    print("Email checking manually stopped.")
