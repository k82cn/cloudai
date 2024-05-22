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


class JobSubmissionError(Exception):
    """
    Exception raised for errors that occur during job submission.

    Attributes
        test_name (str): The name of the test associated with the job.
        command (str): The command that was executed to submit the job.
        stdout (str): The standard output from the command execution.
        stderr (str): The standard error from the command execution.
        message (str): A custom message describing the error.
    """

    def __init__(self, test_name: str, command: str, stdout: str, stderr: str, message: str):
        """
        Initialize a JobSubmissionError instance.

        Args:
            test_name (str): The name of the test associated with the job.
            command (str): The command that was executed to submit the job.
            stdout (str): The standard output from the command execution.
            stderr (str): The standard error from the command execution.
            message (str): A custom message describing the error.
        """
        super().__init__(message)
        self.test_name = test_name
        self.command = command
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()
        self.message = message

    def __str__(self):
        """
        Return a formatted string representation of the JobSubmissionError instance.

        Returns
            str: A formatted string with detailed error information.
        """
        return (
            f"\nERROR: Job Submission Failed\n"
            f"\tTest Name: {self.test_name}\n"
            f"\tMessage: {self.message}\n"
            f"\tCommand: '{self.command}'\n"
            f"\tstdout: '{self.stdout}'\n"
            f"\tstderr: '{self.stderr}'\n"
        )


class JobIdRetrievalError(JobSubmissionError):
    """
    Exception raised when a job ID cannot be retrieved after job submission.

    Attributes
        Inherits all attributes from JobSubmissionError.
    """

    pass