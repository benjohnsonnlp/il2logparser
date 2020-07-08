import json
import os
from collections import defaultdict

MISSION_START = 0
HIT = 1
DAMAGE = 2
KILL = 3
PLAYER_MISSION_END = 4
TAKE_OFF = 5
LANDING = 6
MISSION_END = 7
MISSION_OBJECTIVE = 8
AIRFIELD_INFO = 9
PLAYER_PLANE = 10
GROUP_INIT = 11
OBJECT_SPAWNED = 12
INFLUENCE_AREA_HEADER = 13
INFLUENCE_AREA_BOUNDARY = 14
LOG_VERSION = 15
BOT_UNINIT = 16
POS_CHANGED = 17
BOT_EJECT_LEAVE = 18
ROUND_END = 19
JOIN = 20
LEAVE = 21
NOOP = 22
ALL = 23


def get_logs(directory) -> dict:
    mission_files = defaultdict(list)
    for filename in os.listdir(directory):
        if filename.endswith(".txt") and filename.startswith("missionReport"):
            mission_name = filename.split('[')[0]
            mission_files[mission_name].append(filename)

    return mission_files


def prompt_mission_name(mission_files):
    missions = list(mission_files.keys())
    print("Type the number of the mission you want to score:")
    for i, mission in enumerate(missions):
        print("[{}]: {}".format(i, mission))
    number = int(input("\n"))
    return missions[number]


def get_events(file_contents):
    events = []
    for line in file_contents.split("\n"):
        event = {}
        for token in line.split():
            if ":" in token and len(token.split(':')) == 2:
                key, value = token.split(":")
                event[key] = value
        if event:
            events.append(event)
    return events


def calculate_scores(file_contents):
    events = get_events(file_contents)
    plane_to_player = {}
    kills = defaultdict(list)
    for event in events:
        a_type = int(event['AType'])
        if a_type == PLAYER_PLANE:
            player = int(event['PID'])
            plane = int(event['PLID'])
            plane_to_player[plane] = player
        if a_type == KILL:
            attacker = int(event['AID'])
            victim = int(event['TID'])
            if attacker != -1:
                kills[attacker].append(victim)

    for attacker, victims in kills.items():
        for victim in victims:
            print('{} killed {}'.format(attacker, victim))


def print_scores(mission_files, mission_name, log_dir):
    file_contents = load_mission(log_dir, mission_files, mission_name)
    scores = calculate_scores(file_contents)
    print(scores)


def load_mission(log_dir, mission_files, mission_name):
    file_contents = ""
    for mission_file in mission_files[mission_name]:
        filename = os.path.join(log_dir, mission_file)
        with open(filename, 'r') as f:
            file_contents += f.read()
    return file_contents


def main():
    log_dir = get_config()['DATA_DIR']
    mission_files: dict = get_logs(log_dir)
    for name, files in mission_files.items():
        print(name)
    mission_name = prompt_mission_name(mission_files)
    print_scores(mission_files, mission_name, log_dir)


def get_config():
    with open('config.json', 'r') as f:
        return json.load(f)


if __name__ == '__main__':
    main()
