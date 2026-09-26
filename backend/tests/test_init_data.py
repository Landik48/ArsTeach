import time

import pytest

from app.security.init_data import InitDataError, sign_init_data, validate_init_data

TOKEN = "test-bot-token"


def make(**overrides) -> str:
    fields = {
        "auth_date": int(time.time()),
        "query_id": "4c0ab423-342b-4e45-aea4-2747dbc500cd",
        "user": {
            "id": 67890,
            "first_name": "Max",
            "last_name": "User",
            "username": None,
            "language_code": "ru",
            "photo_url": None,
        },
        "chat": {"id": 12345, "type": "DIALOG"},
        "ip": "192.168.0.1",
    }
    fields.update(overrides)
    return sign_init_data(fields, TOKEN)


def test_valid_init_data_is_parsed():
    data = validate_init_data(make(start_param="promo_2026"), TOKEN)
    assert data.user.id == 67890
    assert data.user.first_name == "Max"
    assert data.chat is not None and data.chat.type == "DIALOG"
    assert data.start_param == "promo_2026"


def test_non_ascii_values_survive_round_trip():
    raw = make(user={"id": 1, "first_name": "Данила & Со = 100%"})
    assert validate_init_data(raw, TOKEN).user.first_name == "Данила & Со = 100%"


def test_wrong_token_is_rejected():
    with pytest.raises(InitDataError, match="Подпись"):
        validate_init_data(make(), "another-token")


def test_tampered_user_is_rejected():
    raw = make().replace("67890", "11111")
    with pytest.raises(InitDataError):
        validate_init_data(raw, TOKEN)


def test_duplicate_hash_is_rejected():
    raw = make()
    with pytest.raises(InitDataError, match="больше одного раза"):
        validate_init_data(raw + "&hash=deadbeef", TOKEN)


def test_missing_hash_is_rejected():
    raw = make().rsplit("&hash=", 1)[0]
    with pytest.raises(InitDataError, match="нет hash"):
        validate_init_data(raw, TOKEN)


def test_expired_init_data_is_rejected():
    raw = make(auth_date=int(time.time()) - 7200)
    with pytest.raises(InitDataError, match="устарела"):
        validate_init_data(raw, TOKEN, max_age=3600)
    # max_age=None — без проверки срока
    assert validate_init_data(raw, TOKEN, max_age=None).user.id == 67890
