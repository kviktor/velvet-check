import logging
import re
from io import BytesIO

import dramatiq
import requests
from bs4 import BeautifulSoup as bs

from django.db import transaction
from django.conf import settings

from .models import (
    Article,
    Image,
)

logger = logging.getLogger(__name__)

TWITTER_RE = re.compile(".+>([a-zA-Z0-9./]+)<.+")
INSTAGRAM_API = "https://api.instagram.com/oembed/?callback=&url=%s"


@dramatiq.actor
def calculate_missing_article_scores(missing_urls):
    for article_url in missing_urls:
        image_urls = get_image_urls_from_link(article_url)
        image_scores = generate_score_for_images(image_urls)

        with transaction.atomic():
            article, _ = Article.objects.get_or_create(url=article_url)

            for image_url, score in image_scores.items():
                Image.objects.update_or_create(
                    article=article,
                    url=image_url,
                    defaults={'score': score},
                )


# not actual dramatiq tasks
def generate_score_for_images(image_urls):
    image_scores = {}
    for url in image_urls:
        score = classify_image(url)
        logger.info("Score for %s: %s", url, score)
        image_scores[url] = score

    return image_scores


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
        except Exception:
            logger.exception("Error calling '%s' with '%s'", f, link)

    logger.info("Scanning finished (%s), found the following images: %s",
                link, ",".join(images))
    return images


# from down here it's from/based on the open_nsfw repo modified for py3
# https://github.com/yahoo/open_nsfw/blob/master/classify_nsfw.py
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
    from PIL import Image as PIL_Image

    im = PIL_Image.open(BytesIO(data))
    if im.mode != "RGB":
        im = im.convert('RGB')
    imr = im.resize(sz, resample=PIL_Image.BILINEAR)
    fh_im = BytesIO()
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
    import caffe  # noqa

    if caffe_net is not None:

        # Grab the default output names if none were requested specifically.
        if output_layers is None:
            output_layers = caffe_net.outputs

        img_data_rs = resize_image(pimg, sz=(256, 256))
        image = caffe.io.load_image(BytesIO(img_data_rs))

        H, W, _ = image.shape
        _, _, h, w = caffe_net.blobs['data'].data.shape
        h_off = int(max((H - h) / 2, 0))
        w_off = int(max((W - w) / 2, 0))
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
    import caffe  # noqa
    import numpy as np  # noqa

    response = requests.get(url)
    if not (200 <= response.status_code < 300):
        logger.error('%s returned %d', url, response.status_code)
        return None

    image_data = response.content

    # Pre-load caffe model.
    nsfw_net = caffe.Net(
        settings.MODEL_DEF_PATH,
        settings.PRETRAINED_MODEL_PATH,
        caffe.TEST,
    )

    # Load transformer
    # Note that the parameters are hard-coded for best results
    caffe_transformer = caffe.io.Transformer(
        {'data': nsfw_net.blobs['data'].data.shape})
    # move image channels to outermost
    caffe_transformer.set_transpose('data', (2, 0, 1))
    # subtract the dataset-mean value in each channel
    caffe_transformer.set_mean('data', np.array([104, 117, 123]))
    # rescale from [0, 1] to [0, 255]
    caffe_transformer.set_raw_scale('data', 255)
    # swap channels from RGB to BGR
    caffe_transformer.set_channel_swap('data', (2, 1, 0))

    # Classify.
    scores = caffe_preprocess_and_compute(
        image_data, caffe_transformer=caffe_transformer,
        caffe_net=nsfw_net, output_layers=['prob'])

    # Scores is the array containing SFW / NSFW image probabilities
    # scores[1] indicates the NSFW probability
    return scores[1]
