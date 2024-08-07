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

from cloudai import InstallStatusResult
from cloudai.systems.slurm.strategy import SlurmInstallStrategy


class ChakraReplaySlurmInstallStrategy(SlurmInstallStrategy):
    """Installation strategy for CommsTraceReplay on Slurm systems."""

    def is_installed(self) -> InstallStatusResult:
        return InstallStatusResult(success=True)

    def install(self) -> InstallStatusResult:
        return self.is_installed()

    def uninstall(self) -> InstallStatusResult:
        return InstallStatusResult(success=True)
