
#!/usr/bin/env python

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

"""
setup.py file for hashblock_zksnark
"""
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class BuildExt(build_ext):
    def build_extensions(self):
        self.compiler.compiler_so.remove('-Wstrict-prototypes')
        self.compiler.compiler_so.append('-DCURVE_EDWARDS')
        self.compiler.compiler_so.append('-std=c++11')
        super(BuildExt, self).build_extensions()


zksnark_module = Extension(
    '_hashblock_zksnark',
    sources=['src/hashblock_zksnark.cxx', 'src/generate.cpp'])

setup(
    name='hashblock_zksnark',
    version='0.1.0',
    cmdclass={'build_ext': BuildExt},
    ext_modules=[zksnark_module],
    py_modules=["hashblock_zksnark"])
