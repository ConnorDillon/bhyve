import subprocess
from .vm import VM, Disk, NIC
from .config import Config
from cmdtool import Superscript, Subscript, ToList


class Bhyvesh(Superscript):
    def __init__(self):
        super().__init__(name='bhyvesh',
                         description='A tool for managing bhyve VM\'s',
                         subscripts=[CreateOnce, DestroyOnce, Create, Destroy, CreateAll],
                         log_output='syslog',
                         log_format='bhyvesh: %(levelname)s: %(message)s')


class VMOps(Subscript):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_arg('-c', '--config', default='/usr/local/etc/bhyve.yaml')

    def load_config(self):
        return Config.open(self.args.config)

    def load_vm(self, name):
        return self.load_config().get(name)

    def create_vm(self, name):
        self.info('creating VM: '+name)
        vm = self.load_vm(name)
        for command in vm.create_nics() + vm.start_bootloader():
            self.sh(command)
        try:
            self.sh(vm.start_os())
        except subprocess.CalledProcessError as e:
            if not e.output.decode() == '' and e.returncode == 1:
                raise
            else:
                self.debug('VM stopped with exception: ' + str(e))
        finally:
            self.destroy_vm(name)

    def destroy_vm(self, name):
        self.info('destroying VM: '+name)
        for command in self.load_vm(name).destroy():
            self.sh(command)


class Create(VMOps):
    def __init__(self, superscript):
        super().__init__('create', superscript)
        self.add_arg('name')

    def script(self):
        self.create_vm(self.args.name)


class Destroy(VMOps):
    def __init__(self, superscript):
        super().__init__('destroy', superscript)
        self.add_arg('name')

    def script(self):
        self.destroy_vm(self.args.name)


class CreateAll(VMOps):
    def __init__(self, superscript):
        super().__init__('create_all', superscript)

    def script(self):
        for name in self.load_config().vms.keys():
            self.run_thread(self.create_vm, name)


class CreateOnce(Subscript):
    def __init__(self, superscript):
        super().__init__('create_once', superscript)
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


class DestroyOnce(Subscript):
    def __init__(self, superscript):
        super().__init__('destroy_once', superscript)
        self.add_arg('name')
        self.add_arg('-n', '--nic', dest='nics', action=ToList)

    def script(self):
        commands = [VM.destroy_once(self.args.name)]
        commands.extend(map(lambda x: NIC.destroy_once(x), self.args.nics))
        for command in commands:
            self.sh(command)
