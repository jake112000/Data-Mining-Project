import os
import json
import pandas as pd
import matplotlib.pyplot as plt

# folder that stores the dataset
data_folder = "doo-re"

# List of activity folders in the dataset
activities = ["Eating", "Eating_together", "Lab_meeting", "Phone_call", "Reading", "Seminar", "Small_talk", "Study_together", "Technical_discussion"]

# sensors that give number readings, everything else just turns on/off
number_sensors = ["Brightness", "Humidity", "Temperature", "Sound", "Podium"]

# Holds every episode loaded
all_data = []

# Loads the metadata and sensor data for each episode.
def load_episodes():
    for activity in activities:
        meta_folder = os.path.join(data_folder, activity, "metadata")
        sensor_folder = os.path.join(data_folder, activity, "sensor")

        if not os.path.exists(meta_folder):
            continue

        files = os.listdir(meta_folder)
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            meta_path = os.path.join(meta_folder, file_name)
            meta_file = open(meta_path, "r", encoding="utf-8")
            meta = json.load(meta_file)
            meta_file.close()

            base_name = file_name.replace(".json", "")
            sensor_path = os.path.join(sensor_folder, base_name + ".csv")

            if not os.path.exists(sensor_path):
                continue

            sensor_data = pd.read_csv(sensor_path)
            sensor_data["timestamp"] = pd.to_datetime(sensor_data["timestamp"], unit="ms")
            sensor_data["timestamp"] = sensor_data["timestamp"].dt.tz_localize("UTC").dt.tz_convert("Asia/Seoul")

            episode = {}
            episode["activity"] = activity
            episode["id"] = base_name
            episode["meta"] = meta
            episode["sensor_data"] = sensor_data

            all_data.append(episode)

# Creates a table with summary information for each episode.
def make_summary_table():
    rows = []
    for ep in all_data:
        m = ep["meta"]

        duration = m["duration"]
        people = m["avg_n_human"]

        row = {}
        row["activity"] = ep["activity"]
        row["duration"] = duration
        row["people"] = people
        row["num_readings"] = len(ep["sensor_data"])
        rows.append(row)

    summary = pd.DataFrame(rows)

    return summary

# Creates a table with each sensor's type, number of readings, episode appearances, and activities.
def make_sensor_inventory():
    sensor_stats = {}

    for ep in all_data:
        sensor_groups = ep["sensor_data"].groupby("sensor_name")

        for sensor_name, sensor_rows in sensor_groups:
            if sensor_name not in sensor_stats:
                sensor_stats[sensor_name] = {
                    "total_readings": 0,
                    "episodes_present": 0,
                    "activities": [],
                    "has_numeric_values": False,
                    "has_boolean_values": False,
                    "has_other_values": False,
                }

            stats = sensor_stats[sensor_name]
            stats["total_readings"] += len(sensor_rows)
            stats["episodes_present"] += 1

            if ep["activity"] not in stats["activities"]:
                stats["activities"].append(ep["activity"])

            values = sensor_rows["value"].dropna()
            if not values.empty:
                numeric_values = pd.to_numeric(values, errors="coerce")
                boolean_values = values.astype(str).str.lower().isin(["true", "false"])

                if numeric_values.notna().any():
                    stats["has_numeric_values"] = True
                if boolean_values.any():
                    stats["has_boolean_values"] = True
                if (~numeric_values.notna() & ~boolean_values).any():
                    stats["has_other_values"] = True

    inventory_rows = []
    for sensor_name in sorted(sensor_stats):
        stats = sensor_stats[sensor_name]
        value_types = []

        if stats["has_numeric_values"]:
            value_types.append("Numeric")
        if stats["has_boolean_values"]:
            value_types.append("Boolean")
        if stats["has_other_values"]:
            value_types.append("Event/state")

        if len(value_types) == 0:
            value_type = "Unknown"
        elif len(value_types) == 1:
            value_type = value_types[0]
        else:
            value_type = "Mixed"

        inventory_rows.append({
            "sensor_name": sensor_name,
            "value_type": value_type,
            "total_readings": stats["total_readings"],
            "episodes_present": stats["episodes_present"],
            "activities_present": len(stats["activities"]),
        })

    inventory = pd.DataFrame(inventory_rows)
    inventory.to_csv("sensor_inventory.csv", index=False)
    return inventory

