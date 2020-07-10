import json
import logging
import os
from collections import defaultdict


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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

COUNTRY_NAME = {
    103: "USA",
    201: "Germany",
    101: "USSR",
    102: "Great Britain",
}

COUNTRY_FACTION = {
    103: "Allies",
    201: "Axis",
    101: "Allies",
    102: "Allies",
}


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
    events = sorted(events, key=lambda x: int(x["T"]))
    # with open("recent.txt", 'w') as f:
    #     output = ""
    #     for event in events:
    #         for key, val in event.items():
    #             output += "{}:{} ".format(key, val)
    #         output += "\n"
    #     f.write(output)
    return events


def calculate_scores(file_contents):
    events = get_events(file_contents)
    plane_to_player = {}
    pilots = []
    player_to_country = {}
    bot_pilots = []
    bot_planes = []
    kills = defaultdict(list)
    deaths = defaultdict(list)
    for event in events:
        logging.debug(json.dumps(event))
        a_type = int(event['AType'])
        if a_type == OBJECT_SPAWNED:
            country = int(event["COUNTRY"])
            player = int(event["ID"])
            pid = int(event["PID"])
            if event['TYPE'].startswith('Bot'):
                bot_pilots.append(player)
                bot_planes.append(pid)
            player_to_country[player] = country
        if a_type == PLAYER_PLANE:
            player = int(event['PID'])
            pilots.append(player)
            plane = int(event['PLID'])
            plane_to_player[plane] = {
                'player': player,
                'plane': plane,
                'name': event['NAME']
            }

        if a_type == KILL:
            attacker = int(event['AID'])
            victim = int(event['TID'])
            if attacker == -1:
                # if no one is listed as an attacker, go find them through prior hit events
                for prior_event in events:
                    if prior_event == event:
                        break
                    if int(prior_event['AType']) == HIT and int(prior_event["TID"] == victim):
                        attacker = int(prior_event['AID'])

            if attacker == -1:
                logging.info("{} died to no one.".format(victim))
                deaths[victim].append(attacker)

            if victim not in bot_pilots and victim not in pilots:
                kills[attacker].append(victim)
                deaths[victim].append(attacker)
            else:
                logging.info("Ignoring additional pilot kill")

            # logging
            attacker_name = attacker if attacker not in plane_to_player else plane_to_player[attacker]['name']
            victim_name = victim if victim not in plane_to_player else plane_to_player[victim]['name']
            logging.info('{} killed {}'.format(attacker_name, victim_name))

    country_kills = defaultdict(int)
    for attacker, victims in kills.items():
        for victim in victims:
            # if attacker in player_to_country:
            if attacker != -1:
                country_kills[player_to_country[attacker]] += 1

    country_deaths = defaultdict(int)
    for victim, attackers in deaths.items():
        country_deaths[player_to_country[victim]] += len(attackers)
    print("===Victories===")
    for country, kills in country_kills.items():
        print("{} scored {} victories".format(COUNTRY_NAME[country], kills))

    print("\n===Losses===")
    for country, deaths in country_deaths.items():
        print("{} lost {} airframes".format(COUNTRY_NAME[country], deaths))

    print("\nScore formula = 5 * victories - 3 * losses")
    for country, deaths in country_deaths.items():
        kills = 0
        if country in country_kills:
            kills = country_kills[country]
        print('{} score: 5 * {} - 3 * {} = {}'.format(
            COUNTRY_NAME[country],
            kills,
            deaths,
            5 * kills - 3 * deaths))


def print_scores(mission_files, mission_name, log_dir):
    file_contents = load_mission(log_dir, mission_files, mission_name)
    calculate_scores(file_contents)
    input("Press any key to close the window")


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

    mission_name = prompt_mission_name(mission_files)
    print_scores(mission_files, mission_name, log_dir)


def get_config():
    with open('config.json', 'r') as f:
        return json.load(f)


# score
# kills are 5 points
# deaths are -3 points
if __name__ == '__main__':
    logging.basicConfig(filename='stat-log.log', level=logging.DEBUG)
    main()
