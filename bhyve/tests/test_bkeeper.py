import sys
from unittest import TestCase
from bhyve import BKeeper


class TestLog:
    def __init__(self):
        self.data = []

    def write(self, s):
        self.data.append(s)

    def flush(self):
        pass

    def __enter__(self):
        sys.stderr = self
        sys.stdout = self
        return self.data

    def __exit__(self, *_):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class TestBKeeper(TestCase):
    def setUp(self):
        self.config = '/tmp/test.yaml'
        self.vm_name = 'testvm'
        self.vm_nmdmid = 0
        self.vm_cpus = 4
        self.vm_memsize = '512M'
        self.vm_bootdir = '/grub'
        self.vm_bootpart = 'msdos1'
        self.vm_nic = 'tap0'
        self.vm_nic2 = 'tap1'
        self.vm_bridge = 'bridge0'
        self.vm_vol = self.vm_name + '-root'
        self.vm_vol2 = self.vm_name + '-data'
        self.vm_zpool = 'vmpool1'
        self.create_str = self.fmt('{vm_name} {vm_nmdmid} -c {vm_cpus} -m {vm_memsize} -g {vm_bootdir} -b {vm_bootpart}'
                                   ' -n {vm_nic} {vm_bridge} -n {vm_nic2} {vm_bridge} -d {vm_vol} {vm_zpool}'
                                   ' -d {vm_vol2} {vm_zpool}')
        self.clone_vm = 'clonevm'
        self.clone_vol = self.vm_vol.replace(self.vm_name, self.clone_vm)
        self.clone_vol2 = self.vm_vol2.replace(self.vm_name, self.clone_vm)

        self.create_expected = [
            'ifconfig {vm_nic} create',
            'ifconfig {vm_bridge} addm {vm_nic}',
            'ifconfig {vm_nic2} create',
            'ifconfig {vm_bridge} addm {vm_nic2}',
            'echo "(hd0) /dev/zvol/{vm_zpool}/{vm_vol}" > /tmp/{vm_name}-device.map',
            'grub-bhyve -m /tmp/{vm_name}-device.map -d {vm_bootdir} -r hd0,{vm_bootpart} -M {vm_memsize} {vm_name}',
            'rm /tmp/{vm_name}-device.map',
            'bhyve -A -I -H -P -c {vm_cpus} -m {vm_memsize} -l com1,/dev/nmdm{vm_nmdmid}A -s 0,hostbridge -s 1,lpc'
            ' -s 2,virtio-blk,/dev/zvol/{vm_zpool}/{vm_vol} -s 3,virtio-blk,/dev/zvol/{vm_zpool}/{vm_vol2}'
            ' -s 4,virtio-net,{vm_nic} -s 5,virtio-net,{vm_nic2} {vm_name}'
        ]

        self.destroy_expected = [
            'bhyvectl --destroy --vm={vm_name}',
            'ifconfig {vm_nic} destroy',
            'ifconfig {vm_nic2} destroy'
        ]

    def fmt(self, s):
        return s.format(**vars(self))

    def verify_create(self, log):
        expected = []
        for i in self.create_expected:
            expected.append(self.fmt(i))

        for i in expected:
            self.assertIn(i, log)

    def verify_destroy(self, log):
        expected = []
        for i in self.destroy_expected:
            expected.append(self.fmt(i))

        for i in expected:
            self.assertIn(i, log)

    def verify(self, log):
        self.verify_create(log)
        self.verify_destroy(log)

    def test_add(self):
        BKeeper()(self.fmt('add {create_str} --config {config} --console'))

    def test_create(self):
        with TestLog() as log:
            BKeeper()(self.fmt('create {vm_name} --testmode --config {config} --console'))
        self.verify(log)

    def test_destroy(self):
        with TestLog() as log:
            BKeeper()(self.fmt('destroy {vm_name} --testmode --config {config} --console'))
        self.verify_destroy(log)

    def test_create_once(self):
        with TestLog() as log:
            BKeeper()(self.fmt('create_once {create_str} --testmode --console'))
        self.verify_create(log)

    def test_destroy_once(self):
        with TestLog() as log:
            BKeeper()(self.fmt('destroy_once {vm_name} -n {vm_nic} -n {vm_nic2} --testmode --console'))
        self.verify_destroy(log)

    def test_clone(self):
        expected = [self.fmt('zfs snapshot {vm_zpool}/{vm_vol}@{clone_vol}'),
                    self.fmt('zfs clone {vm_zpool}/{vm_vol}@{clone_vol} {vm_zpool}/{clone_vol}')]
        with TestLog() as log:
            BKeeper()(self.fmt('clone {vm_name} {clone_vm} --config {config} --testmode --console'))
        for i in expected:
            self.assertIn(i, log)

    def test_remove(self):
        BKeeper()(self.fmt('remove {vm_name} --config {config} --console'))
        with open(self.config) as cfg:
            self.assertEqual(cfg.read(), '{}\n')
