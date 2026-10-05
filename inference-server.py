import json
import os
import requests
from flask import Flask, jsonify, request

MODELS_DIR = os.environ.get("MODELS_DIR", os.path.join(os.path.expanduser("~"), "models"))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models.json")) as f:
	MODELS = json.load(f)


class Model:
	def __init__(self, id, name, huggingface_url, context_size, description):
		self.id = id
		self.name = name
		self.huggingface_url = huggingface_url
		self.context_size = context_size
		self.description = description


class InferenceServer:
	def __init__(self):
		self.models = []
		for name, cfg in MODELS.items():
			self.models.append(Model(
				id=name,
				name=name,
				huggingface_url=cfg["huggingface_url"],
				context_size=cfg["context_size"],
				description=cfg["description"],
			))

	def model(self, id):
		return next(m for m in self.models if m.id == id)

	def load(self, model):
		path = os.path.join(MODELS_DIR, os.path.basename(model.huggingface_url))
		if os.path.isfile(path):
			return
		os.makedirs(MODELS_DIR, exist_ok=True)
		r = requests.get(model.huggingface_url, stream=True)
		r.raise_for_status()
		tmp_path = path + ".part"
		with open(tmp_path, "wb") as f:
			for chunk in r.iter_content(chunk_size=1 << 20):
				f.write(chunk)
		os.rename(tmp_path, path)


class API:
	def __init__(self, server):
		self.server = server

	def models(self):
		return {
			"object": "list",
			"data": [{"id": model.id, "object": "model", "created": 0, "owned_by": "local"}
					 for model in self.server.models],
		}

	def model(self, model_id):
		model = self.server.model(model_id)
		return {"id": model.id, "object": "model", "created": 0, "owned_by": "local"}

	def chat_completions(self, model_id, messages):
		model = self.server.model(model_id)
		self.server.load(model)


if __name__ == "__main__":
	server = InferenceServer()
	api = API(server)
	app = Flask(__name__)

	@app.route("/v1/models")
	def route_models():
		return jsonify(api.models())

	@app.route("/v1/models/<model_id>")
	def route_model(model_id):
		return jsonify(api.model(model_id))

	@app.route("/v1/chat/completions", methods=["POST"])
	def route_chat_completions():
		data = request.get_json()
		return jsonify(api.chat_completions(data.get("model"), data.get("messages")))

	app.run(host="0.0.0.0", port=8080)