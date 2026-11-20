# AUR package

Files for the `five-finger-gestures` AUR package.

Publish or update it (needs an AUR account with your SSH key added):

```sh
git clone ssh://aur@aur.archlinux.org/five-finger-gestures.git aur-pkg
cp PKGBUILD five-finger-gestures.install aur-pkg/
cd aur-pkg
updpkgsums                         # fills sha256sums (pacman-contrib)
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD five-finger-gestures.install .SRCINFO
git commit -m "five-finger-gestures 1.0.0"
git push
```

For a new release: bump `pkgver`, reset `pkgrel=1`, and repeat from `cp`.
