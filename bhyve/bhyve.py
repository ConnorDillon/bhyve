import cmdtool
from . import vm


class Bhyve(cmdtool.Superscript):
    def __init__(self):
        super().__init__(name='bhyvesh',
                         description='A tool for managing bhyve VM\'s',
                         subscripts=[Create])


class Create(cmdtool.Subscript):
    def __init__(self, superscript):
        super().__init__('create', superscript, testmode=True)
        self.add_arg('name')
        self.add_arg('nmdm_id', type=int)
        self.add_arg('-c', '--cpus', default=1)
        self.add_arg('-m', '--memsize', default='256M')
        self.add_arg('-g', '--grubdir', default='/boot/grub')
        self.add_arg('-d', '--disk', dest='disks', action=cmdtool.ToList, nargs=2, required=True)
        self.add_arg('-n', '--nic', dest='nics', action=cmdtool.ToList, nargs=2, required=True)

    def script(self):
        self.params['disks'] = list(map(lambda x: vm.Disk(*x), self.args.disks))
        self.params['nics'] = list(map(lambda x: vm.NIC(*x), self.args.nics))
        params = self.params
        params.pop('command')
        for command in vm.VM(**params).create():
            self.sh(command)