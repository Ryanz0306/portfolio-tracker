from flask import Flask, jsonify, request, render_template 
import json
import os 
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'