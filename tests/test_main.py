from unittest.mock import patch

import pytest
import requests

import main


def test_main_propagates_render_failure() -> None:
    with (
        patch.object(main, "kjør_quarto_render", side_effect=RuntimeError("render")),
        patch.object(main, "last_opp_filer_til_nada") as upload,
        pytest.raises(RuntimeError, match="render"),
    ):
        main.main()

    upload.assert_not_called()


def test_main_propagates_upload_failure() -> None:
    with (
        patch.object(main, "kjør_quarto_render"),
        patch.object(
            main,
            "last_opp_filer_til_nada",
            side_effect=requests.RequestException("upload"),
        ),
        pytest.raises(requests.RequestException, match="upload"),
    ):
        main.main()
