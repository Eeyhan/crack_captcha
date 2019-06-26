import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import requests
import cv2

import numpy as np

PHONE = 0 # 联通手机号

BORDER_1 = 0
BORDER_2 = 7
BORDER_3 = -7


class CrackGeetest(object):
    """ 破解"""

    def __init__(self):
        self.url = 'https://upay.10010.com/npfweb/npfcellweb/phone_recharge_fill.htm'
        self.browser = webdriver.Chrome()
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, 2)
        self.phone = PHONE
        self.success = False
        self.try_num = 3
        self.now_num = 3
        self.flesh_num = 1

    def __del__(self):
        """删除"""
        self.browser.close()

    def get_tencent_button(self):
        """
        点击按钮，获取验证码iframe页面
        :return: 初始化验证按钮
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btndd')))
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

    @staticmethod
    def get_tracks_v2(space):
        # 模拟人工滑动，避免被识别为机器
        space += 20  # 先滑过一点，最后再反着滑动回来
        v = 0
        t = 0.2
        forward_tracks = []
        current = 0
        mid = space * 3 / 5
        while current < space:
            if current < mid:
                a = 2
            else:
                a = -3
            s = v * t + 0.5 * a * (t ** 2)
            v = v + a * t
            current += s
            forward_tracks.append(round(s))
        # 反着滑动到准确位置
        back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -3, -4]
        return {'forward_tracks': forward_tracks, 'back_tracks': back_tracks}

    @staticmethod
    def get_tracks_v3(distance):
        v = 0
        t = 0.3
        # 保存0.3内的位移
        tracks = []
        current = 0
        mid = distance * 4 / 5
        while current <= distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            s = v0 * t + 0.5 * a * (t ** 2)
            current += s
            tracks.append(round(s))
            v = v0 + a * t
        return tracks

    def switch_iframe(self):
        """
        切换iframe
        :return:
        """

        try:
            iframe = self.browser.find_element_by_xpath('//iframe')
            time.sleep(0.5)  # 等待资源加载
            self.browser.switch_to.frame(iframe)
        except Exception as e:
            print('get iframe failed: ', e)

        time.sleep(0.5)  # 等待资源加载
        # 等待图片加载出来
        WebDriverWait(self.browser, 5, 0.5).until(
            EC.presence_of_element_located((By.ID, "tcaptcha_drag_button"))
        )
        try:
            button = self.browser.find_element_by_id('tcaptcha_drag_button')
        except Exception as e:
            print('get button failed: ', e)

    def get_image(self, big_name='big.png', small_name='small.png'):
        """
        获取两张验证码图片，一个有缺口，一个正是缺口图片
        :param big_name: 大图名
        :param small_name: 小图名
        :return:
        """
        # 先点按钮才会出现iframe
        button = self.get_tencent_button()
        button.click()
        time.sleep(2)
        self.switch_iframe()
        #
        # JS = 'return document.getElementsByClassName("geetest_canvas_bg geetest_absolute")[0].toDataURL("image/png");'
        # # 执行 JS 代码并拿到图片 base64 数据
        # im_info = self.browser.execute_script(JS)  # 执行js文件得到带图片信息的图片数据
        # im_base64 = im_info.split(',')[1]  # 拿到base64编码的图片信息
        # im_bytes = base64.b64decode(im_base64)  # 转为bytes类型
        # with open(name, 'wb') as f:  # 保存图片到本地
        #     f.write(im_bytes)

        big_img_url = self.browser.find_element_by_css_selector('#slideBkg').get_attribute('src')
        small_img_url = self.browser.find_element_by_css_selector('#slideBlock').get_attribute('src')

        self.save_image(big_img_url, big_name)
        time.sleep(0.5)
        self.save_image(small_img_url, small_name)
        # 切回默认的iframe
        self.browser.switch_to.parent_frame()
        return big_name, small_name

    def save_image(self, url, name):
        headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
        }
        r = requests.get(url, headers=headers)
        # 将获取到的图片二进制流写入本地文件
        f = open(name, 'wb')
        f.write(r.content)
        f.close()

    # 计算缺口的位置，由于缺口位置查找偶尔会出现找不准的现象，这里进行判断，如果查找的缺口位置x坐标小于450，我们进行刷新验证码操作，重新计算缺口位置，知道满足条件位置。（设置为450的原因是因为缺口出现位置的x坐标都大于450）

    def get_img_distance(self, big_img, small_img):
        """
        获取位置
        :param big_img: 大图文件名
        :param small_img: 小图文件名
        :return:
        """
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
        # 腾讯的原图是680x390，实际图为340x195，减去40是图片所以除以2
        distance = (y - 40 + 20) / 2
        print(distance)
        # 显示
        # show(template)
        return distance

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        self.switch_iframe()

        try:
            slider = self.wait.until(EC.visibility_of_element_located((By.ID, 'tcaptcha_drag_button')))
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
        phone = self.browser.find_elements_by_xpath('//*[@id="number"]')[1]
        time.sleep(0.5)
        phone.send_keys(self.phone)

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
                # track = self.get_tracks_v2(int(gap))
                track = self.get_track(int(gap))

                print('移动距离:', track)

                # 拖动滑块
                slider = self.get_slider()
                self.move_to_gap(slider, track)
                # self.move_to_gap_v2(slider, track)
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
                big_img, small_img = self.get_image()
                # # 测试加的，真正使用删除return
                # return

            except Exception as e:
                # todo: 其他验证，或者是自动识别通过
                self.success = True
                print("自动识别通过或者验证非滑动验证码，无需滑动%s" % e)
                time.sleep(5)
                big_img, small_img = self.get_image()

            # 获取缺口位置
            gap = self.get_img_distance(big_img, small_img)
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
