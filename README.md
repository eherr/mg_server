# Morphablegraphs State Machine Server

Stateful TCP/Websocket server for statistical motion synthesis based on [morphablegraphs](https://github.com/asr-dfki/morphablegraphs). 

The server can load a graph of motion models exported from the [motion modelling database](https://github.com/eherr/motion_database_server). 

## Setup Instructions

Install the base packages for [animation data editing](https://github.com/eherr/anim_utils), [visualization](https://github.com/eherr/vis_utils) and the [db interface](https://github.com/eherr/motion_db_interface) and [amorphablegraphs](https://github.com/asr-dfki/morphablegraphs) .

```bat

pip install git+https://github.com/eherr/anim_utils

pip install git+https://github.com/eherr/vis_utils

pip install git+https://github.com/eherr/motion_db_interface

pip install git+https://github.com/dfki-asr/morphablegraphs


pip install -r requirements.txt

```
## License
Copyright (c) 2019 DFKI GmbH.  
MIT License, see the LICENSE file.