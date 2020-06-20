[![pipeline status](https://salsa.debian.org/freedombox-team/freedom-maker/badges/master/pipeline.svg)](https://salsa.debian.org/freedombox-team/freedom-maker/commits/master)
[![Debian Unstable](https://badges.debian.net/badges/debian/unstable/freedom-maker/version.svg)](https://packages.debian.org/unstable/freedom-maker)
[![Debian Testing](https://badges.debian.net/badges/debian/testing/freedom-maker/version.svg)](https://packages.debian.org/testing/freedom-maker)

# Freedom-Maker: The FreedomBox image builder

These scripts build FreedomBox-images for various supported hardware
that can then be copied to SD card, USB stick or Hard Disk drive to
boot into FreedomBox.

These scripts are meant for developers of FreedomBox to build images
during releases and for advanced users who intend to build their own
images. Regular users who wish to turn their devices into
FreedomBoxes should instead download the pre-built images.

Get a pre-built image via https://freedombox.org/download/.  There
are images available for all supported target devices.  You also find
the setup instructions on the [Wiki](https://wiki.debian.org/FreedomBox/).

If you wish to create your own FreedomBox image, perhaps with some
tweaks, see the *Build Images* section below.

# Create Images

## Supported Targets

Freedom-maker supports building for the following targets:


- *a20-olinuxino-lime*: A20 OLinuXino Lime's SD card
- *a20-olinuxino-lime2*: A20 OLinuXino Lime2's SD card
- *a20-olinuxino-micro*: A20 OLinuXino MICRO's SD card
- *amd64*: Disk image for any machine with amd64 architecture
- *banana-pro*: Banana Pro's SD card
- *beaglebone*: BeagleBone Black's SD card
- *cubieboard2*: Cubieboard2's SD card
- *cubietruck*: Cubietruck's SD card
- *i386*: Disk image for any machine with i386 architecture
- *lamobo-r1*: Lamobo R1 aka BananaPi Router SD card
- *pcduino3*: pcDuino3's SD card
- *pine64-lts*: Pine64 LTS board's SD card
- *pine64-plus*: Pine64+ board's SD card
- *orange-pi-zero*: Orange Pi Zero's SD card
- *qemu-amd64*: 64-bit image for the Qemu virtualization tool
- *qemu-i386*: 32-bit image for the Qemu virtualization tool
- *raspberry2*: RasbperryPi 2's SD card
- *raspberry3*: RasbperryPi 3's SD card
- *raspberry3-b-plus*: RasbperryPi 3 Model B+'s SD card
- *test*: build virtualbox i386 image and run diagnostics tests on it
- *virtualbox-amd64*: 64-bit image for the VirtualBox virtualization tool
- *virtualbox-i386*: 32-bit image for the VirtualBox virtualization tool

## Running Build

1. Fetch the git source of freedom-maker:
    ```
    $ git clone https://salsa.debian.org/freedombox-team/freedom-maker.git
    ```

2. Install the required dependencies:
    ```shell
    $ sudo apt install btrfs-progs debootstrap kpartx parted qemu-user-static qemu-utils sshpass
    $ cd freedom-maker
    $ sudo apt build-dep .
    ```

3. Build images:

    This command has to be started with root (sudo) permission because it needs
    to run "parted".

    ```
    $ sudo python3 -m freedommaker a20-olinuxino-lime2
    ```
    Take a break from your computer - this takes some time. :)
    
    To see the full list of options read the help-page:
    ```
    $ python3 -m freedommaker --help
    ```

The image will show up in *build/*. Copy the image to the
target disk following the instructions in the *Use Images* section.

# Use Images

You'll need to copy the image to a memory card or USB stick. If you don't
use GNU/Linux or prefer a GUI we recommend [etcher](https://etcher.io/)
for this task. Otherwise follow the steps:

1. Figure out which device your card actually is.

    A. Unplug your card.

    B. Run "lsblk -p" to show which storage devices are connected to your system.

    C. Plug your card in and run "lsblk -p" again. Find the new device and note
    the name.
    
        $ lsblk -p
        NAME                                   MAJ:MIN RM   SIZE RO TYPE  MOUNTPOINT
        /dev/sdg                                 8:0    1  14.9G  0 disk  
        /dev/nvme0n1                           259:0    0   477G  0 disk  
        ├─/dev/nvme0n1p1                       259:1    0   512M  0 part  /boot/efi
        ├─/dev/nvme0n1p2                       259:2    0   244M  0 part  /boot
        └─/dev/nvme0n1p3                       259:3    0 476.2G  0 part  
          └─/dev/mapper/nvme0n1p3_crypt        253:0    0 476.2G  0 crypt 
            ├─/dev/mapper/mjw--t470--vg-root   253:1    0 468.4G  0 lvm   /
            └─/dev/mapper/mjw--t470--vg-swap_1 253:2    0   7.8G  0 lvm   [SWAP]

    D. In the above case, the disk that is newly inserted is available
       as */dev/sdg*. You can also verify the size (16 GB in this example).
       Carefully note this and use it in the copying step below.

2. Copy the image to your card.  Double check and make sure you don't
   write to your computer's main storage (such as /dev/sda).  Also
   make sure that you don't run this step as root (sudo) to avoid potentially
   overriding data on your hard drive due to a mistake. USB disks and SD
   cards inserted into the system should typically be write accessible
   to normal users. If you don't have permission to write to your SD
   card as a user, you may need to run this command as root. In this
   case triple check everything before you run the command. Another
   safety precaution is to unplug all external disks except the SD
   card before running the command.

   For example, if your SD card is /dev/sdg use the following command:
    ```
    $ xzcat build/freedombox-unstable_2018-08-06_beaglebone-armhf.img.xz | dd bs=4M of=/dev/sdg conv=fsync status=progress
    ```

   The above command is an example for the beaglebone image built on
   2018-08-06. Your image file name will be different.

   When picking a device, use the drive-letter destination, like
   /dev/sdf, not a numbered destination, like /dev/sdf1.  The device
   without a number refers to the entire device, while the device with
   anumber refers to a specific partition.  We want to use the whole
   device.  Downloaded images contain complete information about how
   many partitions there should be, their sizes and types. You don't
   have to format your SD card or create partitions. All the data on
   the SD card will be wiped off during the write process.

3. Use the image by inserting the SD card or USB disk into the target
   device and booting from it.  Also see hardware specific
   instructions on how to prepare your device at
   https://wiki.debian.org/FreedomBox/Hardware
