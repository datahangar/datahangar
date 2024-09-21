SHELL=/bin/bash
N_ROUTERS:=12

#Note don't use 10.1.1.0/24 in Github actions; it is probably
#used by runners. Offset it (e.g. 10.50.X.1 where X is the router)

KCTL:=minikube kubectl --
NS:=datahangar-stack
NET_NS:=svc_test
IFACE:=$(shell ip route | grep 10.96.0.0 | sed 's/.*dev \(.*\)/\1/')
COLLECT_LOGS_TIME_S:=15

OUTPUT_FOLDER:=.output

check: _folder _add_tap_ips _start_nfacctd _start_routers _check_outputs

_folder:
	mkdir -p $(OUTPUT_FOLDER)

_start_nfacctd:
	echo "Adding nfacctd and services..."
	$(KCTL) create namespace $(NS) || true
	$(KCTL) -n $(NS) create configmap nfacctd-mock-binary --from-file=nfacctd_mock.py || true
	$(KCTL) -n $(NS) apply -k .
	echo "nfacctd and services applied"
_add_tap_ips:
	echo "Creating NS=$(NS) and veths, addrs and routes ..."
	sudo ip netns add $(NET_NS)
	sudo ip link add type veth
	sudo ip link set up dev veth0
	sudo ip addr add 192.168.0.1/24 dev veth0
	sudo ip link set netns $(NET_NS) dev veth1
	sudo ip netns exec $(NET_NS) ip link set up dev veth1
	for (( i=1; i<=$(N_ROUTERS); i++ )); do sudo ip netns exec $(NET_NS) ip addr add 10.50.$$i.1/32 dev veth1; done
	sudo ip netns exec $(NET_NS) ip addr add 192.168.0.2/24 dev veth1
	sudo ip netns exec $(NET_NS) ip route add default via 192.168.0.1
	sudo ip route add 10.0.0.0/8 via 192.168.0.2
	sudo sysctl -w net.ipv4.ip_forward=1
	sudo sysctl -w net.ipv6.conf.all.forwarding=1
	echo "All network infrastructure created"

_start_routers:
	echo "Starting routers ..."
	sudo docker run -t --privileged --network=host -e DIRECTION=ingress -e IFACES=veth0 ghcr.io/datahangar/sfunnel:0.0.6
	echo "Attached BPF program to veth0"
	while [[ "$${IP_LB_SVC}" == "" ]]; do \
		IP_LB_SVC=`$(KCTL) -n $(NS) get svc flowlogs-ingestor -o jsonpath='{.status.loadBalancer.ingress[0].ip}'`; \
		[[ "$${IP_LB_SVC}" != "" ]] || $(KCTL) -n $(NS) get svc flowlogs-ingestor; \
	done; \
	echo "LB IP: $${IP_LB_SVC}"; \
	for (( i=1; i<=$(N_ROUTERS); i++ )); do \
		sudo ip netns exec $(NET_NS) bash -c "python3 -u router_mock.py $${IP_LB_SVC} 10.50.$$i.1 2>&1 > $(OUTPUT_FOLDER)/router_$$i.log &"; \
	done
	echo "All routers started"

_check_outputs:
	echo "Env"
	sudo ip link show
	sudo ip addr show
	sudo ip route show
	sudo ip netns exec $(NET_NS) ip link show
	sudo ip netns exec $(NET_NS) ip addr show
	sudo ip netns exec $(NET_NS) ip route show
	echo "Make sure traffic is flowing first..."
	sudo tcpdump -i $(IFACE) 'tcp dst port 179' -c 1
	echo "Waiting for convergence (TCP established, UDP funneled thru TCP)"
	sudo tcpdump -i $(IFACE) 'tcp and src port 540 and dst port 179' -c 1
	echo "Waiting for traffic to flow ($(COLLECT_LOGS_TIME_S)sec)..."
	sleep $(COLLECT_LOGS_TIME_S)
	echo "Retrieving POD logs"
	for POD in $$($(KCTL) get pods -n datahangar-stack -o name); do \
		POD_STR=$$(echo $$POD | sed 's#/#_#g'); \
		$(KCTL) logs -c nfacctd-worker -n datahangar-stack $$POD > $(OUTPUT_FOLDER)/$$POD_STR.log; \
	done
	echo -n "Checking logs for no errors..."
	cat $(OUTPUT_FOLDER)/pod_*.log > .worker_logs
	python3 check_logs.py .worker_logs || exit 1
	echo -n "Checking logs for IP preservation..."
	for (( i=1; i<=$(N_ROUTERS); i++ )); do \
		if [[ "$$(grep "10.50.$$i.1" .worker_logs)" == "" ]]; then \
			echo "FAILURE: no logs for 10.50.$$i.1 which indicate SRC IP is not being preserved!";\
			exit 1; \
		fi \
	done
	echo "OK"

clean: _stop_routers _stop_nfacctd _del_tap_ips
	rm -rf $(OUTPUT_FOLDER) || true
	$(KCTL) delete namespace $(NS) || true
_stop_routers:
	rm -rf .worker_logs || true
	sudo ip netns exec $(NET_NS) killall -9 router_mock.py || true
_stop_nfacctd:
	$(KCTL) -n $(NS) delete -k . || true
	$(KCTL) -n $(NS) delete configmap nfacctd-mock-binary || true
_del_tap_ips:
	sudo ip route del 10.0.0.0/8 via 192.168.0.2 || true
	sudo ip link del dev veth0 || true
	sudo ip netns del $(NET_NS) || true
