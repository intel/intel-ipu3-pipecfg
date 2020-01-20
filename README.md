# intel-ipu3-pipecfg
## Usage:
1. Use following command to generate pipe config:

    `# python3 pipe_config.py input=3280x2464 main=1920x1080`

    `# python3 pipe_config.py input=3280x2464 main=1600x1200 vf=1280x960`

2. This tool also allow user to provide a group of input parameters in a file and
   it can generate group of configurations. The file sensor.csv is an example
   which list some common resolution configuration of a camera sensor. You can
   generate your file based on your camera sensor and use cases. Use the
   following command to generate groups of pipe config, it will write the result
   into file 'result_xxx.csv' in same directory.
   For example:

   `# python3 pipe_config_group.py sensor.csv`

## Notes:
1. Do not specify vf value when you just want generate single stream
   pipe config
2. input resolution should be bigger than main output, main output should be
   bigger than vf output if have.
3. keep the order of parameters as $inpu $main $vf
4. The main and vf output width should be multiple of 64, height should be
   multiple of 4
