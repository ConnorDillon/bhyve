from .vm import VM, Disk, NIC
from .config import Config
from cmdtool import Superscript, Subscript, ToList


class Bhyvesh(Superscript):
    def __init__(self):
        super().__init__(name='bhyvesh',
                         description='A tool for managing bhyve VM\'s',
                         subscripts=[Create, Destroy, Start],
                         log_output='syslog',
                         log_format='bhyvesh: %(levelname)s: %(message)s')


class Start(Subscript):
    def __init__(self, superscript):
        super().__init__('start', superscript)
        self.add_arg('name')
        self.add_arg('-c', '--config', default='/usr/local/etc/bhyve.yaml')

    def script(self):
        config = Config.open(self.args.config)
        self.info('starting VM: '+self.args.name)
        for command in config.get(self.args.name).create():
            self.sh(command)


# doesn't work yet, needs threading
class StartAll(Subscript):
    def __init__(self, superscript):
        super().__init__('start_all', superscript)
        self.add_arg('-c', '--config', default='/usr/local/etc/bhyve.yaml')

    def script(self):
        config = Config.open(self.args.config)
        for name, vm in config.vms.items():
            self.info('starting VM: '+name)
            for command in vm.create():
                self.sh(command)


class Create(Subscript):
    def __init__(self, superscript):
        super().__init__('create', superscript)
        self.add_arg('name')
        self.add_arg('nmdm_id', type=int)
        self.add_arg('-c', '--cpus', default=1)
        self.add_arg('-m', '--memsize', default='256M')
        self.add_arg('-g', '--grubdir', default='/boot/grub')
        self.add_arg('-b', '--bootpart', default='gpt1')
        self.add_arg('-d', '--disk', dest='disks', action=ToList, nargs=2, required=True)
        self.add_arg('-n', '--nic', dest='nics', action=ToList, nargs=2, required=True)

    def script(self):
        self.params['disks'] = list(map(lambda x: Disk(*x), self.args.disks))
        self.params['nics'] = list(map(lambda x: NIC(*x), self.args.nics))
        params = self.params
        params.pop('command')
        self.info('creating VM: '+self.args.name)
        for command in VM(**params).create():
            self.sh(command)


class Destroy(Subscript):
    def __init__(self, superscript):
        super().__init__('destroy', superscript)
        self.add_arg('name')
        self.add_arg('-n', '--nic', dest='nics', action=ToList)

    def script(self):
        commands = [VM.destroy(self.args.name)]
        commands.extend(map(lambda x: NIC.destroy(x), self.args.nics))
        for command in commands:
            self.sh(command)