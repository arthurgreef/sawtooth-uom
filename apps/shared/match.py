# ------------------------------------------------------------------------------
# Copyright 2018 Frank V. Castellucci and Arthur Greef
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

"""match - Match business logic

This module is referenced when posting utxq and mtxq exchanges
"""
import os
import uuid

from shared.transactions import (
    submit_single_txn, create_transaction, compose_builder)

from modules.address import Address
from modules.hashblock_zksnark import zksnark_genproof
from modules.config import valid_signer
from modules.decode import decode_from_leaf, STATE_CRYPTO, get_utxq_obj_json
from modules.exceptions import RestException, DataException
from modules.exceptions import AssetNotExistException
from protobuf.match_pb2 import (
    MatchEvent, UTXQ, MTXQ, Quantity, Ratio)

KEYS_PATH = os.environ['HASHBLOCK_KEYS'] + '/'
_asset_addrs = Address(Address.FAMILY_ASSET, "0.1.0")
_utxq_addrs = Address(Address.FAMILY_MATCH, "0.2.0", Address.DIMENSION_UTXQ)
_mtxq_addrs = Address(Address.FAMILY_MATCH, "0.2.0", Address.DIMENSION_MTXQ)


_ACTION_MAP = {
    'ask': MatchEvent.UTXQ_ASK,
    'tell': MatchEvent.MTXQ_TELL,
    'offer': MatchEvent.UTXQ_OFFER,
    'accept': MatchEvent.MTXQ_ACCEPT,
    'commitment': MatchEvent.UTXQ_COMMITMENT,
    'obligation': MatchEvent.MTXQ_OBLIGATION,
    'give': MatchEvent.UTXQ_GIVE,
    'take': MatchEvent.MTXQ_TAKE}


def __validate_partners(plus, minus):
    """Validate the plus and minus are reachable keys"""
    valid_signer(plus)
    valid_signer(minus)
    print("Validated partners")


def __validate_assets(value, unit, resource):
    """Validate and return asset addresses that are reachable"""
    int(value)
    unit_add = _asset_addrs.asset_item(
        Address.DIMENSION_UNIT,
        unit['system'], unit['key'])
    resource_add = _asset_addrs.asset_item(
        Address.DIMENSION_RESOURCE,
        resource['system'], resource['key'])

    unit_res = decode_from_leaf(unit_add)
    resource_res = decode_from_leaf(resource_add)
    if not unit_res['data'] or not resource_res['data']:
        raise AssetNotExistException
    return (unit_res['data'], resource_res['data'])


def __get_and_validate_utxq(address):
    """Check that the utxq exists to recipricate on"""
    try:
        return get_utxq_obj_json(address)
    except RestException:
        raise DataException('Invalid initiate (utxq) address')


def __validate_utxq(request):
    """Validate the content for utxq"""
    __validate_partners(request["plus"], request["minus"])
    quantity_assets = __validate_assets(
        request['quantity']['value'],
        request['quantity']['unit'],
        request['quantity']['resource'])
    return (quantity_assets)


def __validate_mtxq(request):
    """Validate the content for mtxq"""
    utxq, json = __get_and_validate_utxq(request["utxq_address"])
    utxq_qblock = json['data']['quantity']
    quantity_assets = __validate_assets(
        request['quantity']['value'],
        request['quantity']['unit'],
        request['quantity']['resource'])
    numerator_assets = __validate_assets(
        request['ratio']['numerator']['value'],
        request['ratio']['numerator']['unit'],
        request['ratio']['numerator']['resource'])
    denominator_assets = __validate_assets(
        request['ratio']['denominator']['value'],
        request['ratio']['denominator']['unit'],
        request['ratio']['denominator']['resource'])
    data_tuple = []
    data_tuple.append(str(utxq_qblock['value']))
    data_tuple.append(request['ratio']['numerator']['value'])
    data_tuple.append(request['ratio']['denominator']['value'])
    data_tuple.append(request['quantity']['value'])
    data_tuple.append(str(utxq_qblock['valueUnit']))
    data_tuple.append(numerator_assets[0]['value'])
    data_tuple.append(denominator_assets[0]['value'])
    data_tuple.append(quantity_assets[0]['value'])
    data_tuple.append(str(utxq_qblock['resourceUnit']))
    data_tuple.append(numerator_assets[1]['value'])
    data_tuple.append(denominator_assets[1]['value'])
    data_tuple.append(quantity_assets[1]['value'])
    data_str = ",".join(data_tuple)
    print("Pairing tuple = {}".format(data_tuple))
    print("Pairing data_str = {}".format(data_str))
    prf_pair = zksnark_genproof(KEYS_PATH, data_str)
    return (
        utxq,
        request["utxq_address"],
        quantity_assets,
        numerator_assets,
        denominator_assets,
        prf_pair)


