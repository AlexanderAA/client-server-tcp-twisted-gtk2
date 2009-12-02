import os
import pickle
import random

from twisted.spread import pb

IMAGE_FOLDER = 'images'
IMAGE_EXT = '.jpg'

def _serialize_random_image():
    '''
    Returns random image (actually, any data in given file) serialized with pickle.
    If file is not exist, returns pickle.dumps(None)
    
    For now, images must be 300x200 pixels JPEG. 
    Otherwise, client app will render them incorrectly.
    '''
    # choose from 10 images in 'images' folder 
    image_name = str(random.randint(1, 10)) # 
    # generate url to read file
    image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', IMAGE_FOLDER, image_name + IMAGE_EXT)
    # check if the file exists (e.g. was not deleted from file system)
    if os.path.exists(image_path):
        image_data = open(image_path).read()
        return pickle.dumps({'file_name': image_name + IMAGE_EXT, 'file_data': image_data})
    else:
        return pickle.dumps(None)

class ImageServer(pb.Root):
    '''
    ImageServer sends random image to client applications
    '''
    def remote_serve_random_image(self, request):
	'''
	serve random image on request
	'''
        return _serialize_random_image()

