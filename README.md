# openvoiceassistant-node
Node satelite for openvoiceassistant

Open Voice Assistant is a fully offline, locally hosted and completely customizable Voice Assistant.

# Deployment
OVA Node is designed to be deployed on small embeded computers such as Raspberry Pis, but can also be deployed on standard machines like PCs and Laptops. You can even deploy OVA Node alongside OVA Hub.

## Installation
openvoiceassistant-node is tested Raspberry Pi OS with **python >= 3.9**

It is recomended to setup [openvoiceassistant-hub](https://github.com/greerviau/openvoiceassistant-hub) first, before setting up any nodes.

### Raspberry Pi Install
First flash an instant of Raspberry Pi OS, or a similar Raspberry Pi certified distro. Recomended to use Raspberry Pi OS Lite in a headless configuration with SSH enabled.

Once OS is flashed, ssh to the device and run the following command:
```
sudo apt install git && \
sudo git clone https://github.com/greerviau/openvoiceassistant-node.git && \
cd openvoiceassistant-node && \
sudo ./scripts/install.sh
```

The installation will automatically create a systemd service.

The node should now be running! If you check your OVA Hub frontend you should see your node has been auto discovered. This can take a few minutes on initial install. If it takes longer than 5 minutes, check the status of the systemd service using ```sudo systemctl status ova_node.service```. 

On initial install, the node may show up with an ID name such as ```node_8917a474bc894ccd848780e6a8dfb988```. Use the ```Identify``` button to identify your node, it will announce "Hello World!" confirming which Node it is.

## Configuration
From the configuration page for a Node, there are several settings you can change.

* Name
* Area
* Wake Word
* Wake Word Confidence
* Wakeup Sound
* VAD Sensitivity
* VAD Threshold
* Speex Noise Supression
* Microphone
* Speaker
* Volume

### Name
It is recomended to give each Node a unique, human readable name.

### Area
This indicates the are of the house that the node is located. This is primarily utilized when OVA is interacting with external smart home platforms. 

For example if you are integrating with Home Assistant, use the same naming scheme you have set up for rooms within Home Assistant. This will allow OVA to control devices such as lights without the need to specify a location. 

Ex. If the Node is in the living room and you say "Lights off", it will turn off the lights in that room.

### Wake Word
This is the wake word that OVA Node will use to wakeup and listen to your command. There are some pretrained wake words provided for you to choose from.

If you want to customize your own, you can train your own by following the documentation on the [openWakeWord github](https://github.com/dscripka/openWakeWord?tab=readme-ov-file#training-new-models). You can then upload the ```.onnx``` file to the Node using the ```Upload Wake Word``` option in the dropdown.

### Wake Word Confidence
This is a percentage value from 0-100% that indicates how confident the wake word model must be that the wake word was spoken in order to activate. This setting works in conjunction with **VAD Threshold**. The default of 80% is usually fine, but if you notice more False Positives then raise it. If you're getting too many False Negatives then maybe lower it.

### Wakeup Sound
This indicates whether or not you want a sound to play when the wake word is detected. The sound acts as an indication that the Node heard you, and when you can start giving it a command.

### VAD Sensitivity
This is how aggressive the Voice Activity detection algorithm will be when determining if you are actively speaking and giving a command. The default of 3 is the maximum and rarely needs to be changed. **This option may end up being removed.**

### VAD Threshold
This is a percentage value from 0-100% that indicates how confident the VAD Detection model must be that you are speaking in order to start listening for the wake word. This setting works in conjunction with **Wake Word Confidence**. By default this is 0% meaning its deactivated, but if you notice you're getting a lot of False Positives then raise it. If you're getting too many False Negatives then maybe lower it or even disable it.

### Speex Noise Supression
This indicates whether or not you want to enable Speex Noise Supression. This setting is only available on linux based systems, including the RPI. If enabled it filters background noise, improving accuracy.

### Microphone & Speaker
These options allow you to choose the respective devices to use as Microphones and Speakers. Any new devices should be auto detected.

### Volume
This is the device volume. You can also adjust it through voice command. 

Ex. "Volume up/down", "Volume 5", "Volume 60 percent".