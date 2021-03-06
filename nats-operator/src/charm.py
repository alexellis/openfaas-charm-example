#!/usr/bin/env python3
# Copyright 2020 alex
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

class NatsCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on["nats-address"].relation_joined, self._on_nats_address_joined)
        self.framework.observe(self.on["nats-address"].relation_changed, self._on_nats_address_changed)

    def _on_nats_address_changed(self, event):
        logger.info("changed {} {} {}".format(self.app.name, self.app, vars(event.relation.data)))
        ingress_ip = self.model.get_binding(event.relation).network.ingress_address

        logger.info("NATS changed IP: {}".format(ingress_ip))

        other_relation_data = event.relation.data[self.unit]
        other_relation_data['ip'] = "{}".format(ingress_ip)

    def _on_nats_address_joined(self, event):
        logger.info("joined {} {} {}".format(self.app.name, self.app, vars(event.relation.data)))
        ingress_ip = self.model.get_binding(event.relation).network.ingress_address

        logger.info("NATS joined IP: {}".format(ingress_ip))

        other_relation_data = event.relation.data[self.unit]
        other_relation_data['ip'] = "{}".format(ingress_ip)


    def _on_config_changed(self, _=None):

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        pod_spec = self._build_pod_spec()
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus("NATS pod ready.")


    def _build_pod_spec(self):

        spec = {
            "version": 3,
            "containers": [
                {
                    "name": self.app.name,
                    "imageDetails": {"imagePath": "nats-streaming:0.17.0"},
                    "ports": [{"containerPort": 4222, "protocol": "TCP"}],
                    "envConfig": {
                    },
                    "command": ["/nats-streaming-server", "--store=memory","--cluster_id=faas-cluster"],
                }
            ]
        }

        return spec


if __name__ == "__main__":
    main(NatsCharm)
