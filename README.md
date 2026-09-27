This project explores the DOO-RE ambient sensor dataset from a meeting room.

Setup:

Install the latest version of pandas and matplotlib
Download and place the unzipped dataset folder in the project folder with this structure:

doo-re/
	Eating/
		metadata/
		sensor/
	Eating_together/
	Lab_meeting/
	Phone_call/
	Reading/
	Seminar/
	Small_talk/
	Study_together/
	Technical_discussion/


Run:

Run this command from the project folder:

```powershell
python ".\doo_re analysis"
```

The script loads the episodes, prints summary information, creates a sensor inventory, and saves plots in the project folder. It will take a few seconds to fully create all tables and images

Main outputs:

sensor_inventory.csv
episode_counts.png
duration_boxplot.png
people_boxplot.png
door_use_boxplot.png
brightness_boxplots.png
humidity_boxplots.png
temperature_boxplots.png
sound_c_boxplot.png
sound_l_boxplot.png
sound_p_boxplot.png
sound_r_boxplot.png
seat_occupancy_heatmap.png
motion_activation_heatmap.png
projector_use_boxplot.png
aircon_use_boxplot.png
