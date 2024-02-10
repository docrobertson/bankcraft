import warnings

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from ipywidgets import widgets, interact

warnings.filterwarnings("ignore")
import matplotlib.colors as mcolors


class Visualization:
    def __init__(self, model, people_df=None, transaction_df=None, agents_df=None, steps=1008, width=15, height=15):
        self.model = model
        self.STEPS = steps
        self.WIDTH = width
        self.HEIGHT = height
        self.pallet = sns.color_palette("tab10")
        if people_df is None:
            people_df = pd.read_csv('people.csv')
        self.people = people_df
        self.people['location'] = self.people['location'].apply(lambda x: eval(x))
        if transaction_df is None:
            transaction_df = pd.read_csv('transactions.csv')
        self.transactions = transaction_df
        if agents_df is None:
            agents_df = pd.read_csv('agents.csv')
        self.agents = agents_df
        self.agents['location'] = self.agents['location'].apply(lambda x: eval(x))
        self.agentID_color = {}
        self.agentID_jitter = {}
        self.agentID_marker = {}
        self.persons = self.people['AgentID'].unique()
        for i, agentID in enumerate(self.agents["AgentID"].unique()):
            if self.agents[self.agents["AgentID"] == agentID]["agent_type"].values[0] == "person":
                self.agentID_color[agentID] = self.pallet[i % 9]
                self.agentID_marker[agentID] = 'o'
                self.agentID_jitter[agentID] = np.random.normal(0, 0.1, 1)

            elif self.agents[self.agents["AgentID"] == agentID]["agent_type"].values[0] == "merchant":
                self.agentID_color[agentID] = 'black'
                self.agentID_marker[agentID] = 'D'
                self.agentID_jitter[agentID] = 0

            elif self.agents[self.agents["AgentID"] == agentID]["agent_type"].values[0] == "employer":
                self.agentID_color[agentID] = 'black'
                self.agentID_marker[agentID] = 's'
                self.agentID_jitter[agentID] = 0

    def line_plot(self):
        fig, ax = plt.subplots(figsize=(15, 6))
        df = self.people
        df = df.groupby(['AgentID', 'Step']).last().reset_index()
        df['date_time'] = pd.to_datetime(df['date_time'])
        df = df.set_index('date_time')
        sns.lineplot(data=df, x="date_time", y="wealth", hue="AgentID", palette=self.agentID_color, ax=ax)
        ax.set_title("Wealth over time")
        ax.set_ylabel("Wealth")
        ax.set_xlabel("Step")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        return fig, ax

    def grid_plot(self):
        grid_df = self.people[~self.people['location'].isnull()]
        non_person = self.agents[self.agents['agent_type'] != 'person'][['AgentID', 'location', 'date_time']]
        grid_df['x'] = grid_df['location'].apply(lambda x: x[0])
        grid_df['y'] = grid_df['location'].apply(lambda x: x[1])
        grid_df['x'] = grid_df['x'].astype(int)
        grid_df['y'] = grid_df['y'].astype(int)
        pos = nx.spring_layout(nx.complete_graph(grid_df['AgentID'].unique()))
        slider = widgets.SelectionSlider(
            options=list(grid_df['date_time'].unique()),
            description='Time:',
            layout={'width': '500px'},
        )

        @interact(slider=slider)
        def grid_plot(slider):
            fig, ax = plt.subplots(1, 2, figsize=(15, 6))
            # extract the agents at the current step
            sns.scatterplot(x=non_person['location'].apply(lambda x: x[0]),
                            y=non_person['location'].apply(lambda x: x[1]), data=non_person, markers=['D', 's'],
                            ax=ax[0], s=100, label='Merchant/Employer')
            df = grid_df[grid_df['date_time'] == slider]
            for agent in df['AgentID'].unique():
                x = df[df['AgentID'] == agent]['x']
                y = df[df['AgentID'] == agent]['y']

                sns.scatterplot(x=x + self.agentID_jitter[agent], y=y + self.agentID_jitter[agent],
                                data=df[df['AgentID'] == agent],
                                color=self.agentID_color[agent],
                                marker=self.agentID_marker[agent],
                                ax=ax[0], s=100, label='Person')
                ax[0].set_title('Agent Movements in the Grid')

            ax[0].set_xlim(0, self.WIDTH)
            ax[0].set_ylim(0, self.HEIGHT)
            ax[0].legend(loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=3)

            ax[0].set_xlabel('X-coordinate')
            ax[0].set_ylabel('Y-coordinate')
            node = self.people[self.people['date_time'] == slider]['AgentID'].unique()
            trans = self.transactions[self.transactions['step'] == slider]
            transaction_edges = []
            for _, row in trans.iterrows():
                if row['sender'] in node and row['receiver'] in node:
                    transaction_edges.append((row['sender'], row['receiver']))
            people = self.people[self.people['date_time'] == slider]
            edge = nx.complete_graph(node)
            nx.draw_networkx_nodes(node,
                                   pos=pos,
                                   node_color=[self.agentID_color[node] for node in node],
                                   node_size=[people[people['AgentID'] == node]['wealth'] for node in node],
                                   ax=ax[1])

            nx.draw_networkx_edges(edge, pos=pos, ax=ax[1])
            nx.draw_networkx_edges(edge, pos=pos, edgelist=transaction_edges, ax=ax[1], width=2.0)
            ax[1].set_title('Social Network')

            # Display the plot
            plt.tight_layout()
            plt.grid(True)
            plt.show()

    def sender_bar_plot(self, include='all'):
        df = self.transactions[self.transactions['sender'].isin(self.persons)]
        df = df if include == 'all' else df[df['sender'] == include]
        df = df.groupby(['sender', 'description']).sum().reset_index()
        fig, ax = plt.subplots(figsize=(15, 6))
        sns.barplot(x='sender', y='amount', hue='description', data=df, ax=ax)
        for xtick in ax.get_xticklabels():
            xtick.set_color(self.agentID_color[int(xtick.get_text())])

        ax.set_xticklabels([f"{str(agent)[:7]}..." for agent in df.sender.unique()],
                           rotation=45, horizontalalignment='right')
        ax.set_title('Sender Bar Plot')
        ax.set_ylabel('Total Amount')
        ax.set_xlabel('Sender')
        return fig, ax

    def receiver_bar_plot(self, include='all'):
        df = self.transactions[self.transactions['receiver'].isin(self.persons)]
        df = df if include == 'all' else df[df['receiver'] == include]
        df = df.groupby(['receiver', 'description']).sum().reset_index()
        fig, ax = plt.subplots(figsize=(15, 6))
        sns.barplot(x='receiver', y='amount', hue='description', data=df, ax=ax, )

        for xtick in ax.get_xticklabels():
            xtick.set_color(self.agentID_color[int(xtick.get_text())])

        ax.set_xticklabels([f"{str(agent)[:7]}..." for agent in df.receiver.unique()],
                           rotation=45, horizontalalignment='right')
        ax.set_title('Receiver Bar Plot')
        ax.set_ylabel('Total Amount')
        ax.set_xlabel('Receiver')
        return fig, ax

    def motivation_plot(self, agent_id):
        df = self.people[self.people['AgentID'] == agent_id]
        df['date_time'] = pd.to_datetime(df['date_time'])
        df = df.set_index('date_time')
        color = self.agentID_color[agent_id]
        fig, ax = plt.subplots(figsize=(15, 6))
        ax.plot(df['ConsumerismState'], color='orange')
        ax.plot(df['HungerState'], color='red')
        ax.plot(df['FatigueState'], color='blue')
        ax.plot(df['SocialState'], color='green')
        ax.plot(df['WorkState'], color='m')
        ax.axhline(y=20, color='grey', linestyle='--')
        labels = ax.get_xticklabels()
        ax.set_xticklabels(labels, rotation=45)
        xticks = ax.get_xticks()
        ax.vlines(xticks, 0, 20, linestyles='dashed', colors='grey')
        ax.locator_params(axis='x', nbins=10)
        ax.set_title(f"Motivation over time for agent {agent_id}")
        ax.set_ylabel("Motivation")
        ax.set_xlabel("date")
        ax.legend(['consumerism level', 'hunger level', 'fatigue level', 'social level', 'work level'],
                  frameon=True)  # ,facecolor=color, framealpha=1)
        return fig, ax

    def transaction_type_bar_plot(self):
        df = self.transactions
        df = df.groupby(['txn_type']).sum().reset_index()
        fig, ax = plt.subplots(figsize=(15, 6))
        sns.barplot(x='txn_type', y='amount', data=df, ax=ax)
        ax.set_title("Transaction type")
        ax.set_ylabel("Total Amount")
        ax.set_xlabel("Transaction type")
        return fig, ax

    def location_over_time(self, agent_id):
        grid_df = self.people[~self.people['location'].isnull()]
        non_person = self.agents[self.agents['agent_type'] != 'person'][['AgentID', 'location', 'date_time']]
        grid_df['x'] = grid_df['location'].apply(lambda x: x[0])
        grid_df['y'] = grid_df['location'].apply(lambda x: x[1])
        grid_df['x'] = grid_df['x'].astype(int)
        grid_df['y'] = grid_df['y'].astype(int)
        pos = nx.spring_layout(nx.complete_graph(grid_df['AgentID'].unique()))
        slider = widgets.SelectionSlider(
            options=list(grid_df['date_time'].unique()),
            description='Time:',
            layout={'width': '500px'},
        )

        @interact(slider=slider)
        def plot_agent_trace(slider):
            # Filter the DataFrame for the specified agent ID
            df = grid_df[grid_df['AgentID'] == agent_id]
            current_location = df[df['date_time'] == slider]
            df = df[df['date_time'] <= slider]
            fig, ax = plt.subplots(1, 1, figsize=(6, 6))

            min_time = df['date_time'].min()
            max_time = slider
            if min_time == max_time:
                df['alpha'] = 1
            else:
                df['alpha'] = (df['date_time'] - min_time) / (max_time - min_time)

            # Plot the agent's trace with varying transparency (alpha)
            sns.scatterplot(x=df['x'], y=df['y'], data=df, color=self.agentID_color[agent_id], alpha=df['alpha'], ax=ax)

            # Plot the agent's current location as grey circle
            sns.scatterplot(x=current_location['x'], y=current_location['y'], data=current_location,
                            color=self.agentID_color[agent_id],
                            marker='o',
                            ax=ax, s=100)
            # plt merchandise locations as black diamonds
            sns.scatterplot(x=non_person['location'].apply(lambda x: x[0]),
                            y=non_person['location'].apply(lambda x: x[1]), data=non_person, markers=['D', 's'], ax=ax,
                            s=100, label='Merchant/Employer', color='black')
            ax.set_title('Agent Trace')
            ax.set_xlim(0, self.WIDTH)
            ax.set_ylim(0, self.HEIGHT)
            ax.set_xlabel('X-coordinate')
            ax.set_ylabel('Y-coordinate')

            plt.show()

    def account_balance_over_time(self, agent_id):
        df = self.people[self.people['AgentID'] == agent_id]
        df['date_time'] = pd.to_datetime(df['date_time'])
        df = df.groupby(['Step']).last().reset_index()
        # number of columns starting with account
        num_accounts = len([col for col in df.columns if col.startswith('account')])
        fig, ax = plt.subplots(figsize=(15, 6))
        for i in range(num_accounts):
            account_df = df[['Step', f'account_{i}']]
            sns.lineplot(data=account_df, x="Step", y=f"account_{i}", ax=ax, label=f"account_{i}")

        ax.legend()
        ax.set_title(f"Account balance over time for agent {agent_id}")
        ax.set_ylabel("Account balance")
        ax.set_xlabel("Step")
        plt.show()
        return fig, ax

    def expenses_breakdown_plot(self, agent_id):
        df = self.transactions[(self.transactions['sender'] == agent_id) | (self.transactions['receiver'] == agent_id)]
        df = df.groupby('description').sum().reset_index()
        salary = df[df['description'] == 'salary']['amount'].values[0]
        df = df[df['description'] != 'salary']
        df['amount'] = df['amount'].abs().sort_values(ascending=False)
        df['percentage'] = df['amount'].apply(lambda x: x / salary)
        # just columns we need
        df = df[['description', 'amount', 'percentage']]
        # if sum of percentage is less than 1, add saving
        if df['percentage'].sum() < 1:
            # add new row
            df.loc[len(df)] = ['saving', salary - df['amount'].sum(), 1 - df['percentage'].sum()]
        df = df.sort_values(by='percentage', ascending=False)

        expenses = self.transactions.description.unique()
        expenses = np.append(expenses, ['others', 'saving'])
        colors = list(mcolors.TABLEAU_COLORS.values())
        colors = colors[0:len(expenses)]
        colors = dict(zip(expenses, colors))

        fig, ax = plt.subplots(1, 2, figsize=(15, 5))
        bar = sns.barplot(x='description', y='amount', data=df, ax=ax[0], palette=colors)
        bar.set_xlabel('Expenses')
        bar.set_ylabel('Amount')
        bar.set_xticklabels(bar.get_xticklabels(), rotation=45)

        others = df[df['percentage'] < 0.10]
        df['description'] = df['description'].apply(
            lambda x: x if df[df['description'] == x]['percentage'].values[0] > 0.10 else 'others')
        df = df.groupby('description').sum().reset_index()

        ax[1].pie(df['percentage'], startangle=90, colors=[colors[x] for x in df['description']], autopct='%1.1f%%',
                  labels=df['description'])
        # show others with their percentage
        for i in range(len(others)):
            ax[1].text(1.5, 0.5 + i * 0.1,
                       f"{others.iloc[i]['description']} ({round(others.iloc[i]['percentage'] * 100, 2)}%)",
                       color='black')
        ax[1].axis('equal')
        ax[0].set_title('Expenses Breakdown by Amount')
        ax[1].set_title('Expenses Breakdown by Percentage of Salary')

        return fig, ax

    def transaction_plot(self):
        df = self.transactions.copy()
        df['date_time'] = pd.to_datetime(df['date_time'])
        df['date'] = df['date_time'].dt.date
        df['date'] = pd.to_datetime(df['date'])
        df['day'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['amount'] = df['amount'].abs()

        view_toggles_buttons = widgets.ToggleButtons(
            options=['day', 'month'],
            description='View:',
            disabled=False
        )

        metric_toggles_buttons = widgets.ToggleButtons(
            options=['number', 'amount'],
            description='Metric:',
            disabled=False
        )

        @widgets.interact(view=view_toggles_buttons, metric=metric_toggles_buttons)
        def plot(view, metric):
            fig, ax = plt.subplots(figsize=(15, 5))

            if view == 'day':
                data_grouped = df.groupby(['year', 'month', 'day', 'description'])
            else:
                data_grouped = df.groupby(['year', 'month', 'description'])

            if metric == 'number':
                data_to_plot = data_grouped.size().unstack(fill_value=0)
                title = 'Number of transactions per ' + view
                y_label = 'Number of transactions'
            else:
                data_to_plot = data_grouped['amount'].sum().unstack(fill_value=0)
                title = 'Amount of transactions per ' + view
                y_label = 'Amount of transactions'

            data_to_plot.plot(kind='bar', stacked=True, ax=ax)
            ax.set_xlabel('Date')
            ax.set_ylabel(y_label)
            ax.set_title(title)

            # Anchor the legend outside the plot
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))

            plt.show()

    def movements_plot(self):
        df = self.people.copy().reset_index()
        df = df[['date_time', 'AgentID', 'location']]
        agents = self.agents[(self.agents['Step'] == 1)]
        info = agents[['AgentID', 'agent_home', 'agent_work', 'agent_type']]
        merchant_locations = info[info['agent_type'] == 'merchant'].agent_home.unique()
        # in df replace location with the name of the location in info
        df = pd.merge(df, info, on='AgentID')
        # for each row in df2, if location is the same as agent_home, replace location_name with 'Home'
        for index, row in df.iterrows():
            if row['location'] == row['agent_home']:
                df.at[index, 'location_name'] = 'Home'
            elif row['location'] == row['agent_work']:
                df.at[index, 'location_name'] = 'Work'
            elif (row['location'] == merchant_locations[0] or row['location'] == merchant_locations[1] or
                  row['location'] == merchant_locations[2]):
                df.at[index, 'location_name'] = 'Merchant'
            else:
                df.at[index, 'location_name'] = 'Traveling'

        location_names = ['Home', 'Work', 'Merchant', 'Traveling']
        num_locations = len(location_names)
        slider = widgets.SelectionSlider(
            options=list(df['date_time'].unique()),
            description='Time:',
            layout={'width': '500px'},
        )
        df2 = df.groupby(['date_time', 'location_name']).count().reset_index()
        df2 = df2.pivot(index='date_time', columns='location_name', values='AgentID')
        df2 = df2.fillna(0)
        df2.reset_index(inplace=True)

        @widgets.interact(step=slider)
        def plot(step):
            current_df = df[df['date_time'] == step]
            fig = plt.figure(figsize=(15, 6))
            gs = fig.add_gridspec(nrows=4, ncols=2)
            ax0 = fig.add_subplot(gs[:, 0])
            for agent in current_df['AgentID'].unique():
                ax0.scatter(current_df[current_df['AgentID'] == agent]['location_name'],
                            current_df[current_df['AgentID'] == agent]['AgentID'],
                            color=self.agentID_color[agent],
                            label=agent,
                            )
            ax0.set_xlabel('Location')
            ax0.set_ylabel('Agent ID')
            ax0.set_title('Agent Locations')
            ax0.set_yticks([])
            ax0.set_yticklabels([])
            ax0.set_xticks(np.arange(0, num_locations, 1))
            ax0.set_xticklabels(location_names)

            ax2 = fig.add_subplot(gs[1, 1])
            ax2.plot(df2['date_time'], df2['Home'], color='red')
            ax2.set_xticks([])
            ax2.axvline(x=step, color='black', linestyle='--')
            ax2.set_title('Home')

            ax3 = fig.add_subplot(gs[2, 1])
            ax3.plot(df2['date_time'], df2['Work'], color='blue')
            ax3.set_title('Work')
            ax3.axvline(x=step, color='black', linestyle='--')
            ax3.set_xticks([])

            ax4 = fig.add_subplot(gs[3, 1])
            ax4.plot(df2['date_time'], df2['Merchant'], color='green')
            ax4.set_title('Merchant')
            ax4.axvline(x=step, color='black', linestyle='--')
            ax4.set_xticks([])

            ax5 = fig.add_subplot(gs[0, 1])
            ax5.plot(df2['date_time'], df2['Traveling'], color='orange')
            ax5.set_title('Traveling')
            ax5.axvline(x=step, color='black', linestyle='--')
            ax5.set_xticks([])

            plt.show()
