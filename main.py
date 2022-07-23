import face_recognition
import face_recognition_models
from loguru import logger
from flask import Flask, request
import os
import json

app = Flask(__name__)


def getImageEncoding(path):
    image = face_recognition.load_image_file(path)
    # face_recognition_models.face_recognition_model_location()
    image_encodings = face_recognition.face_encodings(image)
    if len(image_encodings) < 1:
        logger.info(f'{path}当前路径的照片没有检测到人脸')
        return -1
    return image_encodings


def compare(image_scene, image_lawer, image_retinue):
    scene_encodings = getImageEncoding(image_scene)

    if scene_encodings == -1:
        logger.info(f'{image_scene}:当前路径的照片没有检测到人脸')
        return -1
    if len(scene_encodings) > 2:
        logger.info(f'{image_scene}当前路径的照片检测到{len(scene_encodings)}张人脸,超出会见人数')
        return -2

    lawer_encoding = getImageEncoding(image_lawer)
    if lawer_encoding == -1:
        logger.info(f'{image_lawer}:当前路径的照片没有检测到人脸')
    if len(lawer_encoding) > 1:
        logger.info(f'{image_lawer}:当前路径的照片检测到{len(lawer_encoding)}张人脸,照片头像数量不合格')
        return -3

    if len(image_retinue) == 0:
        '''
        没有随行人员的情况下，现场照片不能检测到多张人脸
        '''
        if len(scene_encodings) > 1:
            logger.info(f'{image_scene}当前路径的照片检测到{len(scene_encodings)}张人脸')
            return -2
        result = face_recognition.face_distance(scene_encodings, lawer_encoding[0])
        logger.info(f'当前检测相似度：{result}')
        data = {'lawerResult': result[0]}
        return data
    else:
        '''
        有随行人员的情况
        '''
        if len(scene_encodings) == 1:
            result1 = face_recognition.face_distance(scene_encodings, lawer_encoding[0])
            logger.info(f'当前检测相似度：{result1}')
            return {'lawerResult': result1[0]}
        else:
            retinue_encoding = getImageEncoding(image_retinue)
            result1 = face_recognition.face_distance(scene_encodings, lawer_encoding[0])
            result2 = face_recognition.face_distance(scene_encodings, retinue_encoding[0])
            if result1[0] < result1[1]:
                logger.info(f'检测相似度结果：{[result1[0], result2[1]]}')
                result = {'lawerResult': result1[0], 'lawerRetinue': result2[1]}
                return result
            else:
                logger.info(f'检测相似度结果：{[result1[1], result2[0]]}')
                result = {'lawerResult':result1[1],'lawerRetinue':result2[0]}
                return result


# compare('./images2/6.jpg','./images2/3.jpg','./images2/2.jpg')
# compare('./images2/1.jpg','./images2/3.jpg','')

@app.route('/', methods=['POST', 'GET'])
def server_status():  # put application's code here
    data = {'status': 200}
    return data


@app.route('/startPersonValidate', methods=['GET'])
def startPersonValidate():

    image_scene = request.args.get('image_scene')
    image_lawer = request.args.get('image_lawer')
    image_retinue = request.args.get('image_retinue')

    # print(image_scene,image_lawer,image_lawer)

    # content = json.loads(request.data)


    # image_scene = content['image_scene']
    # image_lawer = content['image_lawer']
    # image_retinue = content['image_retinue']

    result = compare(image_scene, image_lawer, image_retinue)
    print(result)
    print('====================')
    data = {'status': 200,'result':result}
    print(data)
    return data


if __name__ == '__main__':
    logger.info("------start http server---")
    os.makedirs('./images/', exist_ok=True)
    app.run(debug=False)
