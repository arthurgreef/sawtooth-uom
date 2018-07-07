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

import hashlib
import re
from abc import ABC, abstractmethod

from modules.exceptions import AssetIdRange


class Address(ABC):

    # hashblock Namespace
    NAMESPACE = "hashblock"

    # hashblock TP Families
    FAMILY_UNIT = "unit"
    FAMILY_ASSET = "asset"
    FAMILY_MATCH = "match"
    FAMILY_SETTING = "setting"

    # Dimensions, used by families
    MATCH_TYPE_UTXQ = "utxq"
    MATCH_TYPE_MTXQ = "mtxq"

    # Settings
    SETTING_AUTHKEYS = "authorized-keys"
    SETTING_APPTHRESH = "approval-threshold"

    # Proposals
    CANDIDATES = "candidates"

    # Well known hashes

    _namespace_hash = hashlib.sha512(
        NAMESPACE.encode("utf-8")).hexdigest()[0:6]

    _filler_hash26 = hashlib.sha512('filler'.encode("utf-8")).hexdigest()[0:52]
    _filler_hash23 = _filler_hash26[0:46]

    @classmethod
    def setting_addresser(cls):
        return SettingAddress()

    @classmethod
    def unit_addresser(cls):
        return UnitAddress()

    @classmethod
    def asset_addresser(cls):
        return AssetAddress()

    @classmethod
    def match_utxq_addresser(cls):
        return MatchUTXQAddress()

    @classmethod
    def match_mtxq_addresser(cls):
        return MatchMTXQAddress()

    @classmethod
    def valid_address(cls, address):
        if len(address) \
                and re.fullmatch(r"^[0-9a-fA-F]+$", address) \
                and len(address) % 2 == 0:
            return True
        else:
            return False

    @classmethod
    def valid_leaf_address(cls, address):
        return True if cls.valid_address(address) \
            and len(address) == 70 else False

    @classmethod
    def leaf_address_type(cls, target, address):
        return True if cls.valid_leaf_address(address) \
            and target == address[0:len(target)] else False

    @classmethod
    def hashup(cls, value):
        """Create a suitable hash from value"""
        return hashlib.sha512(value.encode("utf-8")).hexdigest()

    # E.g. hashblock.match.utxq
    # 0-2 namespace
    # 3-5 family
    # 6-8 mtype
    def txq_dimension(self, mtype):
        return self.ns_family \
            + self.hashup(mtype)[0:6]

    # E.g. hashblock.match.utxq.ask
    # 0-2 namespace
    # 3-5 family
    # 6-8 mtype
    # 9-11 ops
    def txq_list(self, mtype, ops):
        return self.txq_dimension(mtype) \
            + self.hashup(ops)[0:6]

    # E.g. hashblock.match.utxq.ask.ident
    # 0-2 namespace
    # 3-5 family
    # 6-8 mtype
    # 9-11 ops
    # 12-34 id
    def txq_item(self, mtype, ops, ident):
        """Create a specific match address based on mtype, operation and id
        """
        return self.txq_list(mtype, ops) \
            + self.hashup(ident)[0:46]

    def set_utxq_unmatched(self, address):
        laddr = list(address)
        laddr[24] = '0'
        return ''.join(laddr)

    def is_utxq_matched(self, address):
        return True if address[24] == '1' else False

    @property
    @abstractmethod
    def family(self):
        pass

    @property
    @abstractmethod
    def family_ns_name(self):
        pass

    @property
    @abstractmethod
    def family_ns_hash(self):
        pass

    @property
    @abstractmethod
    def family_hash(self):
        pass

    @property
    @abstractmethod
    def family_versions(self):
        pass

    @property
    @abstractmethod
    def family_current_version(self):
        pass

    @abstractmethod
    def is_family(self, address):
        pass


