# Copyright 2014 - Rackspace Hosting.
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

from glanceclient import client as glanceclient
from heatclient import client as heatclient
from mistralclient.api import client as mistralclient
from neutronclient.neutron import client as neutronclient
from oslo.config import cfg
from swiftclient import client as swiftclient
from zaqarclient.queues.v1 import client as zaqarclient

from solum.common import exception
from solum.common import solum_barbicanclient
from solum.common import solum_keystoneclient
from solum.openstack.common.gettextutils import _
from solum.openstack.common import log as logging


LOG = logging.getLogger(__name__)


barbican_client_opts = [
    cfg.BoolOpt('insecure',
                default=False,
                help=_("If set, then the server's certificate for barbican "
                       "will not be verified.")),
    cfg.StrOpt('git_secrets_file',
               default='/etc/solum/secrets/git_secrets.db',
               help="Tells where to store the secrets of private git repo. "
                    "private git repo secrets location"),
    cfg.BoolOpt('barbican_disabled',
                default=True,
                help="Defaults to True. If barbican is disabled, it will "
                     "store secrets on the local filesystem specified "
                     "by 'git_secrets_file'")]

# Note: this config is duplicated in many projects that use OpenStack
# clients. This should really be in the client.
# There is a place holder bug here:
# https://bugs.launchpad.net/solum/+bug/1292334
# that we use to track this.
glance_client_opts = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help=_(
                   'Type of endpoint in Identity service catalog to use '
                   'for communication with the Glance service.'))]

heat_client_opts = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help=_(
                   'Type of endpoint in Identity service catalog to use '
                   'for communication with the OpenStack service.')),
    cfg.StrOpt('ca_file',
               help=_('Optional CA cert file to use in SSL connections.')),
    cfg.StrOpt('cert_file',
               help=_('Optional PEM-formatted certificate chain file.')),
    cfg.StrOpt('key_file',
               help=_('Optional PEM-formatted file that contains the '
                      'private key.')),
    cfg.BoolOpt('insecure',
                default=False,
                help=_("If set, then the server's certificate will not "
                       "be verified."))]

zaqar_client_opts = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help=_(
                   'Type of endpoint in Queue service catalog to use '
                   'for communication with the Zaqar service.')),
    cfg.BoolOpt('insecure',
                default=False,
                help=_("If set, then the server's certificate for zaqar "
                       "will not be verified."))]

neutron_client_opts = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help=_(
                   'Type of endpoint in Identity service catalog to use '
                   'for communication with the Neutron service.')),
    cfg.StrOpt('ca_cert',
               help=_('Optional CA bundle file to use in SSL connections.')),
    cfg.BoolOpt('insecure',
                default=False,
                help=_("If set, then the server's certificate for neutron "
                       "will not be verified."))]

swift_client_opts = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help=_(
                   'Type of endpoint in Identity service catalog to use '
                   'for communication with the Swift service.')),
    cfg.StrOpt('cacert',
               help=_('Optional CA cert file to use in SSL connections.')),
    cfg.BoolOpt('insecure',
                default=False,
                help=_("If set the server certificate will not be verified."))]

mistral_client_opts = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               help=_(
                   'Type of endpoint in Identity service catalog to use '
                   'for communication with the mistral service.')),
    cfg.StrOpt('cacert',
               help=_('Optional CA cert file to use in SSL connections '
                      'with Mistral.')),
    cfg.BoolOpt('insecure',
                default=False,
                help=_("If set the server certificate will not be verified "
                       "while using Mistral."))]

cfg.CONF.register_opts(barbican_client_opts, group='barbican_client')
cfg.CONF.register_opts(glance_client_opts, group='glance_client')
cfg.CONF.register_opts(heat_client_opts, group='heat_client')
cfg.CONF.register_opts(zaqar_client_opts, group='zaqar_client')
cfg.CONF.register_opts(neutron_client_opts, group='neutron_client')
cfg.CONF.register_opts(swift_client_opts, group='swift_client')
cfg.CONF.register_opts(mistral_client_opts, group='mistral_client')


