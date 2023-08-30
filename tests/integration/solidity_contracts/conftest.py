import logging

import pytest
from starkware.starknet.core.os.contract_address.contract_address import (
    calculate_contract_address_from_hash,
)
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.testing.contract_utils import gather_deprecated_compiled_class
from web3 import Web3

from tests.utils.contracts import get_contract, use_kakarot_backend
from tests.utils.helpers import generate_random_private_key, hex_string_to_bytes_array

logger = logging.getLogger()


@pytest.fixture(scope="package")
def get_starknet_address(account_proxy_class, kakarot):
    """
    Fixture to return the starknet address of a contract deployed by kakarot using CREATE2
    """

    def _factory(evm_contract_address):
        return calculate_contract_address_from_hash(
            salt=evm_contract_address,
            class_hash=account_proxy_class.class_hash,
            constructor_calldata=[],
            deployer_address=kakarot.contract_address,
        )

    return _factory


@pytest.fixture(scope="package")
def get_solidity_contract(starknet, contract_account_class, kakarot):
    """
    Fixture to attach a modified web3.contract instance to an already deployed contract_account in kakarot.
    """

    def _factory(
        contract_app, contract_name, starknet_contract_address, evm_contract_address, tx
    ):
        """
        This factory is what is actually returned by pytest when requesting the `get_solidity_contract`
        fixture.
        It creates a web3.contract based on the basename of the target solidity file.
        """
        contract_account = StarknetContract(
            starknet.state,
            contract_account_class.abi,
            starknet_contract_address,
            tx,
        )
        contract = get_contract(
            contract_app, contract_name, address=evm_contract_address
        )
        kakarot_contract = use_kakarot_backend(contract, kakarot)
        setattr(kakarot_contract, "contract_account", contract_account)
        setattr(kakarot_contract, "evm_contract_address", evm_contract_address)

        return kakarot_contract

    return _factory


@pytest.fixture(scope="package")
def get_nonce():
    """
    Fixture to get the nonce of a deployed starknet contract.
    """

    async def _factory(starknet_contract: StarknetContract):
        return await starknet_contract.state.state.get_nonce_at(
            starknet_contract.contract_address
        )

    return _factory


@pytest.fixture(scope="package")
def get_storage_at():
    """
    Fixture to get the storage of a deployed starknet contract at a particular key.
    """

    async def _factory(starknet_contract: StarknetContract, key: int):
        return await starknet_contract.state.state.get_storage_at(
            starknet_contract.contract_address, key
        )

    return _factory


@pytest.fixture(scope="package")
def set_storage_at():
    """
    Fixture to set the storage of a deployed starknet contract at a particular key.
    """

    async def _factory(starknet_contract: StarknetContract, key: int, value: int):
        return await starknet_contract.state.state.set_storage_at(
            starknet_contract.contract_address, key, value
        )

    return _factory


@pytest.fixture(scope="package")
def deploy_bytecode(kakarot, deploy_eoa):
    """
    Fixture to deploy a bytecode in kakarot. Returns the EVM address of the deployed contract,
    the corresponding starknet address and the starknet transaction.
    """

    async def _factory(bytecode: str, caller_eoa=None):
        """
        This factory is what is actually returned by pytest when requesting the `deploy_bytecode`
        fixture.
        """
        if caller_eoa is None:
            caller_eoa = await deploy_eoa(
                generate_random_private_key(int(bytecode, 16))
            )

        tx = await kakarot.eth_send_transaction(
            origin=int(caller_eoa.address, 16),
            to=0,
            gas_limit=1_000_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array(bytecode),
        ).execute(caller_address=caller_eoa.starknet_address)

        deploy_event = [
            e
            for e in tx.main_call_events
            if type(e).__name__ == "evm_contract_deployed"
        ][0]

        starknet_contract_address = deploy_event.starknet_contract_address
        evm_contract_address = Web3.to_checksum_address(
            f"{deploy_event.evm_contract_address:040x}"
        )
        return evm_contract_address, starknet_contract_address, tx

    return _factory


@pytest.fixture(scope="package")
def deploy_solidity_contract(deploy_bytecode, get_solidity_contract):
    """
    Fixture to deploy a solidity contract in kakarot. The returned contract is a modified
    web3.contract instance with an added `contract_account` attribute that return the actual
    underlying kakarot contract account.
    """

    async def _factory(contract_app, contract_name, *args, **kwargs):
        """
        This factory is what is actually returned by pytest when requesting the `deploy_solidity_contract`
        fixture.
        It creates a web3.contract based on the basename of the target solidity file.
        This contract is deployed to kakarot using the deploy bytecode generated by web3.contract.
        Eventually, the web3.contract is updated such that each function (view or write) targets instead kakarot.

        The args and kwargs are passed as is to the web3.contract.constructor. Only the `caller_eoa` kwarg is
        is required and filtered out before calling the constructor.
        """
        contract = get_contract(contract_app, contract_name)
        caller_eoa = kwargs.pop("caller_eoa", None)
        evm_contract_address, starknet_contract_address, tx = await deploy_bytecode(
            contract.constructor(*args, **kwargs).data_in_transaction,
            caller_eoa,
        )
        return get_solidity_contract(
            contract_app,
            contract_name,
            starknet_contract_address,
            evm_contract_address,
            tx,
        )

    return _factory


@pytest.fixture(scope="package")
def create_account_with_bytecode(starknet, kakarot, deploy_bytecode, deploy_eoa):
    """
    Fixture to create a solidity contract in kakarot without running the bytecode.
    The given bytecode is directly stored into the account, similarly to what is done
    in a genesis config.

    Returns the corresponding starknet contract with the extra evm_contract_address attribute.
    """

    async def _factory(bytecode: str, caller_eoa=None):
        """
        This factory is what is actually returned by pytest when requesting the `create_account_with_bytecode`
        fixture.
        """
        if caller_eoa is None:
            caller_eoa = await deploy_eoa(
                generate_random_private_key(int(bytecode, 16))
            )

        evm_contract_address, starknet_contract_address, _ = await deploy_bytecode(
            "",
            caller_eoa,
        )
        contract_class = gather_deprecated_compiled_class(
            source="./src/kakarot/accounts/contract/contract_account.cairo",
            cairo_path=["src"],
            disable_hint_validation=True,
        )
        contract = StarknetContract(
            starknet.state,
            contract_class.abi,
            starknet_contract_address,
            None,
        )
        await contract.write_bytecode(hex_string_to_bytes_array(bytecode)).execute(
            caller_address=kakarot.contract_address
        )
        setattr(contract, "evm_contract_address", evm_contract_address)
        return contract

    return _factory
