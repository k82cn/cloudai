# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

import logging
from typing import Any, Dict, List, Optional, Type

from .strategy import (
    CommandGenStrategy,
    GradingStrategy,
    InstallStrategy,
    JobIdRetrievalStrategy,
    ReportGenerationStrategy,
    StrategyRegistry,
)
from .system import System


class TestTemplate:
    """
    Base class representing a test template, providing a framework for test
    execution, including installation, uninstallation, and execution command
    generation based on system configurations and test parameters.

    Attributes:
        name (str): Unique name of the test template.
        env_vars (Dict[str, Any]): Default environment variables.
        cmd_args (Dict[str, Any]): Default command-line arguments.
        logger (logging.Logger): Logger for the test template.
        install_strategy (InstallStrategy): Strategy for installing test
            prerequisites.
        command_gen_strategy (CommandGenStrategy): Strategy for generating
            execution commands.
        job_id_retrieval_strategy (JobIdRetrievalStrategy): Strategy for
            retrieving job IDs.
        report_generation_strategy (ReportGenerationStrategy): Strategy for
            generating reports.
        grading_strategy (GradingStrategy): Strategy for grading performance
            based on test outcomes.
    """

    __test__ = False

    def __init__(
        self,
        system: System,
        name: str,
        env_vars: Dict[str, Any],
        cmd_args: Dict[str, Any],
    ) -> None:
        """
        Initializes a TestTemplate instance.

        Args:
            name (str): Name of the test template.
            env_vars (Dict[str, Any]): Environment variables.
            cmd_args (Dict[str, Any]): Command-line arguments.
        """
        self.system = system
        self.name = name
        self.env_vars = env_vars
        self.cmd_args = cmd_args
        self.logger = logging.getLogger(__name__ + ".TestTemplate")
        self.install_strategy = self._fetch_strategy(InstallStrategy)
        self.command_gen_strategy = self._fetch_strategy(CommandGenStrategy)
        self.job_id_retrieval_strategy = self._fetch_strategy(JobIdRetrievalStrategy)
        self.report_generation_strategy = self._fetch_strategy(ReportGenerationStrategy)
        self.grading_strategy = self._fetch_strategy(GradingStrategy)

    def __repr__(self) -> str:
        """
        Returns a string representation of the TestTemplate instance.

        Returns:
            str: String representation of the test template.
        """
        return f"TestTemplate(name={self.name})"

    def _fetch_strategy(self, strategy_interface: Type) -> Optional[Any]:
        """
        Fetches a strategy from the registry based on system and template.

        Args:
            strategy_interface: Type of strategy to fetch.

        Returns:
            An instance of the requested strategy, or None.
        """
        strategy_class = StrategyRegistry.get_strategy(
            strategy_interface=strategy_interface,
            system_type=type(self.system),
            template_type=type(self),
        )
        if strategy_class:
            if strategy_interface in [
                InstallStrategy,
                CommandGenStrategy,
                GradingStrategy,
            ]:
                return strategy_class(self.system, self.env_vars, self.cmd_args)
            else:
                return strategy_class()
        else:
            self.logger.warning(
                f"No {strategy_interface.__name__} found for "
                f"{type(self).__name__} and "
                f"{type(self.system).__name__}"
            )
            return None

    def is_installed(self) -> bool:
        """
        Checks if the test template is already installed on the specified system.

        Returns:
            bool: True if installed, False otherwise.
        """
        if self.install_strategy is not None:
            return self.install_strategy.is_installed()
        else:
            return True

    def install(self) -> None:
        """
        Installs the test template at the specified location using the system's
        installation strategy.
        """
        if self.install_strategy is not None:
            self.install_strategy.install()

    def uninstall(self) -> None:
        """
        Uninstalls the test template from the specified location using the system's
        uninstallation strategy.
        """
        if self.install_strategy is not None:
            self.install_strategy.uninstall()

    def gen_exec_command(
        self,
        env_vars: Dict[str, str],
        cmd_args: Dict[str, str],
        extra_env_vars: Dict[str, str],
        extra_cmd_args: str,
        output_path: str,
        nodes: List[str],
    ) -> str:
        """
        Generates an execution command for a test using this template.

        This method must be implemented by subclasses.

        Args:
            env_vars (Dict[str, str]): Environment variables for the test.
            cmd_args (Dict[str, str]): Command-line arguments for the test.
            extra_env_vars (Dict[str, str]): Extra environment variables.
            extra_cmd_args (str): Extra command-line arguments.
            output_path (str): Path to the output directory.
            nodes (List[str]): A list of nodes where the test will be executed.

        Returns:
            str: The generated execution command.
        """
        if not nodes:
            nodes = []
        assert self.command_gen_strategy is not None
        return self.command_gen_strategy.gen_exec_command(
            env_vars,
            cmd_args,
            extra_env_vars,
            extra_cmd_args,
            output_path,
            nodes,
        )

    def get_job_id(self, stdout: str, stderr: str) -> Optional[int]:
        """
        Retrieves the job ID from the execution output using the job ID retrieval
        strategy.

        Args:
            stdout (str): Standard output from the test execution.
            stderr (str): Standard error from the test execution.

        Returns:
            Optional[int]: The retrieved job ID, or None if not found.
        """
        assert self.job_id_retrieval_strategy is not None
        return self.job_id_retrieval_strategy.get_job_id(stdout, stderr)

    def can_handle_directory(self, directory_path: str) -> bool:
        """
        Determine if the strategy can handle the directory.

        Args:
            directory_path (str): Path to the directory.

        Returns:
            bool: True if can handle, False otherwise.
        """
        if self.report_generation_strategy is not None:
            return self.report_generation_strategy.can_handle_directory(directory_path)
        else:
            return False

    def generate_report(self, directory_path: str, sol: Optional[float] = None) -> None:
        """
        Generate a report from the directory.

        Args:
            directory_path (str): Path to the directory.
            sol (Optional[float]): Speed-of-light performance for reference.
        """
        if self.report_generation_strategy is not None:
            return self.report_generation_strategy.generate_report(directory_path, sol)

    def grade(self, directory_path: str, ideal_perf: float) -> Optional[float]:
        """
        Read the performance value from the directory.

        Args:
            directory_path (str): Path to the directory containing performance data.
            ideal_perf (float): The ideal performance metric to compare against.

        Returns:
            Optional[float]: The performance value read from the directory.
        """
        if self.grading_strategy is not None:
            return self.grading_strategy.grade(directory_path, ideal_perf)
