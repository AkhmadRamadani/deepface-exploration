import os
import gdown
import tensorflow as tf
from deepface.basemodels import Facenet
from deepface.commons import functions
# from deepface.commons.logger import Logger

# logger = Logger(module="basemodels.Facenet512")

tf_version = int(tf.__version__.split(".", maxsplit=1)[0])

if tf_version == 1:
    from keras.models import Model
else:
    from tensorflow.keras.models import Model


def loadModel(
    url="https://github.com/serengil/deepface_models/releases/download/v1.0/facenet512_weights.h5",
) -> Model:

    model = Facenet.InceptionResNetV2(dimension=512)

    # -------------------------

    home = functions.get_deepface_home()

    if os.path.isfile(home + "/.deepface/weights/facenet512_weights.h5") != True:
        # logger.info("facenet512_weights.h5 will be downloaded...")

        output = home + "/.deepface/weights/facenet512_weights.h5"
        gdown.download(url, output, quiet=False)

    # -------------------------

    model.load_weights(home + "/.deepface/weights/facenet512_weights.h5")

    # -------------------------

    return model

def load_weights():
    """
    Loading pre-trained weights for the RetinaFace model
    Args:
        model (Model): retinaface model structure with randon weights
    Returns:
        model (Model): retinaface model with its structure and pre-trained weights

    """
    home = functions.get_deepface_home()

    exact_file = home + "/.deepface/weights/retinaface.h5"
    url = "https://github.com/serengil/deepface_models/releases/download/v1.0/retinaface.h5"

    # -----------------------------

    if not os.path.exists(home + "/.deepface"):
        os.mkdir(home + "/.deepface")

    if not os.path.exists(home + "/.deepface/weights"):
        os.mkdir(home + "/.deepface/weights")

    # -----------------------------

    if os.path.isfile(exact_file) is not True:
        gdown.download(url, exact_file, quiet=False)

    # -----------------------------

    # gdown should download the pretrained weights here.
    # If it does not still exist, then throw an exception.
    if os.path.isfile(exact_file) is not True:
        raise ValueError(
            "Pre-trained weight could not be loaded!"
            + " You might try to download the pre-trained weights from the url "
            + url
            + " and copy it to the ",
            exact_file,
            "manually.",
        )

    model.load_weights(exact_file)

    return model

model = load_weights()
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
open("converted_model_retina_face.tflite", "wb").write(tflite_model)