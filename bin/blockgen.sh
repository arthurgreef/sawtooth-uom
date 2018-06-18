#!/bin/bash

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

#
# Quick generate of local genesis batch file.
#

info() {
    echo -e "\033[0;36m\n[--- $1 ---]\n\033[0m"
}

info 'Generating hashblock.batch genesis transaction file'

top_dir=$(cd $(dirname $(dirname $0)) && pwd)

docker run -it --rm \
	-v $top_dir/:/project/hashblock-exchange \
	-e "PYTHONPATH=/project/hashblock-exchange:/project/hashblock-exchange/apps" \
	-e "HASHBLOCK_KEYS=/project/hashblock-exchange/localkeys" \
	-e "HASHBLOCK_CONFIG=/project/hashblock-exchange/localconfig" \
	-e "GENESIS_BATCH=/project/hashblock-exchange/samplegenesis/hashblock.batch" \
	hashblock-dev-admin \
	bash -c "hbadm genesis -o \$GENESIS_BATCH"

