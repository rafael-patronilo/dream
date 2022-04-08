import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
MAX_HISTORY_DEPTH = 3

try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("dialogpt is set to run on cuda")

    logger.info("dialogpt is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_response(context):
    global model, tokenizer
    encoded_context = []
    for uttr in context[-MAX_HISTORY_DEPTH:]:
        encoded_context += [tokenizer.encode(uttr + tokenizer.eos_token, return_tensors="pt")]
    bot_input_ids = torch.cat(encoded_context, dim=-1)

    with torch.no_grad():
        if torch.cuda.is_available():
            bot_input_ids = bot_input_ids.to("cuda")
        chat_history_ids = model.generate(
            bot_input_ids, do_sample=True, max_length=50, top_k=3, pad_token_id=tokenizer.eos_token_id
        )
        if torch.cuda.is_available():
            chat_history_ids = chat_history_ids.cpu()
    return tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1] :][0], skip_special_tokens=True)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])

    try:
        responses = []
        confidences = []
        for context in contexts:
            responses += [generate_response(context)]
            confidences += [DEFAULT_CONFIDENCE]
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(contexts)
        confidences = [0.0] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"masked_lm exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))