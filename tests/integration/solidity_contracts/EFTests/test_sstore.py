import logging

import pytest
from starkware.starknet.testing.contract import StarknetContract

from tests.utils.helpers import hex_string_to_bytes_array

logger = logging.getLogger()


@pytest.mark.asyncio
@pytest.mark.EF_TEST
@pytest.mark.SSTORE
class TestSSTORE:
    async def test_InitCollision_d0g0v0_Shanghai(
        self,
        deploy_eoa,
        get_nonce,
        get_storage_at,
        set_storage_at,
        kakarot: StarknetContract,
    ):
        # Deploy EOA
        eoa = await deploy_eoa()
        # Set initial storage
        key = 0x01
        value = 0x01
        await set_storage_at(eoa.starknet_contract, key, value)

        storage_initial = await get_storage_at(eoa.starknet_contract, key)
        assert storage_initial == value

        # Send tx
        _ = await kakarot.eth_send_transaction(
            origin=int(eoa.address, 16),
            to=0,
            gas_limit=200_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array("0x6000600155600160015500"),
        ).execute(caller_address=eoa.starknet_address)

        # Check storage
        storage_final = await get_storage_at(eoa.starknet_contract, key)
        assert storage_final == storage_initial

        # Check nonce
        nonce = await get_nonce(eoa.starknet_contract)
        assert nonce == 1

    async def test_InitCollision_d1g0v0_Shanghai(
        self,
        deploy_eoa,
        get_nonce,
        get_storage_at,
        set_storage_at,
        kakarot: StarknetContract,
    ):
        # Deploy EOA
        eoa = await deploy_eoa()
        # Set initial storage
        key = 0x01
        value = 0x01
        await set_storage_at(eoa.starknet_contract, key, value)

        storage_initial = await get_storage_at(eoa.starknet_contract, key)
        assert storage_initial == value

        # Send tx
        _ = await kakarot.eth_send_transaction(
            origin=int(eoa.address, 16),
            to=0,
            gas_limit=200_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array(
                "0x6000600b80601360003960006000f5500000fe6000600155600160015500"
            ),
        ).execute(caller_address=eoa.starknet_address)

        # Check storage
        storage_final = await get_storage_at(eoa.starknet_contract, key)
        assert storage_final == 0x00

        # Check nonce
        nonce = await get_nonce(eoa.starknet_contract)
        assert nonce == 2

    async def test_InitCollision_d2g0v0_Shanghai(
        self,
        deploy_eoa,
        get_nonce,
        get_storage_at,
        set_storage_at,
        kakarot: StarknetContract,
    ):
        # Deploy EOA
        eoa = await deploy_eoa()
        # Set initial storage
        key = 0x01
        value = 0x01
        await set_storage_at(eoa.starknet_contract, key, value)

        storage_initial = await get_storage_at(eoa.starknet_contract, key)
        assert storage_initial == value

        # Send tx
        _ = await kakarot.eth_send_transaction(
            origin=int(eoa.address, 16),
            to=0,
            gas_limit=200_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array(
                "0x6000600b80601360003960006000f5500000fe6000600155600160015500"
            ),
        ).execute(caller_address=eoa.starknet_address)

        # Check storage
        storage_final = await get_storage_at(eoa.starknet_contract, key)
        assert storage_final == storage_initial

        # Check nonce
        nonce = await get_nonce(eoa.starknet_contract)
        assert nonce == 0

    async def test_InitCollision_d3g0v0_Shanghai(
        self,
        deploy_eoa,
        create_account_with_bytecode,
        get_nonce,
        get_storage_at,
        set_storage_at,
        kakarot: StarknetContract,
    ):
        # Deploy contract account
        called_contract = await create_account_with_bytecode(
            "0x6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"
        )

        # Deploy EOA
        eoa = await deploy_eoa()

        # Set initial storage
        key = 0x01
        value = 0x01
        await set_storage_at(eoa.starknet_contract, key, value)

        storage_initial = await get_storage_at(eoa.starknet_contract, key)
        assert storage_initial == value

        # Send tx
        _ = await kakarot.eth_send_transaction(
            origin=int(eoa.address, 16),
            to=0,
            gas_limit=200_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array(
                f"0x6000600b80603860003960006000f5506000600060006000600073{int(called_contract.evm_contract_address, 16)}62030d40f1500000fe6000600155600160015500"
            ),
        ).execute(caller_address=eoa.starknet_address)

        # Check storage
        storage_final = await get_storage_at(eoa.starknet_contract, key)
        assert storage_final == 0x00

        # Check nonce
        nonce = await get_nonce(eoa.starknet_contract)
        assert nonce == 2

    async def test_InitCollisionNonZeroNonce_d0g0v0_Shanghai(
        self,
        deploy_eoa,
        get_nonce,
        kakarot: StarknetContract,
    ):
        eoa = await deploy_eoa()
        nonce_before = await get_nonce(eoa.starknet_contract)

        _ = await kakarot.eth_send_transaction(
            origin=int(eoa.address, 16),
            to=0,
            gas_limit=200_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array("0x6000600155600160015500"),
        ).execute(caller_address=eoa.starknet_address)

        nonce_after = await get_nonce(eoa.starknet_contract)
        assert nonce_after - nonce_before == 1

    async def test_sstoreGas_d0g0v0_Shanghai(
        self,
        deploy_eoa,
        create_account_with_bytecode,
        get_nonce,
        get_storage_at,
        set_storage_at,
        kakarot: StarknetContract,
    ):
        # Deploy contract account
        called_contract = await create_account_with_bytecode(
            "0x6001600155600060015560016002556000600255600160035560006003556001600455600060045560016005556000600555600160065560006006556001600755600060075560016008556000600855600160095560006009556001600a556000600a556001600b556000600b556001600c556000600c556001600d556000600d556001600e556000600e556001600f556000600f5560016010556000601055600160015500"
        )

        # Deploy EOA
        eoa = await deploy_eoa()

        # Set initial storage
        key = 0x01
        value = 0x01
        await set_storage_at(eoa.starknet_contract, key, value)

        storage_initial = await get_storage_at(eoa.starknet_contract, key)
        assert storage_initial == value

        # Send tx
        _ = await kakarot.eth_send_transaction(
            origin=int(eoa.address, 16),
            to=0,
            gas_limit=200_000,
            gas_price=0,
            value=0,
            data=hex_string_to_bytes_array(
                f"0x6000600b80603860003960006000f5506000600060006000600073{int(called_contract.evm_contract_address, 16)}62030d40f1500000fe6000600155600160015500"
            ),
        ).execute(caller_address=eoa.starknet_address)

        # Check storage
        storage_final = await get_storage_at(eoa.starknet_contract, key)
        assert storage_final == 0x00

        # Check nonce
        nonce = await get_nonce(eoa.starknet_contract)
        assert nonce == 2
