import asyncio
from grpc import RpcError
from pyinjective.async_client import AsyncClient
from pyinjective.constant import GAS_FEE_BUFFER_AMOUNT, GAS_PRICE
from pyinjective.core.network import Network
from pyinjective.transaction import Transaction
from pyinjective.wallet import PrivateKey
import nest_asyncio
from datetime import date, timedelta, datetime

# 👇️ call apply()
nest_asyncio.apply()

#######
async def main() -> None:
    # select network: local, testnet, mainnet
    network = Network.testnet()##############################################################################################change here for mainnet

    # initialize grpc client
    client = AsyncClient(network)
    composer = await client.composer()
    await client.sync_timeout_height()

    address = "inj1y3eq6jrt2w4yp0s2tldd3dnk3qfny7vzpz0ch5"

    while True:
        spendable_balances = await client.fetch_bank_balances(address=address)
        inj_balance = next((spendable_balances['amount'] for spendable_balances in spendable_balances['balances'] if spendable_balances['denom'] == 'inj'), None)
        time = datetime.now()
        
        #Printing Current time and wallet balance
        print(time, inj_balance)        
      
        if inj_balance != "5931997040462196808": #################################################################PLEASE CHANGE HERE FOR THE ACTUAL MAINNET BALANCE
            print("SENDING to MY WALLET")
            priv_key = PrivateKey.from_mnemonic("xxx xxx xxx xxx xxx")
            pub_key = priv_key.to_public_key()
            address = pub_key.to_address()
            await client.fetch_account(address.to_acc_bech32())

            # prepare tx msg
            msg = composer.MsgSend(
                from_address=address.to_acc_bech32(),
                to_address="inj1z08em4ku0ms9d82ak8u65glesyr937uxh2vcsf",
                amount=9,
                denom="INJ",
            )

            # build sim tx
            tx = (
                Transaction()
                .with_messages(msg)
                .with_sequence(client.get_sequence())
                .with_account_num(client.get_number())
                .with_chain_id(network.chain_id)
            )
            sim_sign_doc = tx.get_sign_doc(pub_key)
            sim_sig = priv_key.sign(sim_sign_doc.SerializeToString())
            sim_tx_raw_bytes = tx.get_tx_data(sim_sig, pub_key)

            # simulate tx
            try:
                sim_res = await client.simulate(sim_tx_raw_bytes)
            except RpcError as ex:
                print(ex)
                return

            # build tx
            gas_price = GAS_PRICE
            gas_limit = int(sim_res["gasInfo"]["gasUsed"]) + GAS_FEE_BUFFER_AMOUNT  # add buffer for gas fee computation
            gas_fee = "{:.18f}".format((gas_price * gas_limit) / pow(10, 18)).rstrip("0")
            fee = [
                composer.Coin(
                    amount=gas_price * gas_limit,
                    denom=network.fee_denom,
                )
            ]
            tx = tx.with_gas(gas_limit).with_fee(fee).with_memo("").with_timeout_height(client.timeout_height)
            sign_doc = tx.get_sign_doc(pub_key)
            sig = priv_key.sign(sign_doc.SerializeToString())
            tx_raw_bytes = tx.get_tx_data(sig, pub_key)

            # broadcast tx: send_tx_async_mode, send_tx_sync_mode, send_tx_block_mode
            res = await client.broadcast_tx_sync_mode(tx_raw_bytes)
            print(res)
            print("gas wanted: {}".format(gas_limit))
            print("gas fee: {} INJ".format(gas_fee))
            break


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
