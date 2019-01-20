Jobs are just groups of tasks, same as just any other tasks would
do. The difference there is that the each job is running in parallel
to other. However, if there is a function that requires single run,
then the concurrent processes will wait unless the lock is removed.

This is an experimental idea
