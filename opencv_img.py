# encoding=utf8

import cv2
import numpy as np


def show(name):
    cv2.imshow('Show', name)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def crop_small_image(name):
    """
    剪裁小图，因为保存下来是和大图同尺寸的，剪裁成适合大小
    :param name:
    :return:
    """
    source = cv2.imread(name, flags=cv2.IMREAD_COLOR)  # 读图片
    img = source[45:88, 9:52]  # 裁剪
    # 坐标：[Ly:Ry , Lx:Rx]
    # 左上坐标：(9,45)
    # 右下坐标：(52,88)
    cv2.imwrite('GT_small_corp.png', img, [int(cv2.IMWRITE_PNG_COMPRESSION)])


# def crop_image(name):
#     from PIL import Image
#     # 打开一张图
#     img = Image.open(name)
#     # 图片尺寸
#     img_size = img.size
#     h = img_size[1]  # 图片高度
#     w = img_size[0]  # 图片宽度
#
#     # 开始截取
#     region = img.crop((6, 45, 50, 85))
#     # 保存图片
#     region.save("GT_small_corp.png")


def main():
    otemp = 'GT_big.png'
    oblk = 'GT_small.png'
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

    # # 腾讯的
    cv2.rectangle(template, (y + 20, x + 20), (y + w - 25, x + h - 25), (7, 249, 151), 2)

    # 极验的
    # cv2.rectangle(template, (y + 136, x + 70), (y + w - 80, x + h - 50), (7, 249, 151), 2)

    # 显示
    show(template)
    return y + 20


if __name__ == '__main__':
    crop_small_image('GT_small.png')
    # main()
