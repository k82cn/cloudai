from pathlib import Path

import pytest
from cloudai.schema.system import SlurmSystem
from cloudai.schema.system.slurm import SlurmNode, SlurmNodeState
from cloudai.schema.system.slurm.strategy import SlurmCommandGenStrategy
from cloudai.schema.test_template.nccl_test.slurm_command_gen_strategy import NcclTestSlurmCommandGenStrategy
from cloudai.schema.test_template.nemo_launcher.slurm_command_gen_strategy import NeMoLauncherSlurmCommandGenStrategy


@pytest.fixture
def slurm_system(tmp_path: Path) -> SlurmSystem:
    slurm_system = SlurmSystem(
        name="TestSystem",
        install_path=str(tmp_path / "install"),
        output_path=str(tmp_path / "output"),
        default_partition="main",
        partitions={"main": [SlurmNode(name="node1", partition="main", state=SlurmNodeState.IDLE)]},
    )
    Path(slurm_system.install_path).mkdir()
    Path(slurm_system.output_path).mkdir()
    return slurm_system


@pytest.fixture
def strategy_fixture(slurm_system: SlurmSystem) -> SlurmCommandGenStrategy:
    env_vars = {"TEST_VAR": "VALUE"}
    cmd_args = {"test_arg": "test_value"}
    strategy = SlurmCommandGenStrategy(slurm_system, env_vars, cmd_args)
    return strategy


def test_filename_generation(strategy_fixture: SlurmCommandGenStrategy, tmp_path: Path):
    args = {"job_name": "test_job", "num_nodes": 2, "partition": "test_partition", "node_list_str": "node1,node2"}
    env_vars_str = "export TEST_VAR=VALUE"
    srun_command = "srun --test test_arg"
    output_path = str(tmp_path)

    sbatch_command = strategy_fixture._write_sbatch_script(args, env_vars_str, srun_command, output_path)
    filepath_from_command = sbatch_command.split()[-1]

    # Check that the file exists at the specified path
    assert tmp_path.joinpath("cloudai_sbatch_script.sh").exists()

    # Read the file and check the contents
    with open(filepath_from_command, "r") as file:
        file_contents = file.read()
    assert "test_job" in file_contents
    assert "node1,node2" in file_contents
    assert "srun --test test_arg" in file_contents

    # Check the correctness of the sbatch command format
    assert sbatch_command == f"sbatch {filepath_from_command}"


class TestNcclTestSlurmCommandGenStrategy__GetDockerImagePath:
    @pytest.fixture
    def nccl_slurm_cmd_gen_strategy_fixture(self, slurm_system: SlurmSystem) -> NcclTestSlurmCommandGenStrategy:
        env_vars = {"TEST_VAR": "VALUE"}
        cmd_args = {"test_arg": "test_value"}
        strategy = NcclTestSlurmCommandGenStrategy(slurm_system, env_vars, cmd_args)
        return strategy

    def test_cmd_arg_file_doesnt_exist(self, nccl_slurm_cmd_gen_strategy_fixture: NcclTestSlurmCommandGenStrategy):
        cmd_args = {"docker_image_url": f"{nccl_slurm_cmd_gen_strategy_fixture.install_path}/docker_image"}
        image_path = nccl_slurm_cmd_gen_strategy_fixture.get_docker_image_path(cmd_args)
        assert image_path == f"{nccl_slurm_cmd_gen_strategy_fixture.install_path}/nccl-test/nccl_test.sqsh"

    def test_cmd_arg_file_exists(self, nccl_slurm_cmd_gen_strategy_fixture: NcclTestSlurmCommandGenStrategy):
        cmd_args = {"docker_image_url": f"{nccl_slurm_cmd_gen_strategy_fixture.install_path}/docker_image"}
        Path(cmd_args["docker_image_url"]).touch()
        image_path = nccl_slurm_cmd_gen_strategy_fixture.get_docker_image_path(cmd_args)
        assert image_path == cmd_args["docker_image_url"]


class TestNeMoLauncherSlurmCommandGenStrategy__SetContainerArg:
    @pytest.fixture
    def nemo_cmd_gen(self, slurm_system: SlurmSystem) -> NeMoLauncherSlurmCommandGenStrategy:
        env_vars = {"TEST_VAR": "VALUE"}
        cmd_args = {"test_arg": "test_value"}
        strategy = NeMoLauncherSlurmCommandGenStrategy(slurm_system, env_vars, cmd_args)
        return strategy

    def test_docker_image_url_is_not_file(self, nemo_cmd_gen: NeMoLauncherSlurmCommandGenStrategy):
        nemo_cmd_gen.final_cmd_args["docker_image_url"] = f"{nemo_cmd_gen.install_path}/docker_image"
        nemo_cmd_gen.set_container_arg()
        assert (
            nemo_cmd_gen.final_cmd_args["container"]
            == f"{nemo_cmd_gen.install_path}/NeMo-Megatron-Launcher/nemo_megatron_launcher.sqsh"
        )

    def test_docker_image_url_is_file(self, nemo_cmd_gen: NeMoLauncherSlurmCommandGenStrategy):
        nemo_cmd_gen.final_cmd_args["docker_image_url"] = f"{nemo_cmd_gen.install_path}/docker_image"
        Path(nemo_cmd_gen.final_cmd_args["docker_image_url"]).touch()
        nemo_cmd_gen.set_container_arg()
        assert nemo_cmd_gen.final_cmd_args["container"] == nemo_cmd_gen.final_cmd_args["docker_image_url"]
