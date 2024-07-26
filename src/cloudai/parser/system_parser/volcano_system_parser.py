# SPDX-FileCopyrightText: NVIDIA CORPORATION & AFFILIATES
# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Any, Dict, List

from cloudai import BaseSystemParser
from cloudai.systems.volcano import VolcanoSystem


class VolcanoSystemParser(BaseSystemParser):
    """Parser for parsing Slurm system configurations."""

    def parse(self, data: Dict[str, Any]) -> VolcanoSystem:  # noqa: C901
        """
        Parse the Slurm system configuration.

        Args:
            data (Dict[str, Any]): The loaded configuration data.

        Returns:
            SlurmSystem: The parsed Slurm system object.

        Raises:
            ValueError: If 'name' or 'partitions' are missing from the data or if there are node list parsing issues
            or group membership conflicts.
        """

        def safe_int(value):
            try:
                return int(value) if value is not None else None
            except ValueError:
                return None

        def str_to_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            return value.lower() in ("true", "1", "yes")

        name = data.get("name")
        if not name:
            raise ValueError("Missing mandatory field: 'name'")

        install_path = data.get("install_path")
        if not install_path:
            raise ValueError("Field 'install_path' is required.")
        install_path = os.path.abspath(install_path)

        output_path = data.get("output_path")
        if not output_path:
            raise ValueError("Field 'output_path' is required.")
        output_path = os.path.abspath(output_path)

        default_partition = data.get("default_queue")
        if not default_partition:
            raise ValueError("Field 'default_queue' is required.")

        partitions = data.get("queues")
        if not partitions:
            raise ValueError("Missing mandatory field: 'queues'")

        # Check if default_partition exists in partitions
        partition_names = [partition_data.get("name") for partition_data in partitions.values()]
        if default_partition not in partition_names:
            raise ValueError(f"Default queue '{default_partition}' is not listed in queues.")

        global_env_vars = data.get("global_env_vars", {})

        mpi = data.get("mpi", "pmix")
        ntasks_per_node = safe_int(data.get("task_resreq"))

        nodes_dict: Dict[str, SlurmNode] = {}
        updated_partitions: Dict[str, List[SlurmNode]] = {}
        updated_groups: Dict[str, Dict[str, List[SlurmNode]]] = {}

        for partition_data in partitions.values():
            partition_name = partition_data.get("name")
            if not partition_name:
                raise ValueError("Partition data does not include a 'name' field.")

            raw_nodes = partition_data.get("nodes", [])
            node_names = set()
            for group in raw_nodes:
                node_names.update(set(SlurmSystem.parse_node_list(group)))

            if not node_names:
                raise ValueError(f"No valid nodes found in partition '{partition_name}'")

            partition_nodes = []
            for node_name in node_names:
                if node_name not in nodes_dict:
                    node = SlurmNode(
                        name=node_name,
                        partition=partition_name,
                        state=SlurmNodeState.UNKNOWN_STATE,
                    )
                    nodes_dict[node_name] = node
                else:
                    node = nodes_dict[node_name]
                    node.partition = partition_name
                partition_nodes.append(node)
            updated_partitions[partition_name] = partition_nodes

            groups = partition_data.get("groups", {})
            updated_groups[partition_name] = {}
            for group_data in groups.values():
                group_name = group_data.get("name")
                if not group_name:
                    raise ValueError("Group data does not include a 'name' field.")

                raw_nodes = group_data.get("nodes", [])
                group_node_names = set()
                for group in raw_nodes:
                    group_node_names.update(set(SlurmSystem.parse_node_list(group)))

                group_nodes = []
                for group_node_name in group_node_names:
                    if group_node_name in nodes_dict:
                        group_nodes.append(nodes_dict[group_node_name])
                    else:
                        raise ValueError(
                            f"Node '{group_node_name}' in group '{group_name}' not found in partition "
                            "'{partition_name}' nodes."
                        )

                updated_groups[partition_name][group_name] = group_nodes

        return VolcanoSystem(
            name=name,
            install_path=install_path,
            output_path=output_path,
            default_partition=default_partition,
            partitions=updated_partitions,
            account=account,
            distribution=distribution,
            mpi=mpi,
            gpus_per_node=gpus_per_node,
            ntasks_per_node=ntasks_per_node,
            groups=updated_groups,
            global_env_vars=global_env_vars,
        )