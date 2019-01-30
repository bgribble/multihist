## multihist -- manage multiple open shell histories

I use tmux and typically have 10 or so `bash` shells open at any one time.
I use shell history fairly aggressively to minimize how much I type.  It's
always been frustrating to me that `bash` wants a single HISTFILE and that 
reading, writing, and searching it works sort of poorly.

### Goals

* Up-arrow in a shell always steps through the history of commands typed in that
specific shell
* Ctrl-R (reverse isearch) can search the history of all the shells, not just 
the one I'm typing in
* History is forever

### How it works

* Shell histories live in a new directory.  On my machine it's 
~/.history 
* Each shell saves a history file containing the commands typed into that 
specific shell
* Each shell uses as its HISTFILE a custom merged file that's dynamically 
updated, which contains the shell-specific histories of all the shells, 
with this specific shell's history last
* A helper script is invoked as the `PROMPT_COPMMAND` to update the merged history 
files if needed
* Shell histories from old/closed shells are automatically compacted but the
contents stay around forever. 
* To improve the performance of rebuilding merged files, there's a table of contents
for each merged history file

### Installing 

`setup.py` builds a script called `multihist`.  Install it to your path somewhere.

In your `.bash_profile`, add this bit.  Update `SHELL_HISTDIR` to taste, and merge in
whatever customizations you may already have to your `PROMPT_COMMAND`.

```
export SHELL_UUID=`uuidgen`
export SHELL_HISTDIR=~/.history/
export SHELL_HISTFILE=${SHELL_HISTDIR}/shell-${SHELL_UUID}
export HISTFILE=${SHELL_HISTDIR}/merged-${SHELL_UUID}

function update_histfiles () {
    history -a ${SHELL_HISTFILE} ;
    multihist --update;
    history -c ; 
    history -r ;
}

function init_histfiles () {
    # on login: smash all files older than 30 days into one; touch the new history file
    HIST_OLDFILES=`find ${SHELL_HISTDIR} -mtime +30 -name 'shell-*'`
    if [ -z ${HIST_OLDFILES} ]
    then
        echo "No old history to squash"
    else
        echo "Squashing ${HIST_OLDFILES}"
        (cat ${HIST_OLDFILES} | sort | uniq) >> ${SHELL_HISTDIR}/shell-oldfiles
        rm -f ${HIST_OLDFILES}
        rm -f `echo ${HIST_OLDFILES} | sed -e s/shell/merged/g`
    fi
    touch ${SHELL_HISTFILE}
    touch ${HISTFILE}
    multihist --init;
}

export PROMPT_COMMAND="update_histfiles;"
init_histfiles;
```


