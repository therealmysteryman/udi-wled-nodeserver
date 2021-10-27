# udi-wled-nodeserver

This Poly provides an interface between WLED and Polyglot v2 server. Support control of one WLED Light per Node Server

*** This nodeserver has converted to run on PG3. The code has been moved to https://github.com/UniversalDevicesInc-PG3/udi-wled-nodeserver ***

#### Installation

Installation instructions
You can install from Polyglot V2 store or manually :

1. cd ~/.polyglot/nodeservers
2. git clone https://github.com/therealmysteryman/udi-wled-nodeserver.git
3. run ./install.sh to install the required dependency.
4. Create a custom variable named host -> ipaddress_of_wled
5. After the first run, I suggest you click on the Rebuild Profile of the WLED and restart the Admin Console. This will provide you with and updated list of Effect for your WLED.

#### Usage

This will create two nodes of for the Nanoleaf Controller and then one for the Aurora Light.

Support command are :
- Off / On 
- Brightness
- Effet
- Rebuild Effect List


Note : Everytime you Rebuild your effect list you need to restart ISY Admin Console for the change to take effect.

#### Source

1. Based on the Node Server Template - https://github.com/Einstein42/udi-poly-template-python
2. Library for controlling the WLED - https://github.com/pctechjon/wledpy
