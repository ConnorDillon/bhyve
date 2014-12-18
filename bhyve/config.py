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
        self.add(vm)
        return self

    def get(self, vm_name):
        return self.vms[vm_name]

    def to_dict(self):
        dct = {}
        for k, v in self.vms.items():
            dct[k] = v.to_dict()
            del dct[k]['name']
        return dct

    @classmethod
    def from_dict(cls, dct):
        vms = {}
        for k, v in dct.items():
            v['name'] = k
            vms[k] = VM.from_dict(v)
        return cls(vms)

    @classmethod
    def open(cls, config_file):
        with open(config_file) as cf:
            config = cls.load(cf.read())
            config.file = config_file
            return config

    def save(self):
        assert self.file
        with open(self.file, 'w') as cf:
            cf.write(self.dump())