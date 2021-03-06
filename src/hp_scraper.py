import re
import smtplib
import ssl
import time
import getpass
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


def send_email(subject, msg, port=587, smtp_server="smtp.office365.com"):
    message = 'Subject: {}\n\n{}'.format(subject, msg)
    context = ssl.create_default_context()
    email = user_hp + "@etu.unice.fr"
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(email, password_hp)
        server.sendmail(email, email, message)


def wait_for_element_by_id(id_e):
    while True:
        try:
            browser.find_element_by_id(id_e)
            break
        except NoSuchElementException:
            pass
    return browser.find_element_by_id(id_e)


def extract_avg_grades(): return \
    map(lambda x: re.search(r"(\d+,\d+)", x).group(0),
        wait_for_element_by_id(hp_element_id["AVG_MARKS"]).text.split("\n"))


def extract_all_grades():
    marks = wait_for_element_by_id(hp_element_id["ALL_MARKS"]).text.split("\n")
    grades = [g.group(1) for g in list(map(lambda x: re.search(r'^\s\s(\d+,\d+)', x), marks)) if
              g is not None]
    labels = [lbl.group(0) for lbl in list(map(lambda x: re.search(r'^[A-Z].*', x),
                                               marks)) if
              lbl is not None and not lbl.string.startswith('Moy')]
    return set(map(lambda x: tuple((x[0], x[1])), zip(labels, grades)))


user_hp = getpass.getpass("Username: ")
password_hp = getpass.getpass()
print("Init ...")

hp_element_id = {"AVG_MARKS": "GInterface.Instances[1].Instances[3]_piedDeListe",
                 "SEMESTERS": "GInterface.Instances[1].Instances[1]",
                 "S9": "GInterface.Instances[1].Instances[1]_1",
                 "BODY": "GInterface.Instances[1]",
                 "MARKS_SECTION": "GInterface.Instances[0].Instances[1]_Combo1",
                 "ALL_MARKS": "GInterface.Instances[1].Instances[3]_Contenu_1"}
# Selenium config
op = webdriver.ChromeOptions()
op.add_argument('--headless')
op.add_argument('window-size=1920x1080')
browser = webdriver.Chrome(options=op)

# Login in HyperPlanning
browser.get("http://sco.polytech.unice.fr/1/")
username, password = browser.find_element_by_id("username"), browser.find_element_by_id("password")
username.send_keys(user_hp), password.send_keys(password_hp)
browser.find_element_by_name("submit").click()

# Move to the marks section and current marks extraction
wait_for_element_by_id(hp_element_id["MARKS_SECTION"]).click()
wait_for_element_by_id(hp_element_id["BODY"]).click()
wait_for_element_by_id(hp_element_id["SEMESTERS"]).click()
time.sleep(3)
wait_for_element_by_id(hp_element_id["S9"]).click()

moy_etu, moy_gen = extract_avg_grades()
all_grades = extract_all_grades()
print("READY")

while True:
    try:
        wait_for_element_by_id(hp_element_id["MARKS_SECTION"]).click()
        curr_moy_etu, curr_moy_gen = extract_avg_grades()
        if curr_moy_etu != moy_etu:
            print("New update")
            curr_all_grades = extract_all_grades()
            body = "Before update: \n" + "\n\t".join(map(lambda x: ' '.join(x), all_grades.difference(curr_all_grades)))
            body += "\n\t *********************"
            body += "\n\tStudent average: " + moy_etu + "\n\tClass average: " + moy_gen
            body += "\n\nAfter update: \n" + "\n\t".join(
                map(lambda x: ' '.join(x), curr_all_grades.difference(all_grades)))
            body += "\n\t *********************"
            body += "\n\tStudent average: " + curr_moy_etu + "\n\tClass average: " + curr_moy_gen
            send_email("HyperPlanning Update", body)
            moy_etu, moy_gen = curr_moy_etu, curr_moy_gen
            all_grades = curr_all_grades
        t = time.localtime()
        print(time.strftime("%H:%M:%S", t))
        time.sleep(600)
    except StaleElementReferenceException:
        print("StaleElementReferenceException ; Retrying ...")
        pass
