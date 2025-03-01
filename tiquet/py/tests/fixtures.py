import logging
import os
import pytest
import uuid

from algosdk.v2client import algod
from fractions import Fraction
from network_accounts import NetworkAccounts
from tiquet.common.algorand_helper import AlgorandHelper
from tiquet.administrator_client import AdministratorClient
from tiquet.tiquet_client import TiquetClient
from tiquet.tiquet_issuer import TiquetIssuer


logging.basicConfig(format="%(asctime)s %(message)s")


# Environment variables for algod client.
_ALGOD_ADDRESS_ENVVAR = "ALGOD_ADDR"
_ALGOD_TOKEN_ENVVAR = "ALGOD_TOKEN"
_CONSTANTS_APP_TEAL_FPATH_ENVVAR = "CONSTANTS_APP_FPATH"
_APP_TEAL_FPATH_ENVVAR = "APP_FPATH"
_CLEAR_TEAL_FPATH_ENVVAR = "CLEAR_FPATH"
_ESCROW_TEAL_FPATH_ENVVAR = "ESCROW_FPATH"
_SUCCESS_TEAL_FPATH_ENVVAR = "SUCCESS_TEAL_FPATH"


@pytest.fixture(scope="module")
def logger():
    l = logging.getLogger()
    l.setLevel(logging.DEBUG)
    return l


@pytest.fixture(scope="module")
def accounts():
    return NetworkAccounts()


@pytest.fixture(scope="module")
def tiquet_io_account(accounts, logger):
    tiquet_io_account = accounts.get_tiquet_io_account()
    logger.debug("tiquet.io address: {}".format(tiquet_io_account["pk"]))
    return tiquet_io_account


@pytest.fixture(scope="module")
def issuer_account(accounts, logger):
    issuer_account = accounts.get_issuer_account()
    logger.debug("Issuer address: {}".format(issuer_account["pk"]))
    return issuer_account


@pytest.fixture(scope="module")
def buyer_account(accounts, logger):
    buyer_account = accounts.get_buyer_account()
    logger.debug("Buyer address: {}".format(buyer_account["pk"]))
    return buyer_account


@pytest.fixture(scope="module")
def second_buyer_account(accounts, logger):
    second_buyer_account = accounts.get_second_buyer_account()
    logger.debug("Second Buyer address: {}".format(second_buyer_account["pk"]))
    return second_buyer_account


@pytest.fixture(scope="module")
def fraudster_account(accounts, logger):
    fraudster_account = accounts.get_fraudster_account()
    logger.debug("Fraudster address: {}".format(fraudster_account["pk"]))
    return fraudster_account


@pytest.fixture(scope="module")
def tiquet_price():
    return 100000000000


@pytest.fixture(scope="module")
def tiquet_resale_price():
    return 200000000000


@pytest.fixture(scope="module")
def tiquet_processing_fee_frac():
    # 0.1%
    return Fraction(1, 1000)


@pytest.fixture(scope="module")
def tiquet_processing_fee_numerator(tiquet_processing_fee_frac):
    return tiquet_processing_fee_frac.numerator


@pytest.fixture(scope="module")
def tiquet_processing_fee_denominator(tiquet_processing_fee_frac):
    return tiquet_processing_fee_frac.denominator


@pytest.fixture(scope="module")
def issuer_tiquet_royalty_frac():
    # 0.2%
    return Fraction(1, 500)


@pytest.fixture(scope="module")
def issuer_tiquet_royalty_numerator(issuer_tiquet_royalty_frac):
    return issuer_tiquet_royalty_frac.numerator


@pytest.fixture(scope="module")
def issuer_tiquet_royalty_denominator(issuer_tiquet_royalty_frac):
    return issuer_tiquet_royalty_frac.denominator


@pytest.fixture(scope="module")
def constants_app_fpath(logger):
    return _get_envvar_value(_CONSTANTS_APP_TEAL_FPATH_ENVVAR, logger)


@pytest.fixture(scope="module")
def app_fpath(logger):
    return _get_envvar_value(_APP_TEAL_FPATH_ENVVAR, logger)


@pytest.fixture(scope="module")
def clear_fpath(logger):
    return _get_envvar_value(_CLEAR_TEAL_FPATH_ENVVAR, logger)


@pytest.fixture(scope="module")
def escrow_fpath(logger):
    return _get_envvar_value(_ESCROW_TEAL_FPATH_ENVVAR, logger)


@pytest.fixture(scope="module")
def success_teal_fpath(logger):
    return _get_envvar_value(_SUCCESS_TEAL_FPATH_ENVVAR, logger)


@pytest.fixture(scope="module")
def administrator(
    tiquet_io_account,
    constants_app_fpath,
    clear_fpath,
    algodclient,
    algod_params,
    logger,
):
    client = AdministratorClient(
        pk=tiquet_io_account["pk"],
        sk=tiquet_io_account["sk"],
        mnemonic=tiquet_io_account["mnemonic"],
        app_fpath=constants_app_fpath,
        clear_fpath=clear_fpath,
        algodclient=algodclient,
        algod_params=algod_params,
        logger=logger,
    )
    client.deploy_constants_app()
    return client


@pytest.fixture(scope="module")
def constants_app_id(administrator):
    return administrator.constants_app_id


