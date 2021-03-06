# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014 CERN.
#
# kwalitee is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# kwalitee is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kwalitee; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

import os
import shutil
import subprocess
import sys
import tempfile
from io import StringIO
from unittest import TestCase

import pytest
from click.testing import CliRunner
from hamcrest import assert_that, has_length, is_not

from kwalitee.cli.githooks import HOOK_PATH, install, uninstall


class GithookCliTest(TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.hooks = ('pre-commit', 'prepare-commit-msg', 'post-commit')
        self.path = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        self.stderr = sys.stderr
        sys.stderr = StringIO()
        os.chdir(self.path)

    def tearDown(self):
        os.chdir(self.cwd)
        sys.stderr = self.stderr
        shutil.rmtree(self.path)

    def call(self, *args):
        return subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.path
        ).wait()

    def test_install_hooks(self):
        precommit = os.path.join(HOOK_PATH, "pre-commit")
        self.call("git", "init")
        self.call("touch", precommit)

        result = self.runner.invoke(install)
        assert_that(result.exit_code == 0)

        for hook in self.hooks:
            filename = os.path.join(self.path, HOOK_PATH, hook)
            assert_that(os.path.exists(filename), filename)

        with open(precommit, "r") as f:
            assert_that(f.read(), has_length(0),
                        "precommit should be have been left as is")

        result = self.runner.invoke(uninstall)
        assert_that(result.exit_code == 0)

        for hook in self.hooks:
            filename = os.path.join(self.path, HOOK_PATH, hook)
            assert_that(not os.path.exists(filename), filename)

    def test_dont_install_in_non_git(self):
        result = self.runner.invoke(install)
        assert_that(result.exit_code != 0)

        for hook in self.hooks:
            filename = os.path.join(self.path, HOOK_PATH, hook)
            assert_that(not os.path.exists(filename), filename)

        result = self.runner.invoke(uninstall)
        assert_that(result.exit_code != 0)

    def test_install_hooks_and_overrides(self):
        precommit = os.path.join(HOOK_PATH, "pre-commit")
        self.call("git", "init")
        self.call("touch", precommit)

        result = self.runner.invoke(install, ['--force'])
        assert_that(result.exit_code == 0)

        for hook in self.hooks:
            filename = os.path.join(self.path, HOOK_PATH, hook)
            assert_that(os.path.exists(filename), filename)

        with open(precommit, "r") as f:
            assert_that(f.read(), is_not(has_length(0)),
                        "precommit should have been overridden")

        result = self.runner.invoke(uninstall)
        assert_that(result.exit_code == 0)

        for hook in self.hooks:
            filename = os.path.join(self.path, HOOK_PATH, hook)
            assert_that(not os.path.exists(filename), filename)
