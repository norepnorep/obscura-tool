# obscura-tool
all-in-one tool for sorting, labeling and decrypting legacy iOS applications

built for the [iPhoneOS Obscura Project](https://discord.gg/rTJ9zxjMu3)

## config
set the IP address, port and credentials of your devices' SSH server in config.cfg

## decrypting
to decrypt using the iOS 6 bypass method, you need to have a jailbroken device with the Activator, AppStoreFix and iTunesStoreX tweaks installed
your device must be attached to your computer via a USB cable that supports data transfer

## windows
to run on windows, you also need to put the [windows binaries for libimobiledevice](https://github.com/L1ghtmann/libimobiledevice/releases/) in the "libimobiledevice" folder, alongside all the DLLs

## examples

```python
python obscura-tool.py decrypt --input-path "C:/tons/of/encrypted/ipa/files/" --output-path "C:/Users/Me/Documents/IPAs/" --sort --delete --attempts 10
```
attempts to decrypt all IPA files in the input folder with the iOS 6 bypass 10 times and sorts them into the output folder using the iPhoneOS Obscura naming scheme.

```python
python obscura-tool.py decrypt --input-path "C:/tons/of/encrypted/ipa/files/" --output-path "C:/Users/Me/Documents/IPAs/" --sort --delete --no-bypass
```
attempts to decrypt all IPA files in the input folder with the iOS device's AppleID and sorts them into the output folder using the iPhoneOS Obscura naming scheme.

```python
python obscura-tool.py sort --input-path "C:/unsorted/random/ipa/files/" --output-path "C:/Users/Me/My Archive/"
```
sorts all IPA files in the input folder into the output folder using the iPhoneOS Obscura naming scheme.

---
this is a very early version of like 10 mini scripts i had for personal use rewritten and combined into one. please feel free to open issues if you find any bugs.