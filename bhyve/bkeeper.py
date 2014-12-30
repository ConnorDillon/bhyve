import subprocess
from .vm import VM, Disk, NIC
from .config import Config
from cmdtool import SuperCommand, SubCommand, ToList


class BKeeper(SuperCommand):
    def __init__(self):
        super().__init__(name='bkeeper',
                         description='A tool for managing bhyve VM\'s',
                         subscripts=[CreateOnce, DestroyOnce, Create, Destroy, CreateAll,
                                     Add, Remove, Clone, Snapshot],
                         log_fmt='bkeeper: %(levelname)s: %(message)s')


class ConfigOps(SubCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_arg('--config', default='/usr/local/etc/bhyve.yaml')

    def load_config(self):
        return Config.open(self.args.config)

    def save(self, config):
        if not self.testmode:
            config.save()
        else:
            self.debug(config.dump())


class VMOps(ConfigOps):

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
    def __init__(self, supercmd):
        super().__init__('create', supercmd)
        self.add_arg('name')

    def script(self):
        self.create_vm(self.args.name)


class Destroy(VMOps):
    def __init__(self, supercmd):
        super().__init__('destroy', supercmd)
        self.add_arg('name')

    def script(self):
        self.destroy_vm(self.args.name)


class CreateAll(VMOps):
    def __init__(self, supercmd):
        super().__init__('create_all', supercmd)

    def script(self):
        for name in self.load_config().vms.keys():
            self.run_thread(self.create_vm, name)


class VMCreation(SubCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_arg('name')
        self.add_arg('nmdm_id', type=int)
        self.add_arg('-c', '--cpus', type=int, default=1)
        self.add_arg('-m', '--memsize', default='256M')
        self.add_arg('-g', '--grubdir', default='/boot/grub')
        self.add_arg('-b', '--bootpart', default='gpt1')
        self.add_arg('-n', '--nic', dest='nics', action=ToList, nargs=2, required=True)
        self.add_arg('-d', '--disk', dest='disks', action=ToList, nargs=2, required=True)

    def get_vm(self):
        vm = {
            'name': self.args.name,
            'nmdm_id': self.args.nmdm_id,
            'cpus': self.args.cpus,
            'memsize': self.args.memsize,
            'grubdir': self.args.grubdir,
            'bootpart': self.args.bootpart,
            'nics': list(map(lambda x: NIC(*x), self.args.nics)),
            'disks': list(map(lambda x: Disk(*x), self.args.disks))
        }
        return VM(**vm)


class CreateOnce(VMCreation):
    def __init__(self, supercmd):
        super().__init__('create_once', supercmd)

    def script(self):
        vm = self.get_vm()
        self.info('creating VM: '+vm.name)
        for command in vm.create():
            self.sh(command)


class DestroyOnce(SubCommand):
    def __init__(self, supercmd):
        super().__init__('destroy_once', supercmd)
        self.add_arg('name')
        self.add_arg('-n', '--nic', dest='nics', action=ToList)

    def script(self):
        commands = [VM.destroy_once(self.args.name)]
        commands.extend(map(lambda x: NIC.destroy_once(x), self.args.nics))
        for command in commands:
            self.sh(command)


class Add(ConfigOps, VMCreation):
    def __init__(self, supercmd):
        super().__init__('add', supercmd)

    def script(self):
        vm = self.get_vm()
        config = self.load_config()
        config.add(vm)
        self.save(config)


class Remove(VMOps):
    def __init__(self, supercmd):
        super().__init__('remove', supercmd)
        self.add_arg('name')
        self.add_arg('--erase', action='store_true')

    def script(self):
        config = self.load_config()
        config.remove(self.args.name)
        self.save(config)

        if self.args.erase:
            vm = self.load_vm(self.args.name)
            for disk in vm.disks:
                self.sh(disk.destroy())


class Clone(ConfigOps):
    def __init__(self, supercmd):
        super().__init__('clone', supercmd)
        self.add_arg('source')
        self.add_arg('name')

    def script(self):
        config = self.load_config()
        for cmd in config.clone(self.args.source, self.args.name):
            self.sh(cmd)
        self.save(config)


class Snapshot(ConfigOps):
    def __init__(self, supercmd):
        super().__init__('snapshot', supercmd)
        self.add_arg('name')
        self.add_arg('snapshot')
        self.add_arg('-d', '--disk')

    def script(self):
        config = self.load_config()
        vm = config.get(self.args.name)
        if not self.args.disk:
            for cmd in [disk.snapshot(self.args.snapshot) for disk in vm.disks]:
                self.sh(cmd)
        else:
            try:
                disk = [d for d in vm.disks if d.name == self.args.disk][0]
            except IndexError:
                self.error('no disk with name: ' + self.args.disk)
            else:
                self.sh(disk.snapshot(self.args.snapshot))