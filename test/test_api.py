import pytest

from mys_goods_tool.api import get_stoken_v2_by_v1, get_cookie_token_by_stoken
from test.config import test_config, ACCOUNT


@pytest.mark.asyncio
async def test_get_stoken_v2_by_v1():
    result = await get_stoken_v2_by_v1(test_config.accounts[ACCOUNT].cookies,
                                       test_config.accounts[ACCOUNT].device_id_ios)
    assert result[0].success
    assert result[1].stoken_v2 is not None


@pytest.mark.asyncio
async def test_get_cookie_token_by_stoken():
    result = await get_cookie_token_by_stoken(test_config.accounts[ACCOUNT].cookies,
                                              test_config.accounts[ACCOUNT].device_id_ios)
    assert result[0].success
    assert result[1].cookie_token is not None
