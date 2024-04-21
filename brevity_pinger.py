from flask import Flask
from threading import Thread

app = Flask(__name__)

# @app.route('/')
# def home():
#     return "Hello, I am listening!"

@app.route("/")
def index():
  return "Hello, I am listening!"

def run():
  # app.run(host='0.0.0.0',port=8080)
  from waitress import serve
  serve(app, host="0.0.0.0", port=8080)

def listen_for_brevity():
    t = Thread(target=run)
    t.start()
    