class BaseAddress(Address):
    """BaseAddress provides the fundemental address primatives for TPs"""

    def __init__(self, family, version_list):
        self._family = family
        self._versions = version_list
        self._family_hash = self.hashup(family)[0:6]
        self._reghash = self._namespace_hash + self._family_hash

    @property
    def family(self):
        return self._family

    @property
    def family_ns_name(self):
        return self.NAMESPACE + "_" + self.family

    @property
    def family_ns_hash(self):
        return self._reghash

    @property
    def family_hash(self):
        return self._family_hash

    @property
    def family_versions(self):
        return self._versions

    @property
    def family_current_version(self):
        return self.family_versions[0]

    def is_family(self, address):
        return self.family_ns_hash == address[0:6]


class SettingAddress(BaseAddress):
    """SettingAddress provides the setting TP address support

    Both Unit and Asset use internally as they are VotingAddress types
    """
    def __init__(self):
        super().__init__(self.FAMILY_SETTING, ["0.2.0"])

    # E.g. hashblock.setting.unit.authorized_keys
    # 0-2 namespace
    # 3-5 family
    # 6-8 stype (currenly 'unit' or 'asset')
    # 9-34 filler26
    def settings(self, stype):
        """Create the stype (asset/unit) settings address using key
        """
        return self.family_ns_hash \
            + self.hashup(stype)[0:6] \
            + self._filler_hash26


class VotingAddress(BaseAddress):
    """VotingAddress provides the setting and candidate addresses"""
    def __init__(self, family, version_list):
        super().__init__(family, version_list)
        self._setting_addy = Address.setting_addresser().settings(family)
        self._candidate_addy = self._namespace_hash \
            + self.hashup(self.CANDIDATES)[0:6] \
            + self.family_hash \
            + self._filler_hash26

    @property
    def setting_address(self):
        """For unit and asset, return settings address"""
        return self._setting_addy

    @property
    def candidate_address(self):
        """For unit and asset, return candidate address"""
        return self._candidate_addy

    def address_syskey(self, system, key):
        """Form an address prefix for unit/asset of system and key"""
        return self.family_ns_hash \
            + self.hashup(system)[0:8] \
            + self.hashup(key)[0:6]


class UnitAddress(VotingAddress):
    """UnitAddress provides the unit-of-measure TP address support"""
    def __init__(self):
        super().__init__(self.FAMILY_UNIT, ["0.3.0"])

    def unit_address(self, system, key, ident):
        if ident is None or len(ident) != 44:
            raise AssetIdRange(
                "Invalid ident {} for  {} {} {}"
                .format(ident, self._family, system, key))

        return self.address_syskey(system, key) + ident

    def element_address(self, system, key, ident):
        return self.unit_address(system, key, ident)


class AssetAddress(VotingAddress):
    """AssetAddress provides asset TP address support"""
    def __init__(self):
        super().__init__(self.FAMILY_ASSET, ["0.3.0"])

    def asset_address(self, system, key, ident):
        if ident is None or len(ident) != 44:
            raise AssetIdRange(
                "Invalid ident {} for  {} {} {}"
                .format(ident, self._family, system, key))

        return self.address_syskey(system, key) + ident

    def element_address(self, system, key, ident):
        return self.asset_address(system, key, ident)


class MatchAddress(BaseAddress):
    """MatchAddress is base for UTXQ/MTXQ address support"""
    def __init__(self, mtype):
        super().__init__(self.FAMILY_MATCH, ["0.3.0"])
        self._mtype = mtype
        self._mtype_address = self.family_ns_hash + \
            self.hashup(mtype)[0:6]

    @property
    def mtype(self):
        return self._mtype

    @property
    def mtype_address(self):
        return self._mtype_address

    def operation_address(self, operation):
        return self.mtype_address + self.hashup(operation)[0:6]


class MatchUTXQAddress(MatchAddress):
    """MatchUTXQAddress is concrete for UTXQ address support"""
    def __init__(self):
        super().__init__(self.MATCH_TYPE_UTXQ)

    def utxq_unmatched(self, operation, ident):
        return self.operation_address(operation) \
            + '0' + self.hashup(ident)[0:45]


class MatchMTXQAddress(MatchAddress):
    """MatchMTXQAddress is concrete for MTXQ address support"""
    def __init__(self):
        super().__init__(self.MATCH_TYPE_MTXQ)

    def set_utxq_matched(self, address):
        laddr = list(address)
        laddr[24] = '1'
        return ''.join(laddr)
