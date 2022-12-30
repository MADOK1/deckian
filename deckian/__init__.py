from .chroot import *
from .data import *
from .disk import *
import shutil
import os

def log(info):
	print("[deckian]:", info)

def warn(info):
	print("[WARNING]:", info)

def error(info):
	print("[ERROR]:", info)
	
def write_file(filename, data):
	f = open(filename, "w")
	f.seek(0)
	f.write(data)
	f.close()

def bootstrap(release="bookworm", mirror="http://deb.debian.org/debian"):
	if os.path.isdir("data/staging"):
		error("Staging directory already exists! Please push your staging rootfs into the rootfs list or delete it first!")
		return
		
	os.environ["DEBIAN_FRONTEND"] = "noninteractive"
	os.environ["DEBCONF_NONINTERACTIVE_SEEN"] = "true"
		
	os.system("mkdir -p data/staging")
		
	log("Running debootstrap...")
	
	os.environ["DEBIAN_RELEASE"] = release
	os.environ["DEBIAN_MIRROR"] = mirror
	os.environ["ROOTFS"] = "data/staging"
	
	os.system("debootstrap ${DEBIAN_RELEASE} ${ROOTFS} ${DEBIAN_MIRROR}")
	
	log("Creating /etc/apt/sources.list...")
	
	os.system("echo \"deb ${DEBIAN_MIRROR} ${DEBIAN_RELEASE} main non-free\" > ${ROOTFS}/etc/apt/sources.list")
	
	log("Creating /etc/fstab...")
	
	write_file("data/staging/etc/fstab", fstab)
	
	log("Creating /bin/displayfix...")
	
	write_file("data/staging/bin/displayfix", displayfix)
	os.system("chmod +x ${ROOTFS}/bin/displayfix")
	
	log("Opening chroot...")
	
	c = Chroot("data/staging")
	
	log("Running apt-get update...")
	
	c.run("apt-get update")
	
	log("Installing kernel...")
	
	c.run("apt-get install linux-image-amd64 -y")
	
	log("Installing NetworkManager...")
	
	c.run("apt-get install network-manager network-manager-gnome -y")
	
	log("Installing drivers...")
	
	os.environ["PACKAGES"] = " ".join([xorg_packages, driver_packages, wireless_packages])
	
	c.run("apt-get install ${PACKAGES} -y")
	
	log("Installing browsers...")
	
	c.run("apt-get install firefox-esr chromium -y")
	
	log("Installing SDL2...")
	
	c.run("apt-get install libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-gfx-1.0-0 libsdl2-net-2.0-0 libsdl2-ttf-2.0-0 -y")
	
	log("Installing applications...")
	
	c.run("apt-get install pavucontrol neofetch ffmpeg vlc onboard python3-gi python3-gi-cairo libhidapi-dev -y")
	
	log("Installing GRUB...")
	
	c.run("apt-get install grub-common grub-efi-amd64-bin grub-efi-amd64-signed grub-efi-amd64 grub2-common -y")
	
	log("Running apt-get autoremove and apt-get clean...")
	
	c.run("apt-get autoremove --purge -y")
	c.run("apt-get clean")
	
	log("Closing chroot...")
	
	c.close()
	
	log("Finished!")
	
def install_desktop_environment(name):
	if not os.path.isdir("data/staging"):
		error("Cannot install desktop environment because the staging rootfs does not exist.")
		return
		
	if not name in ["gnome", "xfce", "plasma"]:
		error("Unknown desktop environment.")
		return
		
	if name == "gnome":
		warn("GNOME is currently broken on deckian.")
		
	os.environ["DEBIAN_FRONTEND"] = "noninteractive"
	os.environ["DEBCONF_NONINTERACTIVE_SEEN"] = "true"
	
	log("Opening chroot...")
	
	c = Chroot("data/staging")
	
	log("Installing desktop environment...")
	
	if name == "gnome":
		c.run("apt-get install gnome -y")
	elif name == "xfce":
		c.run("apt-get install xfce4 xfce4-terminal lightdm -y")
	elif name == "plasma":
		c.run("apt-get install kde-standard sddm kdeaccessibility orca k3b k3b-i18n plasma-nm apper qtvirtualkeyboard-plugin -y")
	
	log("Fixing desktop environment configuration...")
	
	if name == "gnome":
		warning("GNOME is currently broken on deckian, and I do not know a workaround for this problem. You will need to fix it yourself.")
		warning("If you know a way to fix GNOME crashing on deckian, please contact me.")
	elif name == "xfce":
		log("\tFixing /etc/lightdm/lightdm.conf...")
		
		write_file("data/staging/etc/lightdm/lightdm.conf", lightdm)
		
		log("\tFixing /etc/lightdm/lightdm-gtk-greeter.conf...")
		
		write_file("data/staging/etc/lightdm/lightdm-gtk-greeter.conf", lightdm_gtk_greeter)
	elif name == "plasma":
		log("\tFixing /usr/share/sddm/scripts/Xsetup...")
		
		write_file("data/staging/usr/share/sddm/scripts/Xsetup", xsetup)
		
	log("Closing chroot...")
	
	c.close()
	
	log("Finished!")
	
def install(name, path, username="user"):
	os.environ["DISK_PATH"] = path
	
	d = Disk(path)
	
	log("Creating partitions...")
	
	d.create_partitions()
	
	log("Opening disk...")
	
	d.open()
	
	log("Extracting rootfs tarball...")
	
	os.environ["ORIGINAL_PWD"] = os.getcwd()
	os.environ["ROOTFS_NAME"] = name
	
	os.system("cd /mnt/deckian; tar -xf ${ORIGINAL_PWD}/data/list/${ROOTFS_NAME}.tar.gz; cd ${ORIGINAL_PWD}")
	
	log("Opening chroot...")
	
	d.open_chroot()
	
	log("Changing root password...")
	
	d.chroot.run("echo \"root:password\" | chpasswd")
	
	log("Creating user...")
	
	os.environ["DECKIAN_USERNAME"] = username
	
	d.chroot.run("useradd ${DECKIAN_USERNAME} -m -s /bin/bash")
	d.chroot.run("passwd -d -l ${DECKIAN_USERNAME}")
	d.chroot.run("echo \"${DECKIAN_USERNAME}:password\" | chpasswd")
	
	log("Installing GRUB...")
	
	d.chroot.run("grub-install --target=x86_64-efi --removable ${DISK_PATH}")
	d.chroot.run("grub-install --recheck ${DISK_PATH}")
	d.chroot.run("update-grub")
	
	log("Closing disk...")
	
	d.close()
	
	log("Finished!")
