from morefunctools import flatmap


class VM:
    def __init__(self, name, memsize, cpus, nmdm_id, bootpart, grubdir, nics, disks):
        self.name = name
        self.memsize = memsize
        self.cpus = cpus
        self.nmdm = '/dev/nmdm{}A'.format(nmdm_id)
        self.grubdir = grubdir
        self.nics = nics
        self.disks = disks
        self.devmap = '(hd0) ' + self.disks[0].zvol
        self.bootdev = 'hd0,' + bootpart

    def create_nics(self):
        return list(flatmap(lambda x: x.create(), self.nics))

    def start_bootloader(self):
        return ['echo "{devmap}" > /tmp/{name}-device.map'.format(**self.__dict__),
                'grub-bhyve -m /tmp/{name}-device.map -d {grubdir}'
                ' -r {bootdev} -M {memsize} {name}'.format(**self.__dict__),
                'rm /tmp/{name}-device.map'.format(**self.__dict__)]

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

    @staticmethod
    def destroy(name):
        return 'bhyvectl --destroy --vm='+name


class NIC:
    def __init__(self, name, bridge):
        self.name = name
        self.bridge = bridge

    def create(self):
        return ['ifconfig {} create'.format(self.name),
                'ifconfig {0} addm {1}'.format(self.bridge, self.name)]

    @staticmethod
    def destroy(name):
        return 'ifconfig {} destroy'.format(name)

    def as_option(self, slot):
        return '-s {0},virtio-net,{1}'.format(slot, self.name)


class Disk:
    def __init__(self, name, pool, size=None):
        self.name = name
        self.pool = pool
        self.size = size
        self.zvol = '/dev/zvol/{0}/{1}'.format(self.pool, self.name)

    def as_option(self, slot):
        return '-s {0},virtio-blk,{1}'.format(slot, self.zvol)