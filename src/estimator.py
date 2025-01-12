import json
import os
import shutil

import sys
from unicodedata import name
import pandas as pd

fpath = os.path.join(os.path.dirname(__file__), 'model')
sys.path.append(fpath)

SERVE_SOCKET = '/tmp/estimator.sock'

###############################################
# power request 

class PowerRequest():
    def __init__(self, metrics, values, output_type, system_features, system_values, model_name="", filter=""):
        self.model_name = model_name
        self.metrics = metrics
        self.filter = filter
        self.output_type = output_type
        self.system_features = system_features
        self.datapoint = pd.DataFrame(values, columns=metrics)
        data_point_size = len(self.datapoint)
        for i in range(len(system_features)):
            self.datapoint[system_features[i]] = [system_values[i]]*data_point_size

###############################################
# serve

import sys
import socket
import signal
from model_server_connector import ModelOutputType, is_weight_output, make_request, get_output_path
from archived_model import get_achived_model
from model.load import load_model
from util.config import set_env_from_model_config

loaded_model = dict()

def handle_request(data):
    try:
        power_request = json.loads(data, object_hook = lambda d : PowerRequest(**d))
    except Exception as e:
        msg = 'fail to handle request: {}'.format(e)
        return {"powers": [], "msg": msg}

    output_type = ModelOutputType[power_request.output_type]
    is_weight = is_weight_output(output_type)
    if is_weight:
        msg = "estimator is not implemented for weight-typed model"
        return {"powers": [], "msg": msg}

    if output_type.name not in loaded_model:
        output_path = get_output_path(output_type)
        if not os.path.exists(output_path):
            # try connecting to model server
            output_path = make_request(power_request)
            if output_path is None:
                # find from config
                output_path = get_achived_model(power_request)
                if output_path is None:
                    return {"powers": [], "msg": "failed to get model"}
        loaded_model[output_type.name] = load_model(output_type.name)
        # remove loaded model
        shutil.rmtree(output_path)

    model = loaded_model[output_type.name]
    print('Estimator model: ', model.model_name)
    powers, msg = model.get_power(power_request)
    if msg != "":
        print("{} fail to predict, removed".format(model.model_name))
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
    return {"powers": powers, "msg": msg}

class EstimatorServer:
    def __init__(self, socket_path):
        self.socket_path = socket_path

    def start(self):
        s = self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self.socket_path)
        s.listen(1)
        try:
            while True:
                connection, _ = s.accept()
                self.accepted(connection)
        finally:
            try:
                os.remove(self.socket_path)
                sys.stdout.write("close socket\n")
            except:
                pass

    def accepted(self, connection):
        data = b''
        while True:
            shunk = connection.recv(1024).strip()
            data += shunk
            if shunk is None or shunk.decode()[-1] == '}':
                break
        decoded_data = data.decode()
        y = handle_request(decoded_data)
        response = json.dumps(y)
        connection.send(response.encode())

def clean_socket():
    print("clean socket")
    if os.path.exists(SERVE_SOCKET):
        os.unlink(SERVE_SOCKET)

def sig_handler(signum, frame) -> None:
    clean_socket()
    sys.exit(1)

import argparse

if __name__ == '__main__':
    set_env_from_model_config()
    clean_socket()
    signal.signal(signal.SIGTERM, sig_handler)
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-e', '--err',
                            required=False,
                            type=str,
                            default='mae', 
                            metavar="<error metric>",
                            help="Error metric for determining the model with minimum error value" )
        args = parser.parse_args()
        DEFAULT_ERROR_KEYS = args.err.split(',')
        server = EstimatorServer(SERVE_SOCKET)
        server.start()
    finally:
        clean_socket()