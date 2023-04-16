import traceback
from functools import wraps
import numpy as np
from matplotlib.colors import ListedColormap

from transformers import AutoTokenizer
from transformers import MarianMTModel, pipeline

# •===========•
#    COLOURS
# •===========•


def convert_hex_to_rgb(hex):
    """
    Convert a hex color to rgb
    :param hex: the hex color
    :return: the rgb color
    """
    h = hex.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def get_colourmap(c1, c2):
    """
    Creates a colourmap from two colours in hex
    :param c1: The first colour
    :param c2: The second colour
    :return: The colourmap
    """
    rgb1 = convert_hex_to_rgb(c1)
    rgb2 = convert_hex_to_rgb(c2)
    
    n = 256
    vals = np.ones((n, 4))
    vals[:, 0] = np.linspace(rgb1[0] / rgb2[0] + 1, 1, n)
    vals[:, 1] = np.linspace(rgb1[1] / rgb2[1] + 1, 1, n)
    vals[:, 2] = np.linspace(rgb1[2] / rgb2[2] + 1, 1, n)
    return ListedColormap(vals)

# •====================•
#    TEXT TRANSLATION
# •====================•

detect_language = pipeline("text-classification", "papluca/xlm-roberta-base-language-detection")

translation_models = {}


def getLanguage(text):
    """
    Detect the language of a text
    :param text: the text to detect
    :return: the language of the text
    """
    # batch = detection_tokenizer([text], return_tensors="pt")
    # with torch.no_grad():
    #     outputs = detection_model(**batch)
    #
    # answer: torch.Tensor = outputs.logits.argmax()

    return detect_language(text)[0]["label"]


def translate(text, src, trg):
    """
    Translate a text from a language to another
    :param text: the text to translate
    :param src: the source language
    :param trg: the target language
    :return: the translated text
    """
    if (src, trg) not in translation_models:
        model_name = f"Helsinki-NLP/opus-mt-{src}-{trg}"
        translation_models[(src, trg)] = (
            MarianMTModel.from_pretrained(model_name), AutoTokenizer.from_pretrained(model_name))

    translation_model, translation_tokenizer = translation_models[(src, trg)]

    batch = translation_tokenizer([text], return_tensors="pt")
    generated_ids = translation_model.generate(**batch)
    return translation_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


def toEnglish(text):
    """
    Translate a text to english
    :param text: the text to translate
    :return: the translated text
    """
    language = getLanguage(text)

    if language == "en":
        return text
    if language == "fr":
        return translate(text, language, "en")
    return text




def toFrench(text):
    """
    Translate a text in English to French
    :param text: the text to translate
    :return: the translated text
    """
    return translate(text, "en", "fr")


# •==============•
#    DECORATORS
# •==============•

def timeIt(func):
    """
    Decorator to time a function
    :param func: the function to time
    :return: the function with a timer
    """
    import time

    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time() - ts

        print(f"Function {func.__name__} took {te:.2f} seconds")
        return result

    return timed


def printExceptions(f):
    """
    Decorator that prints the exceptions of a function
    :param f: the function to be wrapped
    :return: the wrapped function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            traceback.print_exc()

    return wrapper
