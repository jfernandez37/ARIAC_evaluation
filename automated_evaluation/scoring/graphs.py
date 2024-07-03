import os
from typing import Optional
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np

from structs import (
    OrderInfo,
    OrderSubmission
)

def team_raw_score_graph(trial: str, team: str, orders: list[OrderInfo], submissions: list[Optional[OrderSubmission]], save_folder: str):
    num_orders = len(orders)
    bar_width = 0.2 * num_orders

    centers = []
    for i in range(num_orders):
        centers.append(0.6 + 1.2 * i)

    ax: Axes
    _, ax = plt.subplots()

    order_ids = [f'Order ID:\n{o.order_id}' for o in orders]

    data = {
        'actual score': [s.raw_score if s is not None else 0.2 for s in submissions],
        'max score': [o.max_score for o in orders]
    }

    actual = True
    for label, points in data.items():
        x = []
        if actual:
            offset = -bar_width/2
            color = 'skyblue'
        else:
            offset = bar_width/2
            color = 'steelblue'

        for i in range(num_orders):
            x.append(0.6 + offset + (1.2 * i))

        bars = ax.bar(x, [p if not p==0 else 0.2 for p in points], bar_width, label=label, color=color)
        ax.bar_label(bars, padding=3)

        actual = False

    ax.set_ylabel('Points')

    trial_name = trial.replace('_',' ').title()
    team_name = team.replace('_',' ').title()

    ax.set_title(f'{trial_name} Raw Score\nTeam: {team_name}')
    ax.set_xticks(centers, order_ids)
    ax.legend(loc='upper right', ncol=2)
    ax.set_ylim(0, max([o.max_score for o in orders]) + 3)
    ax.set_xlim(0, 1.2 * num_orders)

    plt.savefig(os.path.join(save_folder, trial + '.png'))