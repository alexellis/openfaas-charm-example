#!/usr/bin/env python3
# Copyright 2020 alex
# See LICENSE file for licensing details.

import logging

from pathlib import Path

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus
import yaml
import json

logger = logging.getLogger(__name__)

class OpenfaasCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, _=None): 
        logger.debug("config_change")

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        pod_spec = self._build_pod_spec()
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus("OpenFaaS pod ready.")

    def _build_pod_spec(self):
        namespace = self.model.name

        function_crd = {}
        profiles_crd = {}

        try:
            function_crd = yaml.load(open(Path('files/function_crd.yaml'),"r"), Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print("Error in configuration file:", exc)

        try:
            profiles_crd = yaml.load(open(Path('files/profiles_crd.yaml'),"r"), Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print("Error in configuration file:", exc)

        logger.debug(json.dumps(function_crd["spec"]))

# "functions_provider_url": "http://192.168.0.35:8080",
        spec = {
            "version": 3,
            "kubernetesResources": {
                "customResourceDefinitions": [
                    {
                        "name": function_crd["metadata"]["name"],
                        "labels": {
                            "juju-global-resource-lifecycle": "model",
                        },
                        "spec": function_crd["spec"],
                    },
                    {
                        "name": profiles_crd["metadata"]["name"],
                        "labels": {
                            "juju-global-resource-lifecycle": "model",
                        },
                        "spec": profiles_crd["spec"],
                    },
                ],
            },
            "containers": [
                {
                    "name": self.app.name+"-gateway",
                    "imageDetails": {"imagePath": "openfaas/gateway:0.20.2"},
                    "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                    "envConfig": {
                        "functions_provider_url": "http://127.0.0.1:8081",
                        "direct_functions": "false",
                        "basic_auth": "false",
                        "faas_prometheus_host": "192.168.0.35",
                        "faas_prometheus_port": "9090"
                    }
                },
                {
                    "name": self.app.name+"-provider",
                    "imageDetails": {"imagePath": "openfaas/operator:0.12.9"},
                    "ports": [{"containerPort": 8081, "protocol": "TCP"}],
                    "envConfig": {
                        "port": "8081",
                        "function_namespace": namespace,
                        "cluster_role": "false",
                        "profiles_namespace": namespace
                    }
                }
            ]
        }

        logger.debug(json.dumps(spec))

        return spec


if __name__ == "__main__":
    main(OpenfaasCharm)
