_job_complete() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="start monitor end profile su modify --help -h"

    case ${COMP_CWORD} in
        1)
            # Complete main commands and options
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        2)
            # Complete based on the previous command
            case ${prev} in
                start|su|modify)
                    # Complete with profile names
                    local profiles=""
                    if [ -d "$HOME/pbs-workbench/profiles" ]; then
                        profiles=$(find "$HOME/pbs-workbench/profiles" -name "*.sh" -type f -exec basename {} .sh \; 2>/dev/null)
                    fi
                    COMPREPLY=( $(compgen -W "${profiles}" -- ${cur}) )
                    ;;
                profile)
                    # For profile command, complete with existing profile names for editing
                    local profiles=""
                    if [ -d "$HOME/pbs-workbench/profiles" ]; then
                        profiles=$(find "$HOME/pbs-workbench/profiles" -name "*.sh" -type f -exec basename {} .sh \; 2>/dev/null)
                    fi
                    COMPREPLY=( $(compgen -W "${profiles}" -- ${cur}) )
                    ;;
                monitor|end)
                    # These commands don't take arguments
                    COMPREPLY=()
                    ;;
            esac
            ;;
        *)
            # No completion for further arguments
            COMPREPLY=()
            ;;
    esac
    return 0
}
complete -F _job_complete job
