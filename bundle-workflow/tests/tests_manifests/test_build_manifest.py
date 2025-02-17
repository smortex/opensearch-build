# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import os
import unittest
from unittest.mock import mock_open, patch

import yaml

from manifests.build_manifest import BuildManifest


class TestBuildManifest(unittest.TestCase):
    def setUp(self):
        self.data_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "data")
        )
        self.manifest_filename = os.path.join(
            self.data_path, "opensearch-build-1.1.0.yml"
        )
        self.manifest = BuildManifest.from_path(self.manifest_filename)

    def test_build(self):
        self.assertEqual(self.manifest.version, "1.0")
        self.assertEqual(self.manifest.build.name, "OpenSearch")
        self.assertEqual(self.manifest.build.version, "1.1.0")
        self.assertEqual(len(self.manifest.components), 15)

    def test_component(self):
        opensearch_component = self.manifest.components[0]
        self.assertEqual(opensearch_component.name, "OpenSearch")
        self.assertEqual(
            opensearch_component.repository,
            "https://github.com/opensearch-project/OpenSearch.git",
        )
        self.assertEqual(
            opensearch_component.commit_id, "b7334f49d530ffd1a3f7bd0e5832b9b2a9caa583"
        )
        self.assertEqual(opensearch_component.ref, "1.x")
        self.assertEqual(
            sorted(opensearch_component.artifacts.keys()),
            ["bundle", "core-plugins", "maven"],
        )

    def test_to_dict(self):
        data = self.manifest.to_dict()
        with open(self.manifest_filename) as f:
            self.assertEqual(yaml.safe_load(f), data)

    def test_get_manifest_relative_location(self):
        actual = BuildManifest.get_build_manifest_relative_location(
            "25", "1.1.0", "x64"
        )
        expected = "builds/1.1.0/25/x64/manifest.yml"
        self.assertEqual(
            actual, expected, "the manifest relative location is not as expected"
        )

    @patch("manifests.build_manifest.S3Bucket")
    def test_from_s3(self, mock_s3_bucket):
        s3_bucket = mock_s3_bucket.return_value
        with patch("os.remove"):
            with patch("builtins.open", mock_open()):
                s3_download_path = BuildManifest.get_build_manifest_relative_location(
                    self.manifest.build.id,
                    self.manifest.build.version,
                    self.manifest.build.architecture,
                )
                with patch("manifests.build_manifest.BuildManifest.from_file"):
                    BuildManifest.from_s3(
                        "bucket_name",
                        self.manifest.build.id,
                        self.manifest.build.version,
                        self.manifest.build.architecture,
                        "/xyz",
                    )
                    self.assertEqual(s3_bucket.download_file.call_count, 1)
                    s3_bucket.download_file.assert_called_with(s3_download_path, "/xyz")
                    os.remove.assert_called_with("/xyz/manifest.yml")
