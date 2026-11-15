import json
from datetime import date

import pytest

from kinn.data import seal

OPEN, SEALED = date(2023, 11, 8), date(2023, 11, 9)


def test_dates_before_the_seal_pass():
    seal.check_range(date(2010, 1, 1), OPEN, source="t")


@pytest.mark.parametrize("end", [SEALED, date(2026, 1, 1)])
def test_holdout_dates_raise(end):
    with pytest.raises(seal.HoldoutError):
        seal.check_range(date(2010, 1, 1), end, source="t")


def test_the_flag_alone_or_the_token_alone_is_not_enough(tmp_path):
    with pytest.raises(seal.HoldoutError):
        seal.check_range(OPEN, SEALED, source="t", unseal=True, log_dir=tmp_path, env={})
    with pytest.raises(seal.HoldoutError):
        seal.check_range(OPEN, SEALED, source="t", log_dir=tmp_path, env={seal.TOKEN_VARIABLE: "x"})
    assert not (tmp_path / seal.UNSEAL_LOG_NAME).exists()


def test_an_unseal_is_logged_without_the_token(tmp_path):
    env = {seal.TOKEN_VARIABLE: "owner-secret"}
    seal.check_range(OPEN, SEALED, source="final-test", unseal=True, log_dir=tmp_path, env=env)
    text = (tmp_path / seal.UNSEAL_LOG_NAME).read_text()
    record = json.loads(text)
    assert record["source"] == "final-test" and record["end"] == "2023-11-09"
    assert "owner-secret" not in text


def test_an_unseal_that_cannot_be_logged_is_refused():
    with pytest.raises(seal.HoldoutError):
        seal.check_range(OPEN, SEALED, source="t", unseal=True, env={seal.TOKEN_VARIABLE: "x"})
