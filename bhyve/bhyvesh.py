import cmdtool
from . import vm


class Bhyvesh(cmdtool.Superscript):
    def __init__(self):
        super().__init__(name='bhyvesh',
                         description='A tool for managing bhyve VM\'s',
                         subscripts=[Create, Destroy],
                         log_output='syslog',
                         log_format='bhyvesh: %(levelname)s: %(message)s')


class Create(cmdtool.Subscript):
    def __init__(self, superscript):
        super().__init__('create', superscript)
        self.add_arg('name')
        self.add_arg('nmdm_id', type=int)
        self.add_arg('-c', '--cpus', default=1)
        self.add_arg('-m', '--memsize', default='256M')
        self.add_arg('-g', '--grubdir', default='/boot/grub')
        self.add_arg('-b', '--bootpart', default='gpt1')
        self.add_arg('-d', '--disk', dest='disks', action=cmdtool.ToList, nargs=2, required=True)
        self.add_arg('-n', '--nic', dest='nics', action=cmdtool.ToList, nargs=2, required=True)

    def script(self):
        self.params['disks'] = list(map(lambda x: vm.Disk(*x), self.args.disks))
        self.params['nics'] = list(map(lambda x: vm.NIC(*x), self.args.nics))
        params = self.params
        params.pop('command')
        self.info('creating VM: '+self.args.name)
        for command in vm.VM(**params).create():
            print('executing command: ' + command)
            self.sh(command)


class Destroy(cmdtool.Subscript):
    def __init__(self, superscript):
        super().__init__('destroy', superscript)
        self.add_arg('name')
        self.add_arg('-n', '--nic', dest='nics', action=cmdtool.ToList)

    def script(self):
        commands = [vm.VM.destroy(self.args.name)]
        commands.extend(map(lambda x: vm.NIC.destroy(x), self.args.nics))
        for command in commands:
            self.sh(command)