def __create_quantity(value, quantity):
    """Converts a quantity type into byte string from prime number"""
    unit_data, resource_data = quantity
    return Quantity(
        value=int(value).to_bytes(2, byteorder='little'),
        valueUnit=int(unit_data['value']).to_bytes(
            2, byteorder='little'),
        resourceUnit=int(resource_data['value']).to_bytes(
            2, byteorder='little'))


def __create_utxq(ingest):
    """Create a utxq object"""
    operation, quantity, data = ingest
    return (operation, data['plus'], UTXQ(
        matched=False,
        plus=valid_signer(data['plus']).encode(),
        minus=valid_signer(data['minus']).encode(),
        quantity=__create_quantity(data['quantity']['value'], quantity)))


def __create_initiate_payload(ingest):
    """Create the utxq payload"""
    operation, signer, data = ingest
    utxq_addr = _utxq_addrs.match2_initiate_unmatched(
        _utxq_addrs.dimension, operation, str(uuid.uuid4))
    encrypted = STATE_CRYPTO.encrypt(data.SerializeToString())
    return (operation, signer, MatchEvent(
        udata=encrypted,
        ukey=utxq_addr,
        action=_ACTION_MAP[operation]))


def __create_initiate_inputs_outputs(ingest):
    """Create utxq address (state) authorizations"""
    operation, signer, payload = ingest
    inputs = []
    outputs = [payload.ukey]
    return (
        signer, _utxq_addrs, {"inputs": inputs, "outputs": outputs}, payload)


def __create_mtxq(ingest):
    """Create the mtxq object"""
    operation, qassets, data = ingest
    utxq, uaddr, quantity, numerator, denominator, prf_pair = qassets
    # mtxq = MTXQ()
    maddr = _mtxq_addrs.set_utxq_matched(uaddr)
    return (operation, utxq, maddr, prf_pair, data, MTXQ(
        plus=valid_signer(data['plus']).encode(),
        minus=valid_signer(data['minus']).encode(),
        quantity=__create_quantity(data['quantity']['value'], quantity),
        ratio=Ratio(
            numerator=__create_quantity(
                data['ratio']['numerator']['value'], numerator),
            denominator=__create_quantity(
                data['ratio']['denominator']['value'], denominator)),
        utxq_addr=maddr.encode()))


def __create_reciprocate_payload(ingest):
    """Create the mtxq payload"""
    operation, utxq, maddr, prf_pair, request, payload = ingest
    proof, pairing = prf_pair
    return (operation, request['plus'], MatchEvent(
        action=_ACTION_MAP[operation],
        ukey=maddr,
        mkey=_mtxq_addrs.txq_item(
            _mtxq_addrs.dimension, operation, str(uuid.uuid4)),
        mdata=STATE_CRYPTO.encrypt(payload.SerializeToString()),
        udata=STATE_CRYPTO.encrypt(utxq.SerializeToString()),
        pairings=pairing.encode(),
        proof=proof.encode()))


def __create_reciprocate_inputs_outputs(ingest):
    """Create mtxq address (state) authorizations"""
    operation, signer, payload = ingest
    inputs = []
    outputs = [payload.ukey, payload.mkey]
    return (
        signer, _mtxq_addrs, {"inputs": inputs, "outputs": outputs}, payload)


def create_utxq(operation, request):
    """Create utxq transaction"""
    quant = __validate_utxq(request)
    # Creaate utxq
    # Create payload
    # Create inputs/outputs
    # Create transaction
    # Create batch
    utxq_build = compose_builder(
        submit_single_txn, create_transaction,
        __create_initiate_inputs_outputs, __create_initiate_payload,
        __create_utxq)
    utxq_build((operation, quant, request))


def create_mtxq(operation, request):
    """Create mtxq transaction"""
    qnd = __validate_mtxq(request)
    # Creaate mtxq
    # Create payload
    # Create inputs/outputs
    # Create transaction
    # Create batch
    mtxq_build = compose_builder(
        submit_single_txn, create_transaction,
        __create_reciprocate_inputs_outputs, __create_reciprocate_payload,
        __create_mtxq)
    mtxq_build((operation, qnd, request))