#  Creates a bar graph showing the number of episodes each activity type recorded
def plot_episode_counts(summary):
    counts = summary["activity"].value_counts()
    #Formatting the graph
    plt.figure(figsize=(8, 5))
    plt.barh(counts.index, counts.values)
    plt.title("Number of episodes per activity")
    plt.xlabel("count")
    plt.tight_layout()
    plt.savefig("episode_counts.png")
    plt.close()

# Creates a box plot of the duration of each activity type
def plot_duration_boxplot(summary):
    activity_list = summary["activity"].unique()
    activity_list = sorted(activity_list)

    box_data = []
    for activity in activity_list:
        values = summary[summary["activity"] == activity]["duration"]
        box_data.append(values.dropna().values)
    #Formatting the graph
    plt.figure(figsize=(10, 5))
    plt.boxplot(box_data, tick_labels=activity_list)
    plt.title("Duration by activity")
    plt.ylabel("duration (sec)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("duration_boxplot.png")
    plt.close()

# Creates a boxplot showing the number of individuals participating in each activity type
def plot_people_boxplot(summary):
    activity_list = summary["activity"].unique()
    activity_list = sorted(activity_list)

    box_data = []
    for activity in activity_list:
        values = summary[summary["activity"] == activity]["people"]
        box_data.append(values.dropna().values)
    #Formatting the graph
    plt.figure(figsize=(10, 5))
    plt.boxplot(box_data, tick_labels=activity_list)
    plt.title("Average participants by activity")
    plt.ylabel("avg. participants")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("people_boxplot.png")
    plt.close()

#Counts the number of times the door is activated in an episode. Used to generate the oor use boxplot
def count_door_activations():
    rows = []
    for ep in all_data:
        door_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"].str.startswith("Door")]
        count = len(door_rows)
        row = {}
        row["activity"] = ep["activity"]
        row["door_count"] = count
        rows.append(row)

    door_table = pd.DataFrame(rows)
    return door_table

# Creates a boxplot showing the number of times the door is activated in each activity type
def plot_door_use_boxplot(door_table):
    activity_list = door_table["activity"].unique()
    activity_list = sorted(activity_list)

    box_data = []
    for activity in activity_list:
        values = door_table[door_table["activity"] == activity]["door_count"]
        box_data.append(values.dropna().values)
    #Formatting the graph
    plt.figure(figsize=(10, 5))
    plt.boxplot(box_data, tick_labels=activity_list)
    plt.title("Door activation count by activity")
    plt.ylabel("num activations")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("door_use_boxplot.png")
    plt.close()  

# Counts projector activations in each episode. Trailing spaces in sensor names are ignored.
def count_projector_activations():
    rows = []
    for ep in all_data:
        projector_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"].astype(str).str.strip() == "Projector"]
        count = len(projector_rows)
        row = {}
        row["activity"] = ep["activity"]
        row["projector_count"] = count
        rows.append(row)

    projector_table = pd.DataFrame(rows)
    return projector_table

# Creates a boxplot showing projector activations by activity type.
def plot_projector_use_boxplot(projector_table):
    activity_list = sorted(projector_table["activity"].unique())
    box_data = []
    for activity in activity_list:
        values = projector_table[projector_table["activity"] == activity]["projector_count"]
        box_data.append(values.dropna().values)

    plt.figure(figsize=(10, 5))
    plt.boxplot(box_data, tick_labels=activity_list)
    plt.title("Projector activation count by activity")
    plt.ylabel("num activations")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("projector_use_boxplot.png")
    plt.close()

# Counts Aircon readings in each episode.
def count_aircon_activations():
    rows = []
    for ep in all_data:
        aircon_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"].astype(str).str.startswith("Aircon")]
        count = len(aircon_rows)
        row = {}
        row["activity"] = ep["activity"]
        row["aircon_count"] = count
        rows.append(row)

    aircon_table = pd.DataFrame(rows)
    return aircon_table

# Creates a boxplot showing Aircon readings by activity type.
def plot_aircon_use_boxplot(aircon_table):
    activity_list = sorted(aircon_table["activity"].unique())
    box_data = []
    for activity in activity_list:
        values = aircon_table[aircon_table["activity"] == activity]["aircon_count"]
        box_data.append(values.dropna().values)

    plt.figure(figsize=(10, 5))
    plt.boxplot(box_data, tick_labels=activity_list)
    plt.title("Aircon reading count by activity")
    plt.ylabel("num readings")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("aircon_use_boxplot.png")
    plt.close()

# Computes the average brightness value for each sensor channel in each episode, excluding zeros and missing values.
def count_brightness_readings():
    rows = []
    for ep in all_data:
        for sensor_name in ["Brightness_1", "Brightness_2"]:
            sensor_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"] == sensor_name].copy()
            values = pd.to_numeric(sensor_rows["value"], errors="coerce").dropna()
            values = values[values != 0]
            avg_value = values.mean() if not values.empty else None

            row = {}
            row["activity"] = ep["activity"]
            row["sensor_name"] = sensor_name
            row["brightness_avg_value"] = avg_value
            rows.append(row)

    brightness_table = pd.DataFrame(rows)
    return brightness_table

# Creates separate boxplots for Brightness_1 and Brightness_2 by activity type
def plot_brightness_boxplot(brightness_table):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    sensor_names = ["Brightness_1", "Brightness_2"]

    for ax, sensor_name in zip(axes, sensor_names):
        activity_list = sorted(brightness_table["activity"].unique())
        box_data = []
        for activity in activity_list:
            values = brightness_table[(brightness_table["activity"] == activity) & (brightness_table["sensor_name"] == sensor_name)]["brightness_avg_value"]
            box_data.append(values.dropna().values)

        ax.boxplot(box_data, tick_labels=activity_list)
        ax.set_title(f"{sensor_name} by activity")
        ax.set_ylabel("avg. brightness")
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig("brightness_boxplots.png")
    plt.close()

# Computes the average humidity value for each sensor channel in each episode, excluding zeros and missing values.
def count_humidity_readings():
    rows = []
    for ep in all_data:
        for sensor_name in ["Humidity_1", "Humidity_2"]:
            sensor_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"] == sensor_name].copy()
            values = pd.to_numeric(sensor_rows["value"], errors="coerce").dropna()
            values = values[values != 0]
            avg_value = values.mean() if not values.empty else None

            row = {}
            row["activity"] = ep["activity"]
            row["sensor_name"] = sensor_name
            row["humidity_avg_value"] = avg_value
            rows.append(row)

    humidity_table = pd.DataFrame(rows)
    return humidity_table

# Creates separate boxplots for Humidity_1 and Humidity_2 by activity type
def plot_humidity_boxplot(humidity_table):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    sensor_names = ["Humidity_1", "Humidity_2"]

    for ax, sensor_name in zip(axes, sensor_names):
        activity_list = sorted(humidity_table["activity"].unique())
        box_data = []
        for activity in activity_list:
            values = humidity_table[(humidity_table["activity"] == activity) & (humidity_table["sensor_name"] == sensor_name)]["humidity_avg_value"]
            box_data.append(values.dropna().values)

        ax.boxplot(box_data, tick_labels=activity_list)
        ax.set_title(f"{sensor_name} by activity")
        ax.set_ylabel("avg. humidity")
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig("humidity_boxplots.png")
    plt.close()

# Computes the average temperature value for each sensor channel in each episode, excluding zeros and missing values.
def count_temperature_readings():
    rows = []
    for ep in all_data:
        for sensor_name in ["Temperature_1", "Temperature_2"]:
            sensor_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"] == sensor_name].copy()
            values = pd.to_numeric(sensor_rows["value"], errors="coerce").dropna()
            values = values[values != 0]
            avg_value = values.mean() if not values.empty else None

            row = {}
            row["activity"] = ep["activity"]
            row["sensor_name"] = sensor_name
            row["temperature_avg_value"] = avg_value
            rows.append(row)

    temperature_table = pd.DataFrame(rows)
    return temperature_table

# Creates separate boxplots for Temperature_1 and Temperature_2 by activity type
def plot_temperature_boxplot(temperature_table):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    sensor_names = ["Temperature_1", "Temperature_2"]
    for ax, sensor_name in zip(axes, sensor_names):
        activity_list = sorted(temperature_table["activity"].unique())
        box_data = []
        for activity in activity_list:
            values = temperature_table[(temperature_table["activity"] == activity) & (temperature_table["sensor_name"] == sensor_name)]["temperature_avg_value"]
            box_data.append(values.dropna().values)

        ax.boxplot(box_data, tick_labels=activity_list)
        ax.set_title(f"{sensor_name} by activity")
        ax.set_ylabel("avg. temperature")
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig("temperature_boxplots.png")
    plt.close()


# Computes the average sound value for each sensor channel in each episode, excluding zeros and missing values.
def count_sound_readings():
    rows = []
    for ep in all_data:
        for sensor_name in ["Sound_C", "Sound_L", "Sound_P", "Sound_R"]:
            sensor_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"] == sensor_name].copy()
            values = pd.to_numeric(sensor_rows["value"], errors="coerce").dropna()
            values = values[values != 0]
            avg_value = values.mean() if not values.empty else None

            row = {}
            row["activity"] = ep["activity"]
            row["sensor_name"] = sensor_name
            row["sound_avg_value"] = avg_value
            rows.append(row)

    sound_table = pd.DataFrame(rows)
    return sound_table

# Creates a boxplot image for each sound sensor channel.
def plot_sound_boxplot(sound_table):
    sensor_names = ["Sound_C", "Sound_L", "Sound_P", "Sound_R"]
    activity_list = sorted(sound_table["activity"].unique())

    for sensor_name in sensor_names:
        box_data = []
        for activity in activity_list:
            values = sound_table[(sound_table["activity"] == activity) & (sound_table["sensor_name"] == sensor_name)]["sound_avg_value"]
            box_data.append(values.dropna().values)

        plt.figure(figsize=(10, 5))
        plt.boxplot(box_data, tick_labels=activity_list)
        plt.title(f"{sensor_name} by activity")
        plt.ylabel("avg. sound")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(sensor_name.lower() + "_boxplot.png")
        plt.close()


# Computes how often each seat sensor reports True in each episode.
def count_seat_occupancy():
    rows = []
    seat_names = [
        "Seat_1", "Seat_2", "Seat_3", "Seat_4", "Seat_5", "Seat_6",
        "Seat_7", "Seat_8", "Seat_9", "Seat_10", "Seat_11", "Seat_12"
    ]

    for ep in all_data:
        for seat_name in seat_names:
            seat_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"] == seat_name]
            values = seat_rows["value"].dropna().astype(str).str.lower()

            if len(values) > 0:
                occupied_percent = (values == "true").mean() * 100
            else:
                occupied_percent = None

            row = {}
            row["activity"] = ep["activity"]
            row["sensor_name"] = seat_name
            row["occupied_percent"] = occupied_percent
            rows.append(row)

    seat_table = pd.DataFrame(rows)
    return seat_table


# Creates a heatmap of average seat occupancy by activity.
def plot_seat_heatmap(seat_table):
    table = seat_table.pivot_table(
        index="activity",
        columns="sensor_name",
        values="occupied_percent",
        aggfunc="mean"
    )
    table = table.reindex(sorted(table.index))
    table = table.reindex(sorted(table.columns), axis=1)

    plt.figure(figsize=(12, 6))
    plt.imshow(table, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    plt.colorbar(label="average occupied readings (%)")
    plt.xticks(range(len(table.columns)), table.columns, rotation=45)
    plt.yticks(range(len(table.index)), table.index)
    plt.title("Average seat occupancy by activity")
    plt.xlabel("seat sensor")
    plt.ylabel("activity")
    plt.tight_layout()
    plt.savefig("seat_occupancy_heatmap.png")
    plt.close()


# Computes the percentage that each motion sensor reports True in each episode.
def count_motion_activation():
    rows = []
    sensor_names = [
        "Motion_1", "Motion_2", "Motion_3", "Motion_4", "Motion_5", "Motion_6",
        "Motion_7", "Motion_8"
    ]

    for ep in all_data:
        for sensor_name in sensor_names:
            sensor_rows = ep["sensor_data"][ep["sensor_data"]["sensor_name"] == sensor_name]
            values = sensor_rows["value"].dropna().astype(str).str.lower()

            if len(values) > 0:
                activated_percent = (values == "true").mean() * 100
            else:
                activated_percent = None

            row = {}
            row["activity"] = ep["activity"]
            row["sensor_name"] = sensor_name
            row["activated_percent"] = activated_percent
            rows.append(row)

    sensor_table = pd.DataFrame(rows)
    return sensor_table


# Creates a heatmap of average motion sensor activation by activity.
def plot_motion_heatmap(sensor_table):
    table = sensor_table.pivot_table(
        index="activity",
        columns="sensor_name",
        values="activated_percent",
        aggfunc="mean"
    )
    table = table.reindex(sorted(table.index))
    table = table.reindex(sorted(table.columns), axis=1)

    plt.figure(figsize=(12, 6))
    plt.imshow(table, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    plt.colorbar(label="average True readings (%)")
    plt.xticks(range(len(table.columns)), table.columns, rotation=45)
    plt.yticks(range(len(table.index)), table.index)
    plt.title("Average True reading by activity")
    plt.xlabel("motion sensor")
    plt.ylabel("activity")
    plt.tight_layout()
    plt.savefig("motion_activation_heatmap.png")
    plt.close()

def describe_duration_and_people(summary):
    duration_stats = summary.groupby("activity")["duration"].describe()
    people_stats = summary.groupby("activity")["people"].describe()

    duration_stats.to_csv("duration_stats.csv")
    people_stats.to_csv("people_stats.csv")


def describe_door_activations(door_table):
    stats = door_table.groupby("activity")["door_count"].describe()
    stats.to_csv("door_stats.csv")


def describe_projector_activations(projector_table):
    stats = projector_table.groupby("activity")["projector_count"].describe()
    stats.to_csv("projector_stats.csv")


def describe_aircon_activations(aircon_table):
    stats = aircon_table.groupby("activity")["aircon_count"].describe()
    stats.to_csv("aircon_stats.csv")

# run everything
load_episodes()
sensor_inventory = make_sensor_inventory()
summary = make_summary_table()
door_table = count_door_activations()
brightness_table = count_brightness_readings()
humidity_table = count_humidity_readings()
temperature_table = count_temperature_readings()
sound_table = count_sound_readings()
seat_table = count_seat_occupancy()
motion_table = count_motion_activation()
projector_table = count_projector_activations()
aircon_table = count_aircon_activations()
plot_episode_counts(summary)
plot_duration_boxplot(summary)
plot_people_boxplot(summary)
plot_door_use_boxplot(door_table)
plot_brightness_boxplot(brightness_table)
plot_humidity_boxplot(humidity_table)
plot_temperature_boxplot(temperature_table)
plot_sound_boxplot(sound_table)
plot_seat_heatmap(seat_table)
plot_motion_heatmap(motion_table)
plot_projector_use_boxplot(projector_table)
plot_aircon_use_boxplot(aircon_table)
describe_aircon_activations(aircon_table)
describe_door_activations(door_table)
describe_duration_and_people(summary)
describe_projector_activations(projector_table)