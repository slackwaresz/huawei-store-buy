import json
from selenium import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re

# 设置 Chrome 驱动的路径
chrome_driver_path = 'C:\googlechromelabs\chromedriver.exe'
driver = webdriver.Chrome(executable_path=chrome_driver_path)

elementBy = by.By()

# Read configuration from the JSON file
with open("config.json", "r") as config_file:
    config = json.load(config_file)

chrome_driver_path = config["chrome_driver_path"]
userName = config["username"]
password = config["password"]
indexUrl = config["index_url"]
phonePageUrl = config["phone_page_url"]
submitOrderUrl = config["submit_order_url"]
buyTimeStr = config["buy_time_str"]

def main():
    click_time = None

    # 先登录
    login()

    # 打开抢购页面
    driver.get(phonePageUrl)

    # 计算抢购开始时间点的时间戳
    buyTime = time.mktime(time.strptime(buyTimeStr, "%Y-%m-%d %H:%M:%S.%f"))

    # 获取当前时间戳
    curTime = time.time()

    # 计算需要等待的时间（秒数）
    waitTime = buyTime - curTime

    if waitTime > 0:
        print("等待 {} 秒后开始抢购...".format(waitTime))
        time.sleep(waitTime)

    # 抢购
    buy()

def login():
    print("登录")
    driver.get(indexUrl)
    time.sleep(5)

    # 选择登录按钮
    indexLoginBns = driver.find_elements(elementBy.CLASS_NAME, "r-gy4na3")

    if indexLoginBns:
        for bn in indexLoginBns:
            if bn.text == "请登录":
                bn.click()
                break
    else:
        indexLoginBns = driver.find_elements(elementBy.CLASS_NAME, "r-1ff274t")
        for bn in indexLoginBns:
            if bn.text == "登录":
                bn.click()
                break

    time.sleep(5)
    loginElements = driver.find_elements(elementBy.CSS_SELECTOR, ".hwid-input-root")

    for e in loginElements:
        inputele = e.find_element(elementBy.TAG_NAME, "input")
        attr = inputele.get_attribute("type")

        if attr == "text":
            inputele.send_keys(userName)
        elif attr == "password":
            inputele.send_keys(password)

    loginBtnElement = driver.find_element(elementBy.CSS_SELECTOR, ".hwid-login-btn")
    loginBtnElement.click()

    # 需要手机验证码
    # 此处手动完成验证码验证 预留一分钟
    time.sleep(50)
    print("登录成功")

from selenium.common.exceptions import StaleElementReferenceException

def buy():
    global click_time
    driver.refresh()
    print("准备抢购 - 时间：", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def wait_for_buy_button():
        WebDriverWait(driver, 6000).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'product-button02') and not(contains(@class, 'disabled'))]"))
        )

    cur_url = driver.current_url
    canBuy = False

    if "即将开始" in driver.page_source:
        print("等待抢购开始...")
        wait_for_buy_button()

    # 如果没有进入提交订单页面则一直点击立即下单
    buyCountNum = 1

    while not re.search(submitOrderUrl, cur_url) and not canBuy:
        try:
            # 等待立即下单按钮可点击
            buy_button = WebDriverWait(driver, 6000).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'product-button02') and not(contains(@class, 'disabled'))]"))
            )

            if buy_button.find_element(By.TAG_NAME, "span").text == "立即下单":
                # Set the click time
                click_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                print("点击下单按钮时间:", click_time)
                # 此元素被设置了javascript:; ， 所以click()无法触发，只能通过执行execute_script执行网页js方法
                driver.execute_script('rush.business.clickBtnRushBuy2(this)')
                canBuy = True
        except StaleElementReferenceException:
            continue

    if canBuy:
        try:
            time.sleep(0.1)
            # 等待页面中出现order-submit-btn元素
            WebDriverWait(driver, 600).until(
                EC.presence_of_element_located((By.CLASS_NAME, "order-submit-btn"))
            )

            # 选中checkbox
            checkbox = driver.find_element(By.ID, "agreementChecked")
            if not checkbox.is_selected():
                checkbox.click()

            submitBtn = driver.find_element(elementBy.CLASS_NAME, "order-submit-btn")

            if submitBtn is None:
                print("无法提交订单")
            else:
                submitBtn.click()
        except Exception as e:
            print("提交订单时出现异常:", str(e))


# 运行主函数
main()
