from . import *
from .chroot import *
import shutil
import sys
import os

def usage():
	usage = """Deckian - Debian on a Steam Deck, easily.\nUsage:
	deckian bootstrap - Bootstrap a rootfs using debootstrap & chroot.
	deckain chroot - Chroots into the staging rootfs.
	deckian download [URL / official build name] - Downloads a prebuilt rootfs.
	deckian install-desktop [DE name] - Installs a desktop environment in the staging rootfs.
	deckian delete - Deletes the staging rootfs.
	deckian push [name] - Pushes the staging rootfs into the rootfs list.
	deckian pull [name] - Pulls a rootfs from the rootfs list into staging.
	deckian pop [name] - Deletes a rootfs in the rootfs list.
	deckian install [name] [device] - Installs a rootfs from the rootfs list.
	deckian show - Shows all chroot tarballs in the chroot list.\nOptions:
	deckian bootstrap:
		--mirror=http://example.com/debian - Sets the debian mirror URL.
		--skip-audio - Skip installation of the audio driver. This is usually not what you want.
	deckian push:
		--keep - Skips deletion of the staging rootfs.
	deckian pull:
		--keep - Skips deletion of the rootfs tarball in the rootfs list."""
	print(usage)

def main():
	if os.environ["USER"] != "root":
		error("Please run this script as root.")
		return
	
	# parse args
	
	if len(sys.argv) == 1:
		usage()
		return
	
	command_name = sys.argv[1]
	
	i = 2
	
	arguments = []
	options = {}
	
	while len(sys.argv) > i:
		if sys.argv[i].startswith("--"):
			if not "=" in sys.argv[i]:
				options[sys.argv[i][2:]] = True
				i += 1
				continue
			
			option = sys.argv[i][2:].split("=")
			key = option[0]
			value = option[1]
			
			if "," in value:
				options[key] = value.split(",")
				i += 1
				continue
			
			options[key] = value
			i += 1
			continue
		
		arguments.append(sys.argv[i])
		i += 1
	
	if command_name == "bootstrap":
		if "mirror" in options.keys():
			if "skip-audio" in options.keys():
				bootstrap(mirror=options["mirror"], install_audio_driver=False)
				return
			
			bootstrap(mirror=options["mirror"])
			return
		
		if "skip-audio" in options.keys():
			bootstrap(install_audio_driver=False)
			return
		
		bootstrap()
		return
	
	if command_name == "delete":
		if not os.path.isdir("data/staging"):
			error("Cannot delete the staging rootfs because it does not exist.")
			return
		
		log("Deleting staging rootfs...")
		shutil.rmtree("data/staging")
		log("Finished!")
		return
		
	if command_name == "chroot":
		if not os.path.isdir("data/staging"):
			error("Cannot chroot into the staging rootfs because it does not exist.")
			return
		
		c = Chroot("data/staging")
		c.run("bash")
		c.close()
		
		return
	
	if command_name == "install-desktop":
		if len(arguments) != 1:
			usage()
			return
		
		install_desktop_environment(arguments[0])
		return
		
	if command_name == "push":
		if len(arguments) != 1:
			usage()
			return
			
		if not os.path.isdir("data/staging"):
			error("Cannot push the staging rootfs because it does not exist.")
			return
		
		log("Pushing the staging rootfs onto the rootfs list...")
		
		if not os.path.isdir("data/list"):
			os.system("mkdir -p data/list")
		
		os.environ["NAME"] = arguments[0]
		os.system("cd data/staging; tar -czf ../list/${NAME}.tar.gz .; cd ../..")
		
		if not "keep" in options:
			shutil.rmtree("data/staging")
		
		log("Finished!")
		
		return
	
	if command_name == "pull":
		if len(arguments) != 1:
			usage()
			return
			
		if os.path.isdir("data/staging"):
			error("The staging rootfs already exists. Please push it or delete it first.")
			return
			
		if not os.path.isfile("data/list/" + arguments[0] + ".tar.gz"):
			error("Cannot find a rootfs with the name \"" + arguments[0] + "\"")
			return
			
		os.system("mkdir -p data/staging")
		
		log("Pulling the rootfs tarball into the staging rootfs...")
		
		os.environ["NAME"] = arguments[0]
		os.system("cd data/staging; tar -xf ../list/${NAME}.tar.gz; cd ../..")
		
		if not "keep" in options.keys():
			os.system("rm data/list/${NAME}.tar.gz")
		
		log("Finished!")
		
		return
	
	if command_name == "install":
		if len(arguments) != 2:
			usage()
			return
			
		if not os.path.isfile("data/list/" + arguments[0] + ".tar.gz"):
			error("Cannot find a rootfs with the name \"" + arguments[0] + "\"")
			return
		
		if "username" in options.keys():
			install(arguments[0], arguments[1], username=options["username"])
			return
			
		install(arguments[0], arguments[1])
		return
		
	if command_name == "recover":
		if len(arguments) != 1:
			usage()
			return
		
		d = Disk(arguments[0])
		d.open()
		d.open_chroot()
		d.chroot.run("bash")
		d.close()
		return
	
	usage()
	
	#print(command_name, arguments, options)

if __name__ == "__main__":
	main()
