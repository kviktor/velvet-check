from bs4 import BeautifulSoup as bs
from PIL import Image as PIL_Image
from StringIO import StringIO
import caffe
import numpy as np
import requests

from models import Article, Image


instagram_api = "https://api.instagram.com/oembed/?callback=&url=%s"
MODEL_DEF = "/home/kviktor/Python/open_nsfw/nsfw_model/deploy.prototxt"
PRETRAINED_MODEL = "/home/kviktor/Python/open_nsfw/nsfw_model/resnet_50_1by2_nsfw.caffemodel"


# TASK
def generate_score_for_article(url):
    Article.create(url)
    image_urls = get_image_urls_from_link(url)
    generate_score_for_images(url, image_urls)


def get_article_score(url):
    """ returns the score if it's in db
        if it's not in db it returns None
        and starts the job to calculate it asynchronously
    """
    article = Article.by_url(url)
    if article:
        return article.score
    else:
        generate_score_for_article(url)


def generate_score_for_images(article_url, image_urls):
    for url in image_urls:
        if not Image.by_url(url):
            score = classify_image(url)
            print(url, score)
            Image.create(url, score, article_url)


def extract_instagram_urls(soup, link=None):
    images = []
    blocks = soup.find_all("blockquote", {'class': "instagram-media"})
    for b in blocks:
        href = b.find("a")['href']
        img_url = requests.get(instagram_api % href).json()['thumbnail_url']
        images.append(img_url)
    return images


def get_image_urls_from_link(link):
    content = requests.get(link).content

    soup = bs(content, "lxml")
    a = soup.find("div", {'class': "cikk-torzs-container"})

    def img_and_not_szerzo(tag):
        return (tag.name == "img" and
                (not tag.has_attr("class") or "szerzo-kep" not in tag['class']))
    img_tags = a.find_all(img_and_not_szerzo)

    images = [i['src'] for i in img_tags]
    for f in [extract_instagram_urls]:
        images.extend(f(soup, link))

    return images


# from down here it's from the open_nsfw repo

def resize_image(data, sz=(256, 256)):
    """
    Resize image. Please use this resize logic for best results instead of the
    caffe, since it was used to generate training dataset
    :param str data:
        The image data
    :param sz tuple:
        The resized image dimensions
    :returns bytearray:
        A byte array with the resized image
    """
    img_data = str(data)
    im = PIL_Image.open(StringIO(img_data))
    if im.mode != "RGB":
        im = im.convert('RGB')
    imr = im.resize(sz, resample=PIL_Image.BILINEAR)
    fh_im = StringIO()
    imr.save(fh_im, format='JPEG')
    fh_im.seek(0)
    return bytearray(fh_im.read())


def caffe_preprocess_and_compute(pimg, caffe_transformer=None, caffe_net=None,
                                 output_layers=None):
    """
    Run a Caffe network on an input image after preprocessing it to prepare
    it for Caffe.
    :param PIL.Image pimg:
        PIL image to be input into Caffe.
    :param caffe.Net caffe_net:
        A Caffe network with which to process pimg afrer preprocessing.
    :param list output_layers:
        A list of the names of the layers from caffe_net whose outputs are to
        to be returned.  If this is None, the default outputs for the network
        are returned.
    :return:
        Returns the requested outputs from the Caffe net.
    """
    if caffe_net is not None:

        # Grab the default output names if none were requested specifically.
        if output_layers is None:
            output_layers = caffe_net.outputs

        img_data_rs = resize_image(pimg, sz=(256, 256))
        image = caffe.io.load_image(StringIO(img_data_rs))

        H, W, _ = image.shape
        _, _, h, w = caffe_net.blobs['data'].data.shape
        h_off = max((H - h) / 2, 0)
        w_off = max((W - w) / 2, 0)
        crop = image[h_off:h_off + h, w_off:w_off + w, :]
        transformed_image = caffe_transformer.preprocess('data', crop)
        transformed_image.shape = (1, ) + transformed_image.shape

        input_name = caffe_net.inputs[0]
        all_outputs = caffe_net.forward_all(blobs=output_layers,
                    **{input_name: transformed_image})

        outputs = all_outputs[output_layers[0]][0].astype(float)
        return outputs
    else:
        return []


def classify_image(url):
    image_data = requests.get(url).content

    # Pre-load caffe model.
    nsfw_net = caffe.Net(MODEL_DEF, PRETRAINED_MODEL, caffe.TEST)

    # Load transformer
    # Note that the parameters are hard-coded for best results
    caffe_transformer = caffe.io.Transformer({'data': nsfw_net.blobs['data'].data.shape})
    caffe_transformer.set_transpose('data', (2, 0, 1))  # move image channels to outermost
    caffe_transformer.set_mean('data', np.array([104, 117, 123]))  # subtract the dataset-mean value in each channel
    caffe_transformer.set_raw_scale('data', 255)  # rescale from [0, 1] to [0, 255]
    caffe_transformer.set_channel_swap('data', (2, 1, 0))  # swap channels from RGB to BGR

    # Classify.
    scores = caffe_preprocess_and_compute(image_data, caffe_transformer=caffe_transformer, caffe_net=nsfw_net, output_layers=['prob'])

    # Scores is the array containing SFW / NSFW image probabilities
    # scores[1] indicates the NSFW probability
    return scores[1]
