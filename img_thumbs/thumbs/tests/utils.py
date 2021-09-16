import os
import pathlib

from thumbs.models import ThumbRule, UserImage

TEST_DATA_DIR = os.path.join(pathlib.Path(__file__).parent, 'test_images')
TEST_IMAGES = [
    os.path.join(TEST_DATA_DIR, 'image.jpg'),
    os.path.join(TEST_DATA_DIR, 'image.png')
]
NON_IMAGE_FILE = os.path.join(TEST_DATA_DIR, 'file.txt')

def delete_test_files(ids):
    '''Delete image files on tearDown'''
    for id in ids:
        img = UserImage.objects.get(pk=id)
        if img.file:
            os.remove(img.file.path)

def create_test_rules():
    rules = [] 
    for idx in range(1,5):
        rule = ThumbRule.objects.create(
            height = idx*200
        )
        rules.append(rule)
    return rules