# pbs-workbench

Start a PBS job that runs idle to ssh into and work interactively. 

## Installation

[Install pipx](https://pipx.pypa.io/stable/how-to/install-pipx/).

```sh
python3 -m venv ~/.local/share/pipx-venv
~/.local/share/pipx-venv/bin/pip install pipx
ln -s ~/.local/share/pipx-venv/bin/pipx ~/.local/bin/pipx
pipx ensurepath
```

And then install pbs-workbench with

```sh
pipx install git+https://github.com/eliocamp/pbs-workbench.git
```

To uninstall, run `bash pbs-workbench/uninstall.sh`.

## Quick Start

0. **Create a profile** (first time only):

```sh
job profile
```

Use the UI to configure job requirements (CPUs, memory, walltime, etc.). 
If you want to create more than one profile, you can run `job profile [profile]` to create a new profile with a particular name. 

1. **Start a job**:

```sh
job start
```

This will start the `default` profile. You can start a different one with `job start [profile]`.

2. **Monitor your job**:
 
The monitor starts automatically, showing job status and connection instructions. 
You can safely close the monitor with `Ctrl + C` and restart it with 

```sh
job monitor
```

3. **End your job**:

To end the job early use 

```sh
job end
```

## Connecting to the workbench

You can connect to the workbench using SSH using the commands shown in the monitor. 

Once the job starts, the monitor show something like this: 

```
─────────────────────────────────────────────────────────────────────────────────────────
                                   PBS Workbench Monitor
───────────────────────────────────────────────────────────────────────────────────────── 
 Job ID: 170258723.gadi-pbs                                                             
 Usage: 15 SU                                                                           
 Running on node gadi-cpu-clx-0428                                                      
                                                                                        
 SSH command:                                                                           
    ssh -X xxxxx@gadi-cpu-clx-0428                                                  
 SSH tunnel:                                                                            
    ssh -L 8080:127.0.0.1:8080 xxxxx@gadi-cpu-clx-0428                                
 Remote-ssh:                                                                            
    --remote ssh-remote+gadi-cpu-clx-0428 /home/565/xxxxx     
                                                                                        
         00:57:52                    Progress: 12 %                    07:02:08         
            0.0GB                      Memory: 0 %                     32.0GB           
                                        CPU: 0 %                                        
─────────────────────────────────────────────────────────────────────────────────────────

```

The monitor will tell you the status of the job and the compute node where it's running. 
It will also show you convenient commands that you can copy to connect directly to the compute node via SSH, create an SSH tunnel or connect in VSCode with the Remote-SSH extension. 
The bars wil show you your used and remaining time, as well as CPU usage and memory usage reported by `qstat`. 
If you consistently underuse your CPU, consider requesting a smaller job. 

### SSH

In a terminal **in your local machine**: 

Use the SSH command to ssh into the node: 

```sh
ssh -X xxxxx@gadi-cpu-clx-0428
```

### VScode and similar IDEs

To use a IDE that supports the Remote SSH extension, like VSCode or its forks, first you need to set up the proxy jump [as explained here](https://21centuryweather.github.io/21st-Century-Weather-Software-Wiki/gadi/vscode.html#configure-ssh-only-once). 

After that setup, you can install the [companion extension](https://github.com/eliocamp/pbs-workbench-vscode). 
It will add commands to start and stop Workbenches as well as a command to connect to it via Remote SSH extension. 

Alternatively, you can use the "Remote-ssh" command provided by the monitor. 
Open a new terminal in your local machine, write your editor's command followed by the remote-ssh command.

For example, to use vscode, use 

```sh
code --remote ssh-remote+gadi-cpu-clx-0428 /home/565/xxxxx
```

For Positron, use

```sh
positron --remote ssh-remote+gadi-cpu-clx-0428 /home/565/xxxxx
```

This will open the editor, connect to the remote node, and open the current directory. 

### Jupyter notebook

To run a jupyter notebook first **in your local machine** run the SSH tunnel command:  


```sh
ssh -L 8080:127.0.0.1:8080 xxxxx@gadi-cpu-clx-0428
```

This will SSH into the node and now your terminal will be **in the remote**. 
Navigate to your project and start a jupyter notebook 

```sh
module load jupyterlab/3.4.3-py3.9
jupyter notebook --no-browser --port=8080
```

This will start the server up and end with this message

```
    To access the notebook, open this file in a browser:
        file:///home/xxxx/xxxx/.local/share/jupyter/runtime/nbserver-275862-open.html
    Or copy and paste one of these URLs:
        http://localhost:8889/?token=49ba65820b79e0cfcf769f311cob5f70ffac2396f251ba7a
     or http://127.0.0.1:8889/?token=49ba65820b79e0cfcf769f311cob5f70ffac2396f251ba7a
```

Open any of the two last links in a browser and done!

## More details 

### Project File

PBS Workbench tracks your running job using the file `~/pbs-workbench/workbenches/00`, which contains the job ID of the current job. 
Don't edit or delete that file. 

### Log Files

Job output is saved to `~/pbs-workbench/logs/` with files named:

- `{job_id}.gadi-pbs.OU` (standard output)
- `{job_id}.gadi-pbs.ER` (standard error)


## Limitations

Currently, only one job can be run at a time. 

