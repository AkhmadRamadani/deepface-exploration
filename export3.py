import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model("models/retinaface.h5")
tflite_model = converter.convert()
open("converted_retina_face2.tflite", "wb").write(tflite_model)