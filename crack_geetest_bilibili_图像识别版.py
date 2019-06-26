import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import cv2
from PIL import Image
import numpy as np

EMAIL = 'test'
PASSWORD = '123456'

BORDER_1 = -8
BORDER_2 = 8
BORDER_3 = 8


class CrackGeetest(object):
    """ 破解"""

    def __init__(self):
        self.url = 'https://passport.bilibili.com/login'
        self.browser = webdriver.Chrome()
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, 5)
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
        点击按钮，获取验证码iframe页面
        :return: 初始化验证按钮
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-login')))
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

    def get_image(self, big_name='GT_big.png', small_name='GT_small.png', full_name='GT_full.png'):
        """
        获取两张验证码图片，一个有缺口，一个正是缺口图片
        :param big_name: 大图名
        :param small_name: 小图名
        :return:
        """
        # 先点按钮才会出现iframe
        button = self.get_geetest_button()
        button.click()
        time.sleep(2)

        JS_big = 'return document.getElementsByClassName("geetest_canvas_bg")[0].toDataURL("image/png");'
        JS_small = 'return document.getElementsByClassName("geetest_canvas_slice")[0].toDataURL("image/png");'
        JS_full = 'return document.getElementsByClassName("geetest_canvas_fullbg")[0].toDataURL("image/png");'
        self.save_image(JS_big, big_name)
        self.save_image(JS_full, full_name)
        self.save_image(JS_small, small_name)
        return full_name, big_name

    def save_image(self, js, name):
        """
        执行js，保存图片
        :param js:
        :param name:
        :return:
        """
        # 执行 JS 代码并拿到图片 base64 数据
        im_info = self.browser.execute_script(js)  # 执行js文件得到带图片信息的图片数据
        im_base64 = im_info.split(',')[1]  # 拿到base64编码的图片信息
        im_bytes = base64.b64decode(im_base64)  # 转为bytes类型
        f = open(name, 'wb')
        f.write(im_bytes)
        f.close()

    def crop_small_image(self, name):
        """
        剪裁小图，因为保存下来是和大图同尺寸的，剪裁成适合大小
        :param name:
        :return:
        """
        source = cv2.imread(name, flags=cv2.IMREAD_COLOR)  # 读图片
        img = source[82:136, 10:49]  # 裁剪
        # 坐标：[Ly:Ry , Lx:Rx]
        # 左上坐标：(9,45)
        # 右下坐标：(52,88)
        cv2.imwrite('GT_small_corp.png', img, [int(cv2.IMWRITE_PNG_COMPRESSION)])

    # 计算缺口的位置，由于缺口位置查找偶尔会出现找不准的现象，这里进行判断，如果查找的缺口位置x坐标小于450，我们进行刷新验证码操作，重新计算缺口位置，知道满足条件位置。（设置为450的原因是因为缺口出现位置的x坐标都大于450）
    def get_img_distance(self, big_img, small_img):
        """
        获取位置
        :param big_img: 大图文件名
        :param small_img: 小图文件名
        :return:
        """
        # 先裁剪图片
        self.crop_small_image(small_img)

        otemp = big_img
        oblk = small_img
        target = cv2.imread(oblk, 0)
        template = cv2.imread(otemp, 0)
        w, h = target.shape[::-1]
        temp = 'temp.jpg'
        targ = 'targ.jpg'
        cv2.imwrite(temp, template)
        cv2.imwrite(targ, target)
        target = cv2.imread(targ)
        target = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        target = abs(255 - target)
        cv2.imwrite(targ, target)
        target = cv2.imread(targ)
        template = cv2.imread(temp)
        result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        x, y = np.unravel_index(result.argmax(), result.shape)

        # 展示圈出来的区域
        # cv2.rectangle(template, (y, x), (y + w, x + h), (7, 249, 151), 2)
        cv2.rectangle(template, (y + 20, x + 20), (y + w - 25, x + h - 25), (7, 249, 151), 2)
        # # 腾讯的原图是680x390，实际图为340x195，减去40是图片所以除以2
        # distance = (y - 40 + 20) / 2

        # 极验
        distance = y + 135

        print(distance)
        # 显示
        # show(template)
        return distance

    def get_gap(self, image1, image2):
        """
        获取缺口偏移量
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return:
        """
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        # self.switch_iframe()

        try:
            slider = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'geetest_slider_button')))
        except Exception as e:
            print(e)
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
        email = self.browser.find_elements_by_xpath('//*[@id="login-username"]')[0]
        password = self.browser.find_element_by_xpath('//*[@id="login-passwd"]')

        email.send_keys(self.email)
        password.send_keys(self.password)

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        action = ActionChains(self.browser)
        action.click_and_hold(slider).perform()
        action.reset_actions()  # 清除之前的action
        for x in track:
            action.move_by_offset(xoffset=x, yoffset=0).perform()
            action.reset_actions()  # 清除之前的action
        time.sleep(0.5)
        action.release().perform()

    def crack(self):
        # 输入用户名密码
        self.open()

        # 点击验证按钮,获取iframe页面
        time.sleep(1)

        def slider_try(gap, BORDER):
            if self.now_num:
                # 减去缺口位置
                gap += BORDER

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
                full_img_name, big_img_name = self.get_image()
                # # 测试加的，真正使用删除return
                # return

            except Exception as e:
                # todo: 其他验证，或者是自动识别通过
                self.success = True
                print("自动识别通过或者验证非滑动验证码，无需滑动%s" % e)
                time.sleep(5)
                full_img_name, big_img_name = self.get_image()

            # 获取缺口位置
            full_img = Image.open(full_img_name)
            big_img = Image.open(big_img_name)
            gap = self.get_gap(full_img, big_img)
            print("缺口位置gap为", gap)

            slider_try(gap, BORDER_1)
            # 成功后退出
            if not self.success:
                # 尝试gap减少14
                slider_try(gap, BORDER_2)
                if not self.success:
                    slider_try(gap, BORDER_3)

            if self.success:
                test_num = self.try_num - self.now_num + 1
                print("第{}次刷新,第{}次尝试,验证通过".format(self.flesh_num, test_num))
                time.sleep(5)
                # self.success = True

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
