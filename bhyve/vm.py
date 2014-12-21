from .serializable import Serializable, load_from_key_value


class VM(Serializable):
    def __init__(self, name, memsize, cpus, nmdm_id, bootpart, grubdir, nics, disks):
        self.name = name
        self.memsize = memsize
        self.cpus = cpus
        self.nmdm_id = nmdm_id
        self.bootpart = bootpart
        self.grubdir = grubdir
        self.nics = nics
        self.disks = disks

        self.nmdm = '/dev/nmdm{}A'.format(self.nmdm_id)
        self.devmap = '(hd0) ' + self.disks[0].zvol
        self.bootdev = 'hd0,' + self.bootpart

    def create_nics(self):
        return list(flatmap(lambda x: x.create(), self.nics))

    def start_bootloader(self):
        return ['echo "{devmap}" > /tmp/{name}-device.map'.format(**vars(self)),
                'grub-bhyve -m /tmp/{name}-device.map -d {grubdir}'
                ' -r {bootdev} -M {memsize} {name}'.format(**vars(self)),
                'rm /tmp/{name}-device.map'.format(**vars(self))]

    def start_os(self):
        options = [
            '-A', '-I', '-H', '-P',
            '-c ' + str(self.cpus),
            '-m ' + self.memsize,
            '-l com1,' + self.nmdm,
            '-s 0,hostbridge',
            '-s 1,lpc'
        ]
        for idx, item in enumerate(self.disks + self.nics):
            options.append(item.as_option(idx + 2))

        return 'bhyve {0} {1}'.format(' '.join(options), self.name)

    def create(self):
        return self.create_nics() + self.start_bootloader() + [self.start_os()]

    def destroy(self):
        return ['bhyvectl --destroy --vm='+self.name] + list(map(lambda x: x.destroy(), self.nics))

    @staticmethod
    def destroy_once(name):
        return 'bhyvectl --destroy --vm='+name

    def to_dict(self):
        my_vars = dict(vars(self))
        del my_vars['nmdm']
        del my_vars['devmap']
        del my_vars['bootdev']
        my_vars['nics'] = list(map(lambda x: x.to_dict(), self.nics))
        my_vars['disks'] = list(map(lambda x: x.to_dict(), self.disks))
        return my_vars

    @classmethod
    def from_dict(cls, dct):
        dct['nics'] = list(map(lambda x: NIC.from_dict(x), dct['nics']))
        dct['disks'] = list(map(lambda x: Disk.from_dict(x), dct['disks']))
        return super().from_dict(dct)


class NIC(Serializable):
    def __init__(self, name, bridge):
        self.name = name
        self.bridge = bridge

    def create(self):
        return ['ifconfig {} create'.format(self.name),
                'ifconfig {0} addm {1}'.format(self.bridge, self.name)]

    def destroy(self):
        return 'ifconfig {} destroy'.format(self.name)

    @staticmethod
    def destroy_once(name):
        return 'ifconfig {} destroy'.format(name)

    def as_option(self, slot):
        return '-s {0},virtio-net,{1}'.format(slot, self.name)

    def to_dict(self):
        return {self.name: self.bridge}

    @classmethod
    def from_dict(cls, dct):
        return load_from_key_value(cls, dct)


class Disk(Serializable):
    def __init__(self, name, pool, size=None):
        self.name = name
        self.pool = pool
        self.size = size

        self.zvol = '/dev/zvol/{0}/{1}'.format(self.pool, self.name)

    def create(self):
        assert self.size
        return 'zfs create -V {size} {pool}/{name}'.format(**vars(self))

    def destroy(self):
        return 'zfs destroy {pool}/{name}'.format(**vars(self))

    def as_option(self, slot):
        return '-s {0},virtio-blk,{1}'.format(slot, self.zvol)

    def to_dict(self):
        return {self.name: self.pool}

    @classmethod
    def from_dict(cls, dct):
        return load_from_key_value(cls, dct)


def flatmap(fn, lst):
    return (y for x in map(fn, lst) for y in x)