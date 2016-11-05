# Velvet Check ![build](https://api.travis-ci.org/kviktor/velvet-check.svg?branch=master)

A simple utility to check the NSFW level of articles at the Velvet section of [index.hu](http://index.hu).

### Before
![before](https://cloud.githubusercontent.com/assets/1112058/20032494/497dbfb2-a38b-11e6-803a-58cb2fb201f9.png)

### After
![after](https://cloud.githubusercontent.com/assets/1112058/20032493/4873f834-a38b-11e6-9202-2abc2d4d6d44.png)

## Installation

To whole NSFW classification is based on [open_nsfw](https://github.com/yahoo/open_nsfw)
which uses [caffe](https://github.com/BVLC/caffe). To install caffe follow the [documentation](http://caffe.berkeleyvision.org/installation.html)
or these snippets below (they are basically the same).

```sh
git clone https://github.com/yahoo/open_nsfw.git
git clone https://github.com/BVLC/caffe.git

sudo apt-get install libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler libatlas-base-dev libgflags-dev libgoogle-glog-dev liblmdb-dev python-dev
sudo apt-get install --no-install-recommends libboost-all-dev

cd caffe
pip install -r python/requirements.txt
cp Makefile.config.example Makefile.config  # for the correct settings follow the previously mentioned documentation
make all -j2
make pycaffe

export PYTHONPATH=/path/to/caffe/python:$PYTHONPATH
cd ../open_nsfw
python ./classify_nsfw.py \
--model_def nsfw_model/deploy.prototxt \
--pretrained_model nsfw_model/resnet_50_1by2_nsfw.caffemodel \
INPUT_IMAGE_PATH
```

Now to install Velvet Check clone this repo, enter it and run the following commands.
```sh
sudo apt-get install redis-server sqlite3
pip install -r requirements.txt
```

If you use virtualenv modify the postactivate file and add these settings (if not you can just paste them before starting the web server/celery ¯\\\_(ツ)\_/¯
```
export MODEL_DEF_PATH='/path/to/open_nsfw/nsfw_model/deploy.prototxt'
export PRETRAINED_MODEL_PATH='/path/to/open_nsfw/nsfw_model/resnet_50_1by2_nsfw.caffemodel'
export PYTHONPATH=/path/to/caffe/python:
export FLASK_APP="web.py"
```
