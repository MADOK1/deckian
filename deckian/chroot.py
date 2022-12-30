import os

class Chroot:
	def __init__(self, path):
		self.path = path
		self.open()
	
	def open(self):
		os.environ["ROOTFS"] = self.path
		os.system("mkdir -p ${ROOTFS}/proc")
		os.system("mkdir -p ${ROOTFS}/sys")
		os.system("mkdir -p ${ROOTFS}/dev")
		os.system("mkdir -p ${ROOTFS}/dev/pts")
		os.system("mkdir -p ${ROOTFS}/dev/shm")
		
		os.system("mount -t proc none ${ROOTFS}/proc")
		os.system("mount -t sysfs none ${ROOTFS}/sys")
		os.system("mount -o bind /dev ${ROOTFS}/dev")
		os.system("mount -o bind /dev/pts ${ROOTFS}/dev/pts")
		os.system("mount -o bind /dev/shm ${ROOTFS}/dev/shm")
		self.open = True
	
	def close(self):
		os.system("umount -f ${ROOTFS}/proc")
		os.system("umount -f ${ROOTFS}/sys")
		os.system("umount -f ${ROOTFS}/dev/pts")
		os.system("umount -f ${ROOTFS}/dev/shm")
		os.system("umount -f ${ROOTFS}/dev")
		#os.system("umount ${ROOTFS}/proc")
		#os.system("umount ${ROOTFS}/sys")
		#os.system("umount ${ROOTFS}/dev/pts")
		#os.system("umount ${ROOTFS}/dev/shm")
		#os.system("umount ${ROOTFS}/dev")
		self.open = False
		
	def run(self, command):
		if not self.open:
			raise Exception("Chroot is not open!")
		
		os.environ["ROOTFS"] = self.path
		os.environ["CHROOT_COMMAND"] = command
		os.system("chroot ${ROOTFS} bash -c \"${CHROOT_COMMAND}\"")
