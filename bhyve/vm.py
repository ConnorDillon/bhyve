from morefunctools import flatmap


class VM:
    def __init__(self, name, memsize, cpus, nmdm_id, grubdir, nics, disks):
        self.name = name
        self.memsize = memsize
        self.cpus = cpus
        self.nmdm = '/dev/nmdm{}A'.format(nmdm_id)
        self.grubdir = grubdir
        self.nics = nics
        self.disks = disks
        self.devmap = '(hd0) ' + self.disks[0].zvol
        self.bootpart = 'hd0,gpt1'

    def create(self):
        options = [
            '-A', '-I', '-H', '-P',
            '-c ' + str(self.cpus),
            '-m ' + self.memsize,
            '-l com1,' + self.nmdm,
            '-s 0:0,hostbridge',
            '-s 1:0,lpc'
        ]
        for idx, item in enumerate(self.disks + self.nics):
            options.append(item.as_option(idx+2))
        return list(flatmap(lambda x: x.create(), self.nics)) + ['bhyve {0} {1}'.format(' '.join(options), self.name)]


class NIC:
    def __init__(self, name, bridge):
        self.name = name
        self.bridge = bridge

    def create(self):
        return ['ifconfig {} create'.format(self.name),
                'ifconfig {0} addm {1}'.format(self.bridge, self.name)]

    def as_option(self, slot):
        return '-s {0}:0,virtio-net,{1}'.format(slot, self.name)


class Disk:
    def __init__(self, pool, name, size=None):
        self.name = name
        self.pool = pool
        self.size = size
        self.zvol = '/dev/zvol/{0}/{1}'.format(self.pool, self.name)

    def as_option(self, slot):
        return '-s {0}:0,virtio-blk,{1}'.format(slot, self.zvol)