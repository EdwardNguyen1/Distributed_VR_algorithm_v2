from flask import Flask, render_template, jsonify, request, Response
app = Flask(__name__)
import zmq, socket
import sys
import json
import time
import numpy as np
import matplotlib.pyplot as pyplot
import os, sys
from util.read_data import *
from util.VR_algorithm import *
from util.cost_func import soft_max
from scipy.misc import imresize
import json
import urllib.request

socket = {}
iplist = []
weight = {}
cost_value_list = []
context = zmq.Context()

@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")

@app.route("/search", methods=['GET'])
def search():
	import socket
	PING_PORT_NUMBER = 9999
	PING_MSG_SIZE = 1
	PING_INTERVAL = 1
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.bind(('', PING_PORT_NUMBER))
	poller = zmq.Poller()
	poller.register(sock, zmq.POLLIN)
	ping_at = time.time()
	for x in range(10):
		timeout = ping_at - time.time()
		if timeout < 0:
			timeout = 0
		events = dict(poller.poll(1000* timeout))
		if sock.fileno() in events:
			msg, addrinfo = sock.recvfrom(PING_MSG_SIZE)
			if addrinfo[0] not in iplist:
				iplist.append(addrinfo[0])
				print (addrinfo[0])
			else:
				print (addrinfo[0] + " already in list.")
		if time.time() >= ping_at:
			print("Pinging peers...")
			sock.sendto(b'!', 0, ("255.255.255.255", PING_PORT_NUMBER))
			ping_at = time.time() + PING_INTERVAL
	return jsonify({'iplist': iplist})

@app.route("/connect", methods=['POST'])
def connect():
	# wait 1 mins
	# urllib.request.urlopen('ip:port')
	index = int(request.json['index'])
	self_IP = str(request.json['self_IP'])
	temp = int(self_IP[-3::])
	temp1 = int(iplist[index][-3::])
	if temp > temp1:
		portnumber = str(temp1)[1::]+str(temp)
	else:
		portnumber = str(temp)[1::]+str(temp1)
	s = context.socket(zmq.PAIR)
	s.bind("tcp://"+str(self_IP)+":"+portnumber)
	print ("tcp://"+str(self_IP)+":"+portnumber)
	s1 = context.socket(zmq.PAIR)
	s1.connect("tcp://"+str(iplist[index])+":"+portnumber)
	print("tcp://"+str(iplist[index])+":"+portnumber)
	socket[index] = [s, s1]
	print (socket)
	return Response(None)

@app.route("/generateWeights", methods=['GET'])
def generate_weights():
	self_nbrNum = len(iplist) # iplist has all my neighboring and my own ip address
	nbr_weights_sum = 0
	print (self_nbrNum)
	for idx, socket_list in socket.items():
		socket_list[0].send_json(self_nbrNum)
	for idx, socket_list in socket.items():
		nbr_nbrNum = socket_list[1].recv_json()
		weight[idx] = 1/max(self_nbrNum, nbr_nbrNum)
		nbr_weights_sum += weight[idx]

	weight[0] = 1 - nbr_weights_sum
		# print (weight_list)
	# self_weight = (1 - sum(weight_list))
	# weight_list.insert(0, self_weight)
	# print(weight_list)

	for idx, w in weight.items():
		print (idx, w)

	return Response(None)

@app.route("/get_data", methods=['POST'])
def get_data():
    tmp_mask=request.json['mask']
    mask = [int(i) for i in tmp_mask if tmp_mask[i]]
    print (mask)
    global vr_alg, X, Y
    X,Y = read_mnist (datatype='multiclass', mask_label=mask)
    X = X[:int(X.shape[0]*0.2)]
    Y = Y[:int(Y.shape[0]*0.2)]

    return Response(None)

@app.route("/run_alg", methods=['POST'])
def run_alg():
    mu = float(request.json['mu'])
    max_ite = int(request.json['max_ite'])
    method = request.json['method']
    start_ite = int(request.json['ite'])
    dist_style = request.json['dist_style']
    iter_per_call = int(request.json['iter_per_call'])
    print ("data received")
    while (start_ite < max_ite):
        if start_ite == 0:
            vr_alg = ZMQ_VR_agent(X,Y, np.random.randn(28*28*10,1), soft_max, socket=socket, rho = 1e-4, weights = weight)
        vr_alg.adapt(mu, start_ite, method, dist_style)
        vr_alg.correct(start_ite, dist_style)
        vr_alg.combine(start_ite, dist_style)

        cost_value = vr_alg.cost_model.func_value()
        cost_value_list.append(cost_value)
        start_ite = start_ite + iter_per_call
    plt.plot(cost_value_list)
    plt.show()

    plt.plot(vr_alg.cost_model.w)
    plt.show()
    return Response(None)


if __name__ == '__main__':
    app.run(debug=False, port = sys.argv[1])
