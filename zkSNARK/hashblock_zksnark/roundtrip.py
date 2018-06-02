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

import subprocess

secret_str = "5,2,1,10,2,5,2,5,3,7,3,7"
data_str = "10,4,2,20,11,13,11,13,17,19,17,19"

key_gen = subprocess.run(
    ['build/hbzksnark', '-g', 'build/', secret_str],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if key_gen.returncode == 0:
    prf_gen = subprocess.run(
        ['build/hbzksnark', '-p', 'build/', data_str],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if prf_gen.returncode == 0:
        prf_str = prf_gen.stderr
        ver_gen = subprocess.run(
            ['build/hbzksnark', '-v', 'build/', prf_str, data_str],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ver_gen.returncode == 0:
            print("Church is a GOD!")
        else:
            print("Turing's fault {}".format(ver_gen))
    else:
        print("Turing's fault {}".format(prf_gen))
else:
    print("Turing's fault {}".format(key_gen))
