import os
import pytest

from rag_studio.inference import repo_handling
from rag_studio.hf_repo_storage import api, init_repo, repo_exists
from rag_studio.tests.conftest import (
    TEST_PREFS_REPO,
    TEST_REPO_NAME,
    push_initial_repo_prefs,
)
from rag_studio.tests.test_utils import make_temp_folder


def test_uses_environment_var_as_prefs_repo_name_if_passed():
    os.environ["__TEST_PREFS_REPO_ID__"] = "thing"
    assert repo_handling.infer_prefs_repo_id() == "thing"
    del os.environ["__TEST_PREFS_REPO_ID__"]


def test_uses_default_prefs_repo_name_if_no_env_var_passed():
    assert os.environ.get("__TEST_PREFS_REPO_ID__") is None
    assert repo_handling.infer_prefs_repo_id() == repo_handling.PREFERENCES_REPO_NAME


TEST_TARGET_REPO_FROM_PREFS = "repo-from-prefs"


@pytest.fixture(name="with_test_prefs_repo")
def with_test_prefs_repo_fixture():
    os.environ["__TEST_PREFS_REPO_ID__"] = TEST_PREFS_REPO
    if not repo_exists(TEST_PREFS_REPO):
        api.create_repo(TEST_PREFS_REPO, private=True, exist_ok=False)
    push_initial_repo_prefs(
        api.get_full_repo_name(TEST_PREFS_REPO), TEST_TARGET_REPO_FROM_PREFS
    )
    yield
    del os.environ["__TEST_PREFS_REPO_ID__"]


def test_inf_server_initialises_with_latest_repo_if_no_repo_id_provided(
    with_test_prefs_repo,
):
    assert (
        repo_handling.infer_repo_id(make_temp_folder()) == TEST_TARGET_REPO_FROM_PREFS
    )


def test_inf_server_bails_if_no_repo_id_and_prefs_repo_doesnt_exist():
    another_repo_name = "another-repo"
    os.environ["__TEST_PREFS_REPO_ID__"] = another_repo_name
    assert not repo_exists(another_repo_name)
    with pytest.raises(Exception):
        repo_handling.infer_repo_id(make_temp_folder())


def test_inf_server_bails_if_no_repo_id_and_prefs_repo_exists_but_no_latest_repo(
    with_test_prefs_repo,
):

    assert repo_exists(TEST_PREFS_REPO)
    push_initial_repo_prefs(api.get_full_repo_name(TEST_PREFS_REPO), None)
    with pytest.raises(Exception):
        repo_handling.infer_repo_id(make_temp_folder())


def test_inf_server_uses_repo_id_if_provided():
    os.environ["RAG_REPO_ID"] = "an_other_repo"
    assert repo_handling.infer_repo_id(make_temp_folder()) == "an_other_repo"
