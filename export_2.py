
from retinaface import RetinaFace
from retinaface.commons import postprocess
from typing import Any
import tensorflow as tf

from retinaface.model import retinaface_model
from retinaface.commons import preprocess, postprocess
import numpy as np

model = retinaface_model.build_model()
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.allow_custom_ops = True
converter.experimental_new_converter = True
tflite_model = converter.convert()
open("converted_retina_face_3.tflite", "wb").write(tflite_model)