@pytest.fixture(scope="module")
def issuer(
    tiquet_io_account,
    issuer_account,
    constants_app_id,
    app_fpath,
    clear_fpath,
    escrow_fpath,
    algodclient,
    algod_params,
    logger,
):
    return TiquetIssuer(
        pk=issuer_account["pk"],
        sk=issuer_account["sk"],
        mnemonic=issuer_account["mnemonic"],
        app_fpath=app_fpath,
        clear_fpath=clear_fpath,
        escrow_fpath=escrow_fpath,
        algodclient=algodclient,
        algod_params=algod_params,
        logger=logger,
        tiquet_io_account=tiquet_io_account["pk"],
        constants_app_id=constants_app_id,
    )


@pytest.fixture(scope="function")
def tiquet_issuance_info(issuer, tiquet_price, issuer_tiquet_royalty_frac, logger):
    tiquet_name = uuid.uuid4()
    tiquet_id, app_id, escrow_lsig = issuer.issue_tiquet(
        tiquet_name, tiquet_price, issuer_tiquet_royalty_frac
    )
    logger.debug("Tiquet Id: {}".format(tiquet_id))
    logger.debug("App Id: {}".format(app_id))
    logger.debug("Escrow address: {}".format(escrow_lsig.address()))
    return (tiquet_id, app_id, escrow_lsig)


@pytest.fixture(scope="function")
def buyer(
    tiquet_io_account,
    buyer_account,
    constants_app_id,
    algodclient,
    algod_params,
    logger,
):
    return TiquetClient(
        pk=buyer_account["pk"],
        sk=buyer_account["sk"],
        mnemonic=buyer_account["mnemonic"],
        algodclient=algodclient,
        algod_params=algod_params,
        logger=logger,
        tiquet_io_account=tiquet_io_account["pk"],
        constants_app_id=constants_app_id,
    )


@pytest.fixture(scope="function")
def second_buyer(
    tiquet_io_account,
    second_buyer_account,
    constants_app_id,
    tiquet_issuance_info,
    algodclient,
    algod_params,
    logger,
):
    return TiquetClient(
        pk=second_buyer_account["pk"],
        sk=second_buyer_account["sk"],
        mnemonic=second_buyer_account["mnemonic"],
        algodclient=algodclient,
        algod_params=algod_params,
        logger=logger,
        tiquet_io_account=tiquet_io_account["pk"],
        constants_app_id=constants_app_id,
    )


@pytest.fixture(scope="function")
def fraudster_buyer(
    tiquet_io_account,
    fraudster_account,
    constants_app_id,
    tiquet_issuance_info,
    algodclient,
    algod_params,
    logger,
):
    return TiquetClient(
        pk=fraudster_account["pk"],
        sk=fraudster_account["sk"],
        mnemonic=fraudster_account["mnemonic"],
        algodclient=algodclient,
        algod_params=algod_params,
        logger=logger,
        tiquet_io_account=tiquet_io_account["pk"],
        constants_app_id=constants_app_id,
    )


@pytest.fixture(scope="function")
def initial_sale(tiquet_issuance_info, buyer, issuer_account, tiquet_price, logger):
    tiquet_id, app_id, escrow_lsig = tiquet_issuance_info

    buyer.buy_tiquet(
        tiquet_id=tiquet_id,
        app_id=app_id,
        escrow_lsig=escrow_lsig,
        issuer_account=issuer_account["pk"],
        seller_account=issuer_account["pk"],
        amount=tiquet_price,
    )


@pytest.fixture(scope="function")
def post_for_resale(
    tiquet_issuance_info, initial_sale, buyer, tiquet_resale_price, logger
):
    tiquet_id, app_id, escrow_lsig = tiquet_issuance_info

    buyer.post_for_resale(
        tiquet_id=tiquet_id,
        app_id=app_id,
        tiquet_price=tiquet_resale_price,
    )


@pytest.fixture(scope="module")
def algodclient():
    if _ALGOD_ADDRESS_ENVVAR not in os.environ:
        raise ValueError(
            "algod address environment variable '{}' not set".format(
                _ALGOD_ADDRESS_ENVVAR
            )
        )

    if _ALGOD_TOKEN_ENVVAR not in os.environ:
        raise ValueError(
            "algod token environment variable '{}' not set".format(ALGOD_TOKEN)
        )

    algod_address = os.environ.get(_ALGOD_ADDRESS_ENVVAR)
    algod_token = os.environ.get(_ALGOD_TOKEN_ENVVAR)
    headers = {
        "X-API-Key": algod_token,
    }

    return algod.AlgodClient(
        algod_token=algod_token, algod_address=algod_address, headers=headers
    )


@pytest.fixture(scope="module")
def algod_params(algodclient):
    # Set network params for transactions.
    params = algodclient.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    return params


@pytest.fixture(scope="module")
def algorand_helper(algodclient, logger):
    return AlgorandHelper(algodclient, logger)


def _get_envvar_value(envvar, logger):
    if envvar not in os.environ:
        raise ValueError("Environment variable '{}' not set".format(envvar))

    envvar_val = os.environ.get(envvar)
    logger.debug("%s = %s" % (envvar, envvar_val))

    return envvar_val
