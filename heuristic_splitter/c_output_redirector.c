#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>



struct pipe_fds {
    int read_end;
    int write_end;
};


struct pipe_fds open_pipe() {
   
    int pipe_fdss[2];
    struct pipe_fds pipe_fds_stuff;

    if (pipe(pipe_fdss) == -1) {
        perror("pipe");
        pipe_fds_stuff.read_end = -1;
        pipe_fds_stuff.write_end = -1;
        return pipe_fds_stuff;
    }

    pipe_fds_stuff.read_end = pipe_fdss[0];
    pipe_fds_stuff.write_end = pipe_fdss[1];

    return pipe_fds_stuff;
}

int open_tmp_file() {
    int fd = open("delete_me.txt", O_RDWR | O_CREAT);

    return fd;
}
 

int redirect_stdout_to_fd_and_duplicate_and_close(int fd) {
    int stdout_backup = dup(STDOUT_FILENO); 
    if (dup2(fd, STDOUT_FILENO) == -1) { 
        perror("dup2");
        return 1;
    }

    if (close(fd) == -1) {
        perror("close");
        return 1;

    }

    //char buffer[8192];
    //setvbuf(stdout, buffer, _IOFBF, sizeof(buffer));

    return stdout_backup;
}

int print_something() {
    // Step 3: printf (this will be redirected to the pipe and suppressed from console)
    printf("%s", "TEST\n");
    return 0;
}

int call_flush() {
    fflush(stdout);
    return 0;
}


/*
int redirect_back

    // Step 4: Re-redirect STDOUT back to the console
    fflush(stdout);
    dup2(stdout_backup, STDOUT_FILENO); // Restore original STDOUT
    close(stdout_backup); // Close the backup descriptor


    printf("%s", "FINALLY!\n");

    return 0;
}


int main() {

    //int pipe_fds[2];
    int* pipe_fds = open_pipe();
    //pipe_fds = call_pipe();

    // Step 1: Open a pipe
    // Step 2: Redirect STDOUT to the pipe
    int stdout_backup = dup(STDOUT_FILENO); // Backup original STDOUT
    if (dup2(pipe_fds[1], STDOUT_FILENO) == -1) { // Redirect STDOUT to pipe
        perror("dup2");
        return 1;
    }
    close(pipe_fds[1]); // Close the write end of the pipe (we don’t need it after dup2)

    // Step 3: printf (this will be redirected to the pipe and suppressed from console)
    printf("%s", "TEST\n");

    // Step 4: Re-redirect STDOUT back to the console
    fflush(stdout);
    dup2(stdout_backup, STDOUT_FILENO); // Restore original STDOUT
    close(stdout_backup); // Close the backup descriptor


    printf("%s", "FINALLY!\n");
}
*/
