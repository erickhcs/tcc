import sys
import subprocess
import os

def run_command(base_command, client_folder, num_runs):
  for i in range(1, num_runs + 1):
    log_folder = f"{client_folder}/{i}"

    # Create the log folder if it does not exist
    if not os.path.exists(log_folder):
      os.makedirs(log_folder)

    # Construct the command with the incremented log folder
    command = f"{base_command} {log_folder}"

    # Print the command to be run (optional, for debugging)
    print(f"Running command: {command}")

    # Run the command and wait for it to complete
    subprocess.run(command, shell=True, check=True)

# Check if the script received the correct number of arguments
if len(sys.argv) != 3:
  print("Usage: python script.py <base_command> <num_runs> <folder>")
  sys.exit(1)

# python3 ./script.py client_1 834
# Get the arguments
base_command = './http-1.1_p_pl 10.2.32.126:32001 v1 15 user1 ../per_video/v1/u1.txt 30 4 12 0 1 0 2'
client_folder = 'logs_erick/' + sys.args[1]
num_runs = int(sys.argv[2])

# Run the commands
run_command(base_command, client_folder, num_runs)
