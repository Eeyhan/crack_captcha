import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chaojiying import Chaojiying_Client
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

EMAIL = 'test'
PASSWORD = '123456'

BORDER_1 = 54
BORDER_2 = 74
BORDER_3 = 34


class CrackGeetest(object):
    """ 破解"""

    def __init__(self):
        self.url = 'http://127.0.0.1:8000/home'
        self.browser = webdriver.Chrome()
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, 2)
        self.email = EMAIL
        self.password = PASSWORD
        self.success = False
        self.try_num = 3
        self.now_num = 3
        self.flesh_num = 1

    def __del__(self):
        """删除"""
        self.browser.close()

    def get_geetest_button(self):
        """
        获取初始验证按钮
        :return: 初始化验证按钮
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_radar_tip')))
        return button

    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_img')))
        time.sleep(0.5)
        location = img.location
        print(location)
        size = img.size
        top, bottom, left, right = location['y'] + 50, location['y'] + size['height'] + 100, location['x'] + 130, \
                                   location['x'] + size['width'] + 130

        return top, bottom, left, right

    def get_geetest_image(self, name='captcha.png'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)
        return captcha

    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        try:
            slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        except Exception:
            self.crack()
            return
        return slider

    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        self.browser.get(self.url)
        time.sleep(0.5)
        email = self.browser.find_elements_by_xpath('//*[@id="username1"]')[0]
        password = self.browser.find_element_by_xpath('//*[@id="password1"]')
        time.sleep(0.5)
        email.send_keys(self.email)
        time.sleep(0.5)
        password.send_keys(self.password)

    def to_login(self):
        """
        点击登录按钮
        :return: 登录操作
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest-btn')))
        return button

    @staticmethod
    def get_track(distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 2
            else:
                # 加速度为负3
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    @staticmethod
    def get_gap_pic():
        """
        通过超级鹰获取缺口位置,返回图片id，如果错误则返回id返题分
        :return: 缺口距离
        """
        chaojiying = Chaojiying_Client('超级鹰账号', '密码', '软件ID')
        im = open('target.png', 'rb').read()
        result = chaojiying.PostPic(im, 9101)
        print(result)
        gap = int(result.get("pic_str").split(",")[0])
        pic_id = result.get('pic_id')
        return gap, pic_id

    # 超级赢验证失败,反馈回去,将不扣钱
    @staticmethod
    def fail_to_chaojiying(img_id):
        """
        超级赢验证失败,反馈回去,将不扣钱
        :param img_id: 图片id
        :return: None
        """
        chaojiying = Chaojiying_Client('超级鹰账号', '密码', '软件ID')
        result = chaojiying.ReportError(img_id)
        return result

    @staticmethod
    def add_text_to_image():
        """
        :return: None
        """
        # 设置字体样式
        font = ImageFont.truetype("FZKTJW.TTF", 25)

        imageFile = "captcha.png"
        im1 = Image.open(imageFile)

        add_text = "请点击缺口区域左上角"
        draw = ImageDraw.Draw(im1)
        draw.text((2, 180), add_text, "#FF0000", font=font)

        # 保存
        im1.save("target.png")

    def crack(self):
        # 输入用户名密码
        self.open()

        # 点击验证按钮
        time.sleep(1)
        button = self.get_geetest_button()
        button.click()

        # ＢOREDER有俩种情况，一种是8,一种是１5, 还有一种是28
        def slider_try(gap, BORDER):
            if self.now_num:
                # 减去缺口位置
                gap -= BORDER

                # 计算滑动距离
                track = self.get_track(int(gap))

                print('移动距离:', track)

                # 拖动滑块
                slider = self.get_slider()
                self.move_to_gap(slider, track)
                try:
                    self.success = self.wait.until(
                        EC.text_to_be_present_in_element((By.CLASS_NAME, 'geetest_success_radar_tip_content'), '验证成功'))
                except Exception as e:
                    self.now_num -= 1
                    test_num = self.try_num - self.now_num
                    if self.now_num == 0:
                        print("第%d次尝试失败, 验证失败" % test_num)
                    else:
                        print("验证失败,正在进行第%d次尝试" % test_num)

        while not self.success and self.now_num > 0:

            # 获取验证码图片
            try:
                self.get_geetest_image()

                # # 测试加的，真正使用删除return
                # return

            except Exception as e:
                # todo: 其他验证，或者是自动识别通过
                # self.success = True
                print("自动识别通过或者验证非滑动验证码，无需滑动%s" % e)
                time.sleep(5)

                # 登录
                button = self.to_login()
                button.click()
                return

            # 给验证码加文字
            self.add_text_to_image()

            # 获取缺口位置
            gap, pic_id = self.get_gap_pic()
            print("缺口位置gap为", gap)

            # 第一中请求，gap减少54
            slider_try(gap, BORDER_1)
            # 成功后退出
            if not self.success:
                # 尝试gap减少68
                self.fail_to_chaojiying(pic_id)
                slider_try(gap, BORDER_2)
                if not self.success:
                    self.fail_to_chaojiying(pic_id)
                    slider_try(gap, BORDER_3)

            if self.success:
                test_num = self.try_num - self.now_num + 1
                print("第{}次刷新,第{}次尝试,验证通过".format(self.flesh_num, test_num))
                time.sleep(5)
                # self.success = True
                # 登录
                button = self.to_login()
                button.click()

        if not self.success:
            print("重新刷新页面,这是第%d次刷新" % self.flesh_num)
            self.flesh_num += 1
            self.now_num = 3
            self.try_num = 3
            self.crack()


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()
    del crack
