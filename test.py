import dlib
import os
import time
import base64
import numpy as np
from PIL import Image
import serial
import configparser
from io import BytesIO
from flask import Flask, request
from loguru import logger
from serial import SerialException

app = Flask(__name__)
detector = dlib.get_frontal_face_detector()
currpath = os.path.dirname(os.path.realpath(__file__))
conf = configparser.ConfigParser()
path = os.path.join(currpath, 'config.ini')
conf.read(path, encoding="utf-8")
portVal = conf['params']['port']
top_limit = float(conf['params']['top_limit'])
bottom_limit = float(conf['params']['bottom_limit'])
# port = ''
port = serial.Serial(portVal, baudrate=9600, parity=serial.PARITY_EVEN)

params = {
    'up': '01 06 00 40 03 20 89 36',
    'down': '01 06 00 40 FC 19 08 D4',
    'stop': '01 06 00 40 00 00 88 1E',
    'reset': '01 06 00 40 FC 19 08 D4'
}


def adjust(type):
    '''
    根据类型进行电机控制
    :param type: 1:向上，2：向下，3：停止，4：复位
    :return:
    '''
    if not port.isOpen():
        logger.error('电机串口连接失败，请联系管理员解决')
        try:
            port.open()
        except SerialException as e:
            return -1
    if type == 1:
        print(params.get('up'))
        try:
            port.write(bytes.fromhex(params.get('up')))
        except Exception as e:
            logger.error('向上--调用失败，设备故障')
            return -2
    if type == 2:
        try:
            port.write(bytes.fromhex(params.get('down')))
        except Exception as e:
            logger.error('向下--调用失败，设备故障')
            return -2
    if type == 3:
        try:
            port.write(bytes.fromhex(params.get('stop')))
        except Exception as e:
            logger.error('停止--调用失败，设备故障')
            return -2
    if type == 4:
        try:
            port.write(bytes.fromhex(params.get('reset')))
        except Exception as e:
            logger.error('复位--调用失败，设备故障')
            return -2


@app.route('/check', methods=['POST'])
def startPersonValidate():
    t = time.time()

    image_base64 = request.form['image_base64']
    byte_data = base64.b64decode(image_base64)
    image_data = BytesIO(byte_data)
    image = Image.open(image_data)
    # print(image.size[1])
    image_height = image.size[1]
    image = np.array(image)
    detects = detector(image)
    if len(detects) < 1 :
        adjust(3)
        return {'msg':'未检测到人脸'}

    logger.info(f'耗时：{time.time() - t},检测结果：{detects[0]}')
    result = {'left': detects[0].left(), 'right': detects[0].right(), 'top': detects[0].top(), 'bottom': detects[0].bottom()}
    midle_height = float((detects[0].top() + detects[0].bottom())/2)
    if midle_height < float(top_limit*image_height):
        adjust(1)
        return result

    if midle_height > float(bottom_limit*image_height):
        adjust(2)
        return result

    if float(top_limit*image_height) <= midle_height <= float(bottom_limit*image_height):
        adjust(3)
        return result


if __name__ == '__main__':
    logger.info("------start http server---")
    app.run(debug=False)
