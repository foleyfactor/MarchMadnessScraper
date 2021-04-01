import os
from bs4 import BeautifulSoup
from collections import defaultdict

def get_files(dir_):
    return [os.path.join(dir_, file) for file in os.listdir(dir_) if file[-5:] == ".html"]

def get_contents(filename):
    with open(filename, 'r') as f:
        return "\n".join(f.readlines())

class Team(object):
    def __init__(self, name, seed, id_, sportsid):
        self.name = name
        self.seed = seed
        self.sportsid = sportsid
        self.id_ = id_
    
    @staticmethod
    def of_html(bs):
        name = bs.find('span', class_='name').text
        seed = int(bs.find('span', class_='seed').text)
        id_ = int(bs['data-teamid'])
        sportsid = int(bs.select('span[data-sportsid]')[0]['data-sportsid'])
        return Team(name, seed, id_, sportsid)

class Pick(object):
    def __init__(self, round_, predicted1, predicted2, actual1, actual2, chosen, winner):
        self.round_ = round_
        self.predicted1 = predicted1
        self.predicted2 = predicted2
        self.actual1 = actual1
        self.actual2 = actual2
        self.chosen = chosen
        self.winner = winner
    
    def is_played(self):
        return self.winner is not None

    def is_correct(self):
        if self.winner is None:
            return False
        return self.winner.id_ == self.chosen.id_
    
    def predicted_seed_diff(self):
        return abs(self.predicted1.seed - self.predicted2.seed)

    def was_upset_pick(self):
        loser_seed = self.predicted1.seed + self.predicted2.seed - self.chosen.seed
        return loser_seed < self.chosen.seed

    @staticmethod
    def of_html(bs, by_id, by_sportsid):
        chosen = by_sportsid[int(bs.find("span", class_="selectedToAdvance")['data-sportsid'])]
        actual1, actual2 = None, None
        span1, span2 = bs.find_all("span", class_="actual")
        if "empty" not in span1['class']:
            actual1 = by_sportsid[int(span1['data-sportsid'])]
        if "empty" not in span2['class']:
            actual2 = by_sportsid[int(span2['data-sportsid'])]
        predicted = bs.find_all('span', class_="picked")
        if not predicted:
            predicted1 = actual1
            predicted2 = actual2
        else:
            predicted1, predicted2 = predicted
            predicted1 = by_sportsid[int(predicted1['data-sportsid'])]
            predicted2 = by_sportsid[int(predicted2['data-sportsid'])]
        winner = None
        winning_team = bs.find('span', class_="winner")
        if winning_team is not None:
            winner = by_sportsid[int(winning_team['data-sportsid'])]
        matchup = int(bs['class'][1][2:])
        i = 32
        round_ = 1
        while matchup > i:
            round_ += 1
            matchup -= i
            i /= 2
        return Pick(round_, predicted1, predicted2, actual1, actual2, chosen, winner)
        
def populate_teams(bs):
    by_id = {}
    by_sportsid = {}
    for i in range(1, 65):
        team = Team.of_html(bs.select('div[data-teamid="{}"]'.format(i))[0])
        by_id[i] = team
        by_sportsid[team.sportsid] = team
    return by_id, by_sportsid

def populate_picks(bs, by_id, by_sportsid):
    by_round = defaultdict(list)
    for el in soup.find_all('div', class_="matchup"):
        pick = Pick.of_html(el, by_id, by_sportsid)
        by_round[pick.round_].append(pick)
    return by_round

def aggregate_upsets(picks):
    total_upsets_picked = 0
    total_seed_diff = 0
    total_upsets_right = 0
    for round_ in picks:
        round_upsets_picked = 0
        round_upsets_right = 0
        for pick in picks[round_]:
            if not pick.is_played(): continue

            if pick.was_upset_pick():
                total_upsets_picked += 1
                round_upsets_picked += 1
                if pick.is_correct():
                    total_upsets_right += 1
                    round_upsets_right += 1
                    total_seed_diff += pick.predicted_seed_diff()

        if round_upsets_picked > 0:
            print("Round {}: {} / {} ({:.2f} %)".format(round_, round_upsets_right, round_upsets_picked, (round_upsets_right/round_upsets_picked)*100))
        else:
            print("Round {}: No upsets picked".format(round_))

    if total_upsets_picked > 0:
        print("Total: {} / {} ({:.2f} %)".format(total_upsets_right, total_upsets_picked, (total_upsets_right/total_upsets_picked)*100))
    else:
        print("Total: No upsets picked")
    print("Upset Index: {:.2f}".format(total_seed_diff/total_upsets_picked))
    

def aggregate_stats(picks):
    aggregate_upsets(picks)

if __name__ == "__main__":
    for file in get_files("2019"):
        contents = None
        with open(file, 'r') as f:
            contents = "\n".join(f.readlines())
        soup = BeautifulSoup(contents, "html.parser")
        teams_by_id, teams_by_sportsid = populate_teams(soup)
        picks = populate_picks(soup, teams_by_id, teams_by_sportsid)
        print(file)
        aggregate_stats(picks)
