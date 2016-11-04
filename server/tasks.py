import logging
import re

import caffe
import numpy as np
import requests
from bs4 import BeautifulSoup as bs
from celery import Celery
from PIL import Image as PIL_Image
from StringIO import StringIO

from models import Article, Image
from settings import PRETRAINED_MODEL_PATH, MODEL_DEF_PATH, BROKER_URL

logger = logging.getLogger(__name__)

TWITTER_RE = re.compile(".+>([a-zA-Z0-9\./]+)<.+")
INSTAGRAM_API = "https://api.instagram.com/oembed/?callback=&url=%s"


celery = Celery("tasks")
celery.conf.update(
    BROKER_URL=BROKER_URL,
    CELERY_ACCEPT_CONTENT=["json"],
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
)


@celery.task(name="generate_score_for_article")
def generate_score_for_article(url):
    if Article.by_url(url):
        logger.warning("Article '%s' is already in db", url)
    else:
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
        generate_score_for_article.apply_async((url, ))


def generate_score_for_images(article_url, image_urls):
    for url in image_urls:
        if not Image.by_url(url):
            score = classify_image(url)
            logger.info("%s: %s", url, score)
            Image.create(url, score, article_url)


def extract_instagram_urls(soup, link=None):
    images = []
    blocks = soup.find_all("blockquote", {'class': "instagram-media"})
    for b in blocks:
        href = b.find("a")['href']
        img_url = requests.get(INSTAGRAM_API % href).json()['thumbnail_url']
        images.append(img_url)
    return images


def extract_twitter_urls(soup, link=None):
    images = set([])
    blocks = soup.find_all("blockquote", {'class': "twitter-tweet"})
    for b in blocks:
        content = b.decode_contents().replace("\n", "").replace(" ", "")
        result = TWITTER_RE.match(content)
        pic_url = result.group(1)

        body = requests.get("http://%s" % pic_url).content
        twitter_soup = bs(body, "lxml")
        for div in twitter_soup.find_all(
                "div", {'class': "AdaptiveMedia-photoContainer"}):
            images.add(div['data-image-url'])

    return list(images)


def get_image_urls_from_link(link):
    logger.info("Scanning '%s' started", link)
    content = requests.get(link).content

    soup = bs(content, "lxml")
    a = soup.find("div", {'class': "cikk-torzs-container"})

    def img_and_not_szerzo(tag):
        return (tag.name == "img" and
                (not tag.has_attr("class") or "szerzo-kep" not in tag['class']))
    img_tags = a.find_all(img_and_not_szerzo)

    images = [i['src'] for i in img_tags if not i['src'].startswith("data:image")]
    for f in [extract_instagram_urls, extract_twitter_urls, ]:
        try:
            images.extend(f(soup, link))
        except:
            logger.error("Error calling '%s' with '%s'", f, link)

    logger.info("Scanning '%s' finished, found the following images: %s",
                link, ",".join(images))
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
    nsfw_net = caffe.Net(MODEL_DEF_PATH, PRETRAINED_MODEL_PATH, caffe.TEST)

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
