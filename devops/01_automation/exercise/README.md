# Module 1 Exercise: Automating with Cron

Now that you have learned about Linux, standard streams, and bash scripting, it is time to put it all together into an automated workflow.

## The Challenge

In the labs, we wrote `monitor.sh`, which runs a continuous `while true` loop. While this is useful for debugging, in a real production environment, you don't want to leave scripts running in your terminal forever.

Instead, we use **cron**, a time-based job scheduler in Unix-like operating systems.

Your task:
1. Copy the `monitor.sh` script from the `labs/` folder into this `exercise/` folder and rename it to `check_cpu.sh`.
2. Modify `check_cpu.sh` so that it **no longer loops infinitely**. It should run *exactly once*, check the CPU, log it if it is over the threshold, and then exit.
3. Make the script executable (`chmod +x check_cpu.sh`).
4. Write a **cron expression** that will automatically run this script **every 5 minutes, every day**.
5. Save your cron expression in a file called `my_cron.txt`.

*Hint*: You edit your crontab by typing `crontab -e` in the terminal.

Good luck! When you are done, check the `solution/` folder.
