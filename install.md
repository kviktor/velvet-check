git clone https://github.com/yahoo/open_nsfw.git
git clone https://github.com/BVLC/caffe.git

sudo apt-get install libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler libatlas-base-dev libgflags-dev libgoogle-glog-dev liblmdb-dev python-dev
sudo apt-get install --no-install-recommends libboost-all-dev


cd caffe
pip install -r python/requirements.txt
cp Makefile.config.example Makefile.config
make all -j2

export PYTHONPATH=/home/cloud/caffe/python:$PYTHONPATH
cd ../open_nsfw
python ./classify_nsfw.py \
--model_def nsfw_model/deploy.prototxt \
--pretrained_model nsfw_model/resnet_50_1by2_nsfw.caffemodel \
INPUT_IMAGE_PATH 
