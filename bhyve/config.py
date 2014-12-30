import os
import copy
from .utils import flatmap
from .serializable import Serializable
from .vm import VM


class Config(Serializable):
    def __init__(self, vms):
        self.vms = vms
        self.file = ''

    def add(self, vm):
        self.vms[vm.name] = vm
        return self

    def remove(self, vm_name):
        del self.vms[vm_name]
        return self

    def modify(self, vm):
        return self.add(vm)

    def get(self, vm_name):
        return self.vms[vm_name]

    def clone(self, source, name):
        vm = copy.deepcopy(self.get(source))

        vm.name = name
        vm.nmdm_id = self.new_nmdmid()
        tapid = self.new_tapid()

        for nic in vm.nics:
            nic.name = 'tap' + str(tapid)
            tapid += 1

        cmds = []
        for disk in vm.disks:
            new_name = disk.name.replace(source, name)
            for cmd in disk.clone(new_name):
                cmds.append(cmd)
            disk.name = new_name

        self.add(vm)
        return cmds

    def to_dict(self):
        dct = {}
        for k, v in self.vms.items():
            dct[k] = v.to_dict()
            del dct[k]['name']
        return dct

    @classmethod
    def from_dict(cls, dct):
        if dct is None:
            dct = {}
        vms = {}
        for k, v in dct.items():
            v['name'] = k
            vms[k] = VM.from_dict(v)
        return cls(vms)

    @classmethod
    def open(cls, config_file):
        if os.path.exists(config_file):
            with open(config_file) as cf:
                config = cls.load(cf.read())
        else:
            config = cls.from_dict({})

        config.file = config_file
        return config

    def save(self):
        assert self.file
        with open(self.file, 'w') as cf:
            cf.write(self.dump())

    def new_tapid(self):
        max_id = max(map(lambda x: int(x.name[3:]), flatmap(lambda x: x.nics, self.vms.values())))
        return max_id + 1

    def new_nmdmid(self):
        return max(vm.nmdm_id for vm in self.vms.values()) + 1