class OpenStackClients(object):
    """Convenience class to create and cache client instances."""

    def __init__(self, context):
        self.context = context
        self._barbican = None
        self._keystone = None
        self._glance = None
        self._heat = None
        self._neutron = None
        self._swift = None
        self._zaqar = None
        self._mistral = None

    def url_for(self, **kwargs):
        return self.keystone().client.service_catalog.url_for(**kwargs)

    @property
    def auth_url(self):
        return self.keystone().v3_endpoint

    @property
    def auth_token(self):
        return self.context.auth_token or self.keystone().auth_token

    @exception.wrap_keystone_exception
    def barbican(self):
        if self._barbican:
            return self._barbican

        insecure = self._get_client_option('barbican', 'insecure')
        self._barbican = solum_barbicanclient.BarbicanClient(
            verify=not insecure)
        return self._barbican

    def keystone(self):
        if self._keystone:
            return self._keystone

        self._keystone = solum_keystoneclient.KeystoneClientV3(self.context)
        return self._keystone

    @exception.wrap_keystone_exception
    def zaqar(self):
        if self._zaqar:
            return self._zaqar

        endpoint_type = self._get_client_option('zaqar', 'endpoint_type')
        endpoint_url = self.url_for(service_type='queuing',
                                    endpoint_type=endpoint_type)
        conf = {'auth_opts':
                {'backend': 'keystone',
                 'options': {'os_auth_token': self.auth_token,
                             'os_auth_url': self.auth_url,
                             'insecure': self._get_client_option(
                                 'zaqar', 'insecure')}
                 }
                }
        self._zaqar = zaqarclient.Client(endpoint_url, conf=conf)
        return self._zaqar

    @exception.wrap_keystone_exception
    def neutron(self):
        if self._neutron:
            return self._neutron

        endpoint_type = self._get_client_option('neutron', 'endpoint_type')
        endpoint_url = self.url_for(service_type='network',
                                    endpoint_type=endpoint_type)
        args = {
            'auth_url': self.auth_url,
            'endpoint_url': endpoint_url,
            'token': self.auth_token,
            'username': None,
            'password': None,
            'insecure': self._get_client_option('neutron', 'insecure'),
            'ca_cert': self._get_client_option('neutron', 'ca_cert')
        }
        self._neutron = neutronclient.Client('2.0', **args)
        return self._neutron

    def _get_client_option(self, client, option):
        return getattr(getattr(cfg.CONF, '%s_client' % client), option)

    @exception.wrap_keystone_exception
    def glance(self):
        if self._glance:
            return self._glance

        args = {
            'token': self.auth_token,
        }
        endpoint_type = self._get_client_option('glance', 'endpoint_type')
        endpoint = self.url_for(service_type='image',
                                endpoint_type=endpoint_type)
        self._glance = glanceclient.Client('2', endpoint, **args)

        return self._glance

    @exception.wrap_keystone_exception
    def mistral(self):
        if self._mistral:
            return self._mistral

        args = {
            'auth_token': self.auth_token,
        }
        endpoint_type = self._get_client_option('mistral', 'endpoint_type')
        endpoint = self.url_for(service_type='workflow',
                                endpoint_type=endpoint_type)
        self._mistral = mistralclient.client(mistral_url=endpoint, **args)

        return self._mistral

    @exception.wrap_keystone_exception
    def heat(self):
        if self._heat:
            return self._heat

        endpoint_type = self._get_client_option('heat', 'endpoint_type')
        args = {
            'auth_url': self.auth_url,
            'token': self.auth_token,
            'username': None,
            'password': None,
            'ca_file': self._get_client_option('heat', 'ca_file'),
            'cert_file': self._get_client_option('heat', 'cert_file'),
            'key_file': self._get_client_option('heat', 'key_file'),
            'insecure': self._get_client_option('heat', 'insecure')
        }

        endpoint = self.url_for(service_type='orchestration',
                                endpoint_type=endpoint_type)
        self._heat = heatclient.Client('1', endpoint, **args)

        return self._heat

    @exception.wrap_keystone_exception
    def swift(self):
        if self._swift:
            return self._swift

        endpoint_type = self._get_client_option('swift', 'endpoint_type')
        args = {
            'auth_version': '2.0',
            'preauthtoken': self.auth_token,
            'preauthurl': self.url_for(service_type='object-store',
                                       endpoint_type=endpoint_type),
            'os_options': {'endpoint_type': endpoint_type},
            'cacert': self._get_client_option('swift', 'cacert'),
            'insecure': self._get_client_option('swift', 'insecure')
        }
        self._swift = swiftclient.Connection(**args)
        return self._swift
