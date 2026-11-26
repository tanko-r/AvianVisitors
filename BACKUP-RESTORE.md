# Pi backup and restore

The private backup is under `device-backups/pi-20261126/` in this checkout.
This directory is excluded from Git and accessible only to its owner/root.
It contains system credentials and personal recordings. Keep it private.

This is a file-based system backup, not a sector image of unused card space.
The planned bundle is:

| File | Purpose |
| --- | --- |
| `pi-rootfs.tar.zst` | Pi filesystem, ownership, permissions, ACLs and extended attributes |
| `boot-partition.img.gz` | Original FAT boot partition |
| `partition-table.sfdisk` | Original partition layout and disk identifier |
| `partition-table.json` | Machine-readable partition layout |
| `packages.tsv` | Installed package versions |
| `enabled-services.txt` | Enabled system/user services |
| `manifest.json` | Backup method, timestamps, source revision and verification status |
| `SHA256SUMS` | Checksums for the completed bundle |

The manifest is authoritative for whether capture and verification finished.
Files ending in `.partial` and filesystem staging directories are not a finished
backup. Temporary files, mounted runtime filesystems, caches and the swap file
are excluded. BirdNET recordings, the reference audio library, private settings,
SSH keys and service definitions are included in the filesystem backup.

## Verify before restoring

On the Linux development computer:

```sh
cd /home/david/Projects/avianvisitors/device-backups/pi-20261126
sha256sum --check SHA256SUMS
zstd --test pi-rootfs.tar.zst
gzip --test boot-partition.img.gz
```

Read `manifest.json` and check its recorded verification results. Filesystem
and archive checks do not replace booting a restored spare card; that physical
restore test remains required before treating the spare as ready to ship.

## Restore onto a replacement card using Linux

Use a USB card reader attached to a Linux computer. Do not run these commands
on the Pi's active system card. The original card is 63,281,561,600 bytes;
the replacement must be at least that size. A nominal 64 GB card can be smaller
than another brand's 64 GB card; a 128 GB card avoids that capacity ambiguity.

1. Disconnect other removable drives, insert the replacement, and inspect
   `lsblk -o NAME,SIZE,MODEL,MOUNTPOINTS`. Identify its **whole-disk** device.
   The examples below deliberately use `/dev/REPLACEMENT`, which must be replaced
   with the confirmed card reader device. Restoring erases that selected device.
2. Unmount any automatically mounted partitions on that replacement. Verify
   its capacity with `sudo blockdev --getsize64 /dev/REPLACEMENT`.
3. Recreate the saved partition table, then have the kernel reread it:

   ```sh
   sudo sfdisk /dev/REPLACEMENT < partition-table.sfdisk
   sudo partprobe /dev/REPLACEMENT
   lsblk /dev/REPLACEMENT
   ```

4. Identify its new first and second partition device paths. For example,
   `/dev/sdc1` and `/dev/sdc2` are partitions of `/dev/sdc`, while an MMC device
   uses names such as `/dev/mmcblk1p1`. Restore the FAT boot partition and create
   the root filesystem on the **second** partition:

   ```sh
   set -o pipefail
   gzip -dc boot-partition.img.gz | sudo dd of=/dev/BOOT_PARTITION bs=4M conv=fsync status=progress
   sudo mkfs.ext4 -L rootfs -U 02f61d5e-92cb-4f9c-a781-099d97795020 /dev/ROOT_PARTITION
   ```

5. Mount the new root partition and extract the filesystem as root, retaining
   ownership, ACLs and extended attributes. Mount its boot partition afterward:

   ```sh
   sudo mkdir -p /mnt/avian-restore
   sudo mount /dev/ROOT_PARTITION /mnt/avian-restore
   sudo tar --zstd --extract --file=pi-rootfs.tar.zst --directory=/mnt/avian-restore \
     --numeric-owner --same-owner --same-permissions --acls --xattrs --xattrs-include='*'
   sudo mkdir -p /mnt/avian-restore/boot/firmware
   sudo mount /dev/BOOT_PARTITION /mnt/avian-restore/boot/firmware
   ```

6. Check that `/mnt/avian-restore/etc/fstab` and the boot `cmdline.txt` still
   reference the saved partition identifiers. The saved table preserves disk ID
   `db4c4d27`, so the original `db4c4d27-01` and `db4c4d27-02` PARTUUIDs remain.
   Do not publish those configuration files or any restored private material.
7. Finish cleanly and check the unmounted root filesystem:

   ```sh
   sync
   sudo umount /mnt/avian-restore/boot/firmware
   sudo umount /mnt/avian-restore
   sudo e2fsck -f -n /dev/ROOT_PARTITION
   ```

8. With the Pi powered off, insert the restored card. Boot it with the USB
   microphone attached. Verify network/SSH access, new detections, dashboard,
   frame discovery, swipes and frame-speaker playback using
   [TABLET-SETUP.md](TABLET-SETUP.md). Keep the original card unchanged until
   this spare passes the physical test.

The larger card's extra space remains unused with the original partition table.
Expand the root partition/filesystem later only after a successful restore test.

## Scope and limits

Application services are paused for the final filesystem sync, then restarted.
This captures their databases and configuration without reading a changing raw
root filesystem. The operating system remains running for SSH; this is not an
atomic snapshot of every system log. The backup is intended for recovery of the
same Pi/station, preserving its existing identities and saved frame keys.

It does not contain the tablet's internal Android/eMMC backup, the operator
computer, or the Windows recovery computer. Those existing private backups
remain at the locations described in `PROJECT-HANDOFF.md`. A replacement tablet
needs its own provisioning; see [TABLET-SETUP.md](TABLET-SETUP.md).
