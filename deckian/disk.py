from .chroot import *
import os

sfdisk_command = """sfdisk --force ${DISK_PATH} << END
size=64M,type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B,name="EFI system partition"
;
END"""

class Disk:
	def __init__(self, path):
		if not path.startswith("/dev"):
			raise Exception("Invalid disk path!")
		
		self.path = path
		self.chroot = None
		#self.open()
		
	def get_partition(self, partition):
		if self.path.startswith("/dev/mmcblk") or self.path.startswith("/dev/nvme") or self.path.startswith("/dev/loop") or self.path.startswith("/dev/nbd"):
			return self.path + "p" + str(partition)
		
		return self.path + str(partition)
		
	def create_partitions(self):
		os.environ["DISK_PATH"] = self.path
		os.environ["EFI_PARTITION"] = self.get_partition(1)
		os.environ["ROOT_PARTITION"] = self.get_partition(2)
		
		os.system("parted --script ${DISK_PATH} mklabel gpt")
		os.system(sfdisk_command)
		
		os.system("mkfs.msdos ${EFI_PARTITION}")
		os.system("mkfs.ext4 ${ROOT_PARTITION}")
		os.system("e2label ${ROOT_PARTITION} root")
	
	def open(self):
		os.environ["EFI_PARTITION"] = self.get_partition(1)
		os.environ["ROOT_PARTITION"] = self.get_partition(2)
		
		os.system("mkdir -p /mnt/deckian")
		os.system("mount ${ROOT_PARTITION} /mnt/deckian")
		os.system("mkdir -p /mnt/deckian/boot/efi")
		os.system("mount ${EFI_PARTITION} /mnt/deckian/boot/efi")
		
		self.open = True
		
		if self.chroot == None:
			return
		
		self.chroot.open()
		
	def open_chroot(self):
		self.chroot = Chroot("/mnt/deckian")
	
	def close(self):
		self.chroot.close()
		
		os.system("umount -f /mnt/deckian/boot/efi")
		os.system("rm -rf /mnt/deckian/boot/efi")
		os.system("umount -f /mnt/deckian")
		os.system("rm -rf /mnt/deckian")
		
		self.open = False
