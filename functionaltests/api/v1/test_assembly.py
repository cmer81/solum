# -*- coding: utf-8 -*-
#
# Copyright 2013 - Noorul Islam K M
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from tempest import exceptions as tempest_exceptions

from functionaltests.api import base

sample_data = {"name": "test_assembly",
               "description": "A test to create assembly",
               "project_id": "project_id",
               "user_id": "user_id",
               "status": "status",
               "application_uri": "http://localhost:5000"}

plan_sample_data = {"version": "1",
                    "name": "test_plan",
                    "description": "A test to create plan",
                    "project_id": "project_id",
                    "user_id": "user_id"}


class TestAssemblyController(base.TestCase):

    def setUp(self):
        super(TestAssemblyController, self).setUp()

    def tearDown(self):
        super(TestAssemblyController, self).tearDown()
        self.client.delete_created_assemblies()
        self.client.delete_created_plans()

    def _assert_output_expected(self, body_data, data):
        self.assertEqual(body_data['description'], data['description'])
        self.assertEqual(body_data['plan_uri'], data['plan_uri'])
        self.assertEqual(body_data['name'], data['name'])
        self.assertIsNotNone(body_data['uuid'])
        self.assertEqual(body_data['status'], data['status'])
        self.assertEqual(body_data['application_uri'], data['application_uri'])

    def test_assemblies_get_all(self):
        # Create assemblies to find
        p_resp_1 = self.client.create_plan()
        self.assertEqual(p_resp_1.status, 201)
        a_resp_1 = self.client.create_assembly(data=sample_data,
                                               plan_uuid=p_resp_1.uuid)
        self.assertEqual(a_resp_1.status, 201)

        p_resp_2 = self.client.create_plan()
        self.assertEqual(p_resp_2.status, 201)
        a_resp_2 = self.client.create_assembly(data=sample_data,
                                               plan_uuid=p_resp_2.uuid)
        self.assertEqual(a_resp_2.status, 201)

        # Get list of all assemblies
        resp, body = self.client.get('v1/assemblies')
        self.assertEqual(resp.status, 200)

        # Search for uuids of created assemblies
        assembly_list = json.loads(body)
        found_uuid_1 = False
        found_uuid_2 = False
        for assembly in assembly_list:
            uuid = json.dumps(assembly['uuid'])
            if a_resp_1.uuid in uuid:
                found_uuid_1 = True
            elif a_resp_2.uuid in uuid:
                found_uuid_2 = True

        self.assertTrue(found_uuid_1,
                        'Cannot find assembly [%s] in list of all assemblies.'
                        % a_resp_1.uuid)
        self.assertTrue(found_uuid_2,
                        'Cannot find assembly [%s] in list of all assemblies.'
                        % a_resp_2.uuid)

    def test_assemblies_create(self):
        plan_resp = self.client.create_plan()
        self.assertEqual(plan_resp.status, 201)
        assembly_resp = self.client.create_assembly(
            plan_uuid=plan_resp.uuid,
            data=sample_data)
        self.assertEqual(assembly_resp.status, 201)
        sample_data['plan_uri'] = "%s/v1/plans/%s" % (self.client.base_url,
                                                      plan_resp.uuid)
        self._assert_output_expected(assembly_resp.data, sample_data)

    def test_assemblies_create_none(self):
        self.assertRaises(tempest_exceptions.BadRequest,
                          self.client.post, 'v1/assemblies', "{}")

    def test_assemblies_get(self):
        plan_resp = self.client.create_plan(data=plan_sample_data)
        self.assertEqual(plan_resp.status, 201)
        plan_uuid = plan_resp.uuid
        assembly_resp = self.client.create_assembly(
            plan_uuid=plan_uuid,
            data=sample_data)
        self.assertEqual(assembly_resp.status, 201)
        uuid = assembly_resp.uuid
        sample_data['plan_uri'] = "%s/v1/plans/%s" % (self.client.base_url,
                                                      plan_uuid)
        resp, body = self.client.get('v1/assemblies/%s' % uuid)
        self.assertEqual(resp.status, 200)
        json_data = json.loads(body)
        self._assert_output_expected(json_data, sample_data)

    def test_assemblies_get_not_found(self):
        self.assertRaises(tempest_exceptions.NotFound,
                          self.client.get, 'v1/assemblies/not_found')

    def test_assemblies_put(self):
        plan_resp = self.client.create_plan()
        self.assertEqual(plan_resp.status, 201)
        plan_uuid = plan_resp.uuid
        assembly_resp = self.client.create_assembly(
            plan_uuid=plan_uuid,
            data=sample_data)
        self.assertEqual(assembly_resp.status, 201)
        uuid = assembly_resp.uuid
        uri = "%s/v1/plans/%s" % (self.client.base_url, plan_uuid)
        updated_data = {"name": "test_assembly_updated",
                        "description": "A test to create assembly updated",
                        "plan_uri": uri,
                        "project_id": "project_id updated",
                        "user_id": "user_id updated",
                        "status": "new_status",
                        "application_uri": "new_uri"}
        updated_json = json.dumps(updated_data)
        resp, body = self.client.put('v1/assemblies/%s' % uuid, updated_json)
        self.assertEqual(resp.status, 200)
        json_data = json.loads(body)
        self._assert_output_expected(json_data, updated_data)

    def test_assemblies_put_not_found(self):
        updated_data = {"name": "test_assembly_updated",
                        "description": "A test to create assembly updated",
                        "plan_uri": 'fake_uri',
                        "project_id": "project_id updated",
                        "user_id": "user_id updated",
                        "status": "new_status",
                        "application_uri": "new_uri"}
        updated_json = json.dumps(updated_data)
        self.assertRaises(tempest_exceptions.NotFound,
                          self.client.put, 'v1/assemblies/not_found',
                          updated_json)

    def test_assemblies_put_none(self):
        self.assertRaises(tempest_exceptions.BadRequest,
                          self.client.put, 'v1/assemblies/any', "{}")

    def test_assemblies_delete(self):
        plan_resp = self.client.create_plan()
        self.assertEqual(plan_resp.status, 201)
        assembly_resp = self.client.create_assembly(
            plan_uuid=plan_resp.uuid,
            data=sample_data)
        self.assertEqual(assembly_resp.status, 201)
        uuid = assembly_resp.uuid

        resp, body = self.client.delete_assembly(uuid)
        self.assertEqual(resp.status, 204)
        self.assertEqual(body, '')
        self.assertTrue(self.client.assembly_delete_done(uuid),
                        "Assembly couldn't be deleted.")

    def test_assemblies_delete_not_found(self):
        self.assertRaises(tempest_exceptions.NotFound,
                          self.client.delete, 'v1/assemblies/not_found')
