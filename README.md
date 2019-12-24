# intel-ipu3-pipecfg
## Usage:
1. Use following command to generate pipe config:
    `# python3 pipe_config.py input=3280x2464 main=1920x1080`
    `# python3 pipe_config.py input=3280x2464 main=1600x1200 vf=1280x960`

2. Use the following command to generate groups of pipe config, it will write
   the result into file 'result_xxx.csv' in same directory.
   For example:
   `# python3 pipe_config_group.py sensor.csv`

## Notes:
1. Do not specify vf value when you just want generate single stream
   pipe config
2. input resolution should be bigger than main output, main output should be
   bigger than vf output if have.
3. keep the order of parameters as $inpu $main $